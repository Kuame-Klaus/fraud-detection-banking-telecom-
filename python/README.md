# Python

Python implementation of the shared process:

1. synthetic/ : seeded synthetic data generator (see synthetic/README.md).
2. Pipeline: the numbered steps in docs/pipeline_steps.md, starting with reconciliation and data quality checks, then scenario tests, features, time based splits, models (logistic regression, random forest, XGBoost, LightGBM), imbalanced learn resampling, graph features and SHAP.
3. Outputs in the shared schema in docs/output_schema.md.
4. Charts: read the shared outputs from all three stacks and produce comparison visuals in outputs/charts/.

At 20 million rows, use pyarrow or polars, chunked reads, and LightGBM on a stratified sample or out of core. Runtime and memory will be measured, not assumed.
