# Python pipeline

Runs the six stages in docs/pipeline_steps.md, for banking and telecom separately:

1. Load and control totals.
2. Data quality checks.
3. Features.
4. Scenario rules for all 27 scenarios in docs/scenario_coverage.md.
5. Model: XGBoost, with logistic regression as a baseline and SHAP explanations.
6. Shared results output, including rule coverage gaps, threshold sensitivity at plus or minus 10% and 20%, monthly score drift and agreement with the Alteryx and KNIME results.

Output: outputs/python/results_<run_id>.parquet in the schema in docs/output_schema.md.
