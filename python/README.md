# Python

1. synthetic/ : seeded synthetic data generator (see synthetic/README.md).
2. pipeline/ : the six stage pipeline in docs/pipeline_steps.md, with XGBoost as the model.
3. viz/ : the 12 charts in docs/charts.md, read from the shared results files.

At 20 million rows, use pyarrow or polars, chunked reads, and XGBoost on a stratified sample or with external memory, scoring the full set in chunks. Runtime and memory will be measured, not assumed.
