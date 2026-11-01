# Python pipeline

Runs the six stages in docs/pipeline_steps.md, for banking and telecom separately:

1. Load and control totals.
2. Data quality checks.
3. Features.
4. Scenario rules for all 27 scenarios in docs/scenario_coverage.md.
5. Model: XGBoost, with logistic regression as a baseline and SHAP explanations.
6. Shared results output, including rule coverage gaps, threshold sensitivity at plus or minus 10% and 20%, monthly score drift and agreement with the Alteryx and KNIME results.

Output: outputs/python/results_<run_id>.parquet in the schema in docs/output_schema.md.

## Streaming design (works on the full data)

The pipeline never loads a whole table. For each domain:

1. **One pass per table.** Each manifest part (or Parquet part, or CSV) is read on its own with pyarrow. Data quality counts, key hashes, time ranges, monthly counts and the small lookups used by the rules (for example last SIM swap per number, minutes per route) are updated chunk by chunk.
2. **Entity hash buckets.** Large event tables (B1, T1, T4) are written to on disk buckets of about 1.5 million rows (`--bucket-rows`), split by a hash of the account, number or wallet, under `out/_tmp_<run_id>` (deleted at the end). Every row of one entity lands in the same bucket, so per entity features and rules give the same answer as a one chunk run.
3. **Features and rules per bucket.** Rule rows are appended to the results file as each bucket finishes.
4. **Model.** XGBoost trains on a recorded stratified sample: all positives plus negatives at fraction min(1, max_train_rows / (0.75 x rows)), `--max-train-rows` default 2,000,000. The sample method and fraction are written in the metric rows. Every test row is then scored bucket by bucket. Train is before 2025-10-01, validation is October 2025, test is November and December 2025. The alert threshold is the 0.99 quantile of the validation scores.
5. **Output.** A pyarrow ParquetWriter with the fixed schema in docs/output_schema.md. When input rows are 2 million or fewer, results_latest.csv holds every row. Otherwise results_summary.csv holds everything except score rows (`--csv-scores auto|yes|no`).

`tests/test_pipeline.py::test_chunked_path_matches_single_chunk` splits every table into several parts, uses tiny buckets, and checks the rule metrics equal the one chunk run.
