# Fraud Detection for Banking and Telecom

A Klaus Konsults project to detect fraud in banking and telecom, governed by the Fraud Audit Data Request and Extraction Pack. The same fraud detection process is built three times, in Alteryx, KNIME and Python, so results can be compared directly. Each stack runs on about 20 million rows in the main banking event table (B1) and about 20 million in the main telecom event table (T1), with mobile money transactions (T4) at a similar scale. Python produces the charts. Power BI is a placeholder for now.

Banking and telecom are two separate entities, with no shared keys and no joins between them.

Synthetic data uses the pack's dataset IDs (B1 to B14, T1 to T12) and column names, so the same pipeline runs unchanged on real client extracts.

This repository is public. It holds only code, workflows, configuration and documentation. It never holds data of any kind, client names, keys or credentials.

## 1. Fraud scenarios

Each scenario is mapped to its datasets and columns in docs/scenario_coverage.md.

1. Card testing
2. Account takeover
3. Mule network
4. Structuring
5. Journal abuse
6. Segregation of duties
7. Ghost vendor or employee
8. SIM swap fraud
9. SIM box and bypass
10. Subscription and bust out
11. Agent fraud
12. Insider SIM swap or access abuse

Klaus Konsults extensions beyond the pack:

13. Banking: dormant account wake up, KYC mismatch with expected volume, impossible travel, duplicate vendor payments, payroll after exit, privileged access changes before journals, Benford's law, reversal abuse.
14. Telecom: wallet tier breach, dormant wallet drain, Wangiri, IMEI churn, recharge fraud, interconnect leakage, agent float anomalies.

Banking tests use only banking data and telecom tests use only telecom data.

## 2. Data

1. Dataset list and target columns: docs/data_dictionary.md, copied from the pack.
2. Synthetic data: a seeded, reproducible generator in python/synthetic/, clearly labelled synthetic and calibrated to public data (Kaggle Credit Card Fraud Detection by the ULB Machine Learning Group, and PaySim by E. A. Lopez Rojas) using distributions and fraud rates only.
3. Real client data: only with written authorisation, scope and NDA, following docs/engagement_rules.md. It is kept outside this repository and never committed.
4. Extraction: SQL templates in docs/sql/ and the extraction prompt in docs/prompts/.

## 3. Provisional defaults

Where the pack is silent or unclear, Klaus Konsults has set defaults so work can proceed. Each is an assumption the client can override, and each is labelled ASSUMPTION or ADDITION where it appears. See docs/open_questions.md.

1. Missing column names are snake_case versions of the pack's wording.
2. Where the pack's field lists and SQL differ, the SQL names are kept.
3. Extra control totals for B7 and T1, and SQL templates for datasets the pack has none for, sit in docs/sql/additions/, separate from the pack's SQL.
4. Sizing: about 20 million rows in B1 and T1, T4 at a similar scale, other tables at assumed realistic proportions.

## 4. One process, three stacks

Each stack runs the same six stages (docs/pipeline_steps.md):

1. Load and control totals.
2. Data quality checks.
3. Features.
4. Scenario rules.
5. Model: XGBoost in Python, built in learners in Alteryx and KNIME.
6. Shared results output, with detection review checks: rule coverage gaps, threshold sensitivity at plus or minus 10% and 20%, monthly score drift, and agreement between the three tools.

All stacks write one shared results file format (docs/output_schema.md). The same 12 charts (docs/charts.md) are built in Python from those files, and planned for Power BI.

Further detail:

1. Alteryx, KNIME and Python each run the numbered steps in docs/pipeline_steps.md, starting with the pack's reconciliation and data quality checks.
2. All three read the same input files and use the same time based splits.
3. All three write the shared results file in docs/output_schema.md.
4. Python reads those files and builds the 12 charts in docs/charts.md.
5. Power BI will rebuild the same charts later; nothing is built there yet.

## 5. Repository structure

* python/synthetic/ : generator plan and config file.
* python/pipeline/ : the six stage Python pipeline.
* python/viz/ : the 12 charts.
* alteryx/ : Alteryx workflows (.yxmd).
* knime/ : KNIME workflows (.knwf).
* powerbi/ : the same 12 charts, planned only.
* data/ : local data, ignored by git, except data/sample/ which holds the committed SYNTHETIC sample CSVs.
* outputs/ : local scores, metrics and charts, ignored by git, except outputs/sample/ which holds the sample results and charts.
* docs/sql/additions/ : provisional default SQL, kept apart from the pack SQL.
* docs/ : data dictionary, scenario coverage, pipeline steps, output schema, engagement rules, SQL templates, prompts and open questions.

## 6. Models

