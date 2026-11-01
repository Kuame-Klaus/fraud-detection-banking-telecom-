# Shared output schema

Every stack (Alteryx, KNIME, Python) writes outputs in these three tables, as Parquet or CSV, under outputs/<stack>/. Python charts read these files.

## Scores table

| column | type | meaning |
|---|---|---|
| record_id | string | id of the input row, identical across stacks |
| domain | string | banking or telecom |
| stack | string | alteryx, knime or python |
| scenario | string | scenario from docs/scenario_coverage.md, or all |
| model | string | for example logistic_regression, random_forest, xgboost, lightgbm |
| split | string | train, validation or test |
| score | float | fraud score between 0 and 1 |
| predicted_label | int | 1 for fraud, 0 for not fraud, at the chosen threshold |
| true_label | int | 1 for fraud, 0 for not fraud |
| run_id | string | unique id of the run |

## Metrics table

| column | type | meaning |
|---|---|---|
| run_id | string | links to the scores table |
| domain | string | banking or telecom |
| stack | string | alteryx, knime or python |
| model | string | model name |
| split | string | split evaluated |
| metric | string | for example pr_auc, recall_at_alert_rate, expected_cost |
| value | float | metric value |
| alert_rate | float | alert rate used, if relevant |
| train_rows | int | rows used for training (records sampling) |
| sample_method | string | none, stratified or other |
| runtime_seconds | float | measured runtime |
| peak_memory_mb | float | measured peak memory, if available |
| created_at | string | timestamp of the run |

## Data quality results table

| column | type | meaning |
|---|---|---|
| run_id | string | links to the other tables |
| stack | string | alteryx, knime or python |
| step | int | step number from docs/pipeline_steps.md |
| dataset_id | string | for example B1 or T4 |
| month | string | month checked, if relevant |
| check_name | string | short name of the check |
| expected | string | expected value, for example a client control total |
| observed | string | observed value |
| passed | bool | whether the check passed |
| note | string | explanation or limitation |