1. Rule based scenario tests from docs/scenario_coverage.md.
2. Logistic regression as the baseline.
3. Random forest, XGBoost and LightGBM.
4. Resampling for class imbalance with imbalanced learn, compared against class weights.
5. Graph features, such as shared devices, shared numbers and money flow links.
6. SHAP explanations so analysts can see why a case was flagged.

Labels come from B12 and T10.

## 7. Evaluation

1. Precision recall AUC as the main metric.
2. Recall at a fixed alert rate.
3. Cost based evaluation weighing missed fraud against false alerts.
4. Time based splits, identical across stacks.

No results or benchmarks are reported yet.

## 8. Working at 20 million rows

Real runtime and memory needs will be measured on the actual hardware, not assumed, and recorded in the metrics table.

Alteryx: use the AMP engine, raise the sort and join memory setting, give temp files ample disk space, use chunked inputs or the In Database tools, and expect long runtimes on a desktop.

KNIME: raise the -Xmx setting in knime.ini, use the columnar table backend, use streaming or chunk loops, read with the Parquet reader, and if needed train on a stratified sample while scoring the full set.

Python: use pyarrow or polars, read in chunks, and train LightGBM on a stratified sample or out of core while scoring the full set in chunks.

If a stack trains on a sample, the sample size and method are recorded so comparisons stay fair.

## 9. Milestones

1. Phase 1: plan, skeleton, data dictionary, scenario coverage, pipeline steps and output schema.
2. Phase 2: confirm or override the provisional defaults in docs/open_questions.md with the client.
3. Phase 3: seeded generator for B1 to B14 and T1 to T12 at small scale, calibrated to public data.
4. Phase 4: reconciliation and data quality steps in Python.
5. Phase 5: scenario tests and models in Python, writing the shared schema.
6. Phase 6: scale the generator to about 20 million rows per domain and fix the time based splits.
7. Phase 7: Alteryx pipeline on the same inputs, steps and schema, with runtime and memory measured.
8. Phase 8: KNIME pipeline on the same inputs, steps and schema, with runtime and memory measured.
9. Phase 9: graph features, resampling experiments and SHAP explanations.
10. Phase 10: Python comparison charts across the three stacks and write up.
11. Phase 11: Power BI visualization once its details are confirmed.
12. Phase 12: run on approved real client extracts under the pack's ground rules, outside this repository.

## 10. How to connect each tool

All data in this repo is SYNTHETIC and labelled as such. The committed sample is in data/sample/ (CSV, about 50,000 rows for each main table, every planted fraud case included and labelled in the synthetic_scenario column). The sample pipeline results are in outputs/sample/. Every tool reads the same files.

Raw URL pattern for a dataset:

https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/<domain>/<dataset>.csv

For example:

* https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B1_transactions.csv
* https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T1_cdrs.csv
* https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T4_momo_wallet_txns.csv

The full list of 26 datasets with their raw URLs and local full size paths is in config/sources.csv. The switch between the sample URLs and local full data is the `source` value in config/data_source.yaml (`sample_url` or `local_full`).

Shared results file (all charts read this):

https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/outputs/sample/results_latest.csv

### Alteryx

1. Read config/sources.csv, pick the dataset, and pass its raw_url to a Download tool, then parse the CSV.
2. To use local full data, set `source` to `local_full` and read the Parquet folder with Dynamic Input.
3. Step by step notes are in alteryx/BUILD_NOTES.md. These are notes, not a tested .yxmd workflow.

### KNIME

1. Paste a raw URL into the CSV Reader node as the file path, or loop over config/sources.csv.
2. To use local full data, set the `source` variable to `local_full` and use the Parquet Reader node.
3. Step by step notes are in knime/BUILD_NOTES.md. These are notes, not a tested .knwf workflow.

### Power BI (planned)

1. Home, Get data, Web.
2. Paste https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/outputs/sample/results_latest.csv and choose Anonymous access.
3. In Power Query, set column types, then filter on record_type for each page, as listed in docs/charts.md.
4. Raw dataset CSVs from data/sample/ can be added the same way if a page needs them.

### Python

1. `pip install -r requirements.txt`
2. `make pipeline` runs the six steps on the committed sample (data/sample) and writes outputs/sample.
3. `make charts` draws the charts into outputs/sample/charts.
4. `make test` runs the tests.
5. `make full` generates full size data locally under data/synthetic/full (ignored by git), then `make pipeline-full`.
6. `make release` packages full data into parts of 2 GB or less with a manifest and SHA256 checksums under dist/release. It does not create or publish a GitHub Release.
7. pandas can also read a raw URL directly: `pd.read_csv("https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B1_transactions.csv")`.

## Credits

Klaus Konsults.
