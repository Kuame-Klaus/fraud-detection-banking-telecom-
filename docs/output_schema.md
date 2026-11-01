# Shared results schema

Every stack (Alteryx, KNIME, Python) writes one shared results file per run, outputs/<stack>/results_<run_id>.parquet (CSV option). All 12 charts in docs/charts.md, in Python and later in Power BI, read only these files. The file is in long format: a record_type column says what each row holds, and columns that do not apply to a row are left empty.

## record_type values

1. score: one row per scored record per model.
2. metric: one row per metric per model and split.
3. dq: one row per data quality or reconciliation check.
4. coverage: one row per scenario and rule for the rule coverage gap check.
5. threshold: one row per rule or model per threshold change.
6. drift: one row per model, month and score band.
7. agreement: one row per pair of tools per model and scenario.
8. edge: one row per link in the mule or agent network.
9. benford: one row per first digit per dataset.
10. geo: one row per route or cell per day.
11. run: one row per run with runtime and memory.

## Columns

| column | type | used by | meaning |
|---|---|---|---|
| record_type | string | all | one of the values above |
| run_id | string | all | unique id of the run |
| created_at | string | all | ISO 8601 timestamp of the run |
| stack | string | all | alteryx, knime or python |
| domain | string | all | banking or telecom |
| dataset_id | string | dq, benford, geo | for example B1 or T8 |
| scenario | string | score, metric, coverage, threshold, agreement | scenario name from docs/scenario_coverage.md, or all |
| model | string | score, metric, threshold, drift, agreement | for example xgboost, rule, or the built in learner name |
| rule_id | string | score, coverage, threshold | rule identifier, if a rule fired |
| split | string | score, metric | train, validation or test |
| record_id | string | score | id of the input row, identical across stacks |
| entity_id | string | score, edge | account, wallet, agent, msisdn, user, vendor or employee id |
| entity_type | string | score, edge | type of entity_id |
| event_timestamp | string | score | ISO 8601 time of the event, for alert trends and hour by weekday heat maps |
| month | string | score, dq, drift | YYYY MM month of the row |
| score | float | score | fraud score between 0 and 1 |
| threshold | float | score, threshold | threshold applied |
| predicted_label | int | score | 1 for alert, 0 for no alert |
| true_label | int | score | 1 for fraud, 0 for not fraud |
| true_scenario | string | score | planted scenario label, empty when not fraud |
| amount | float | score | amount of the event, for KPI and leaderboard totals |
| currency | string | score | currency of amount |
| metric | string | metric | for example pr_auc, recall_at_alert_rate, expected_cost |
| value | float | metric, drift, agreement | metric value, drift statistic or agreement rate |
| alert_rate | float | metric | alert rate used, if relevant |
| train_rows | int | metric | rows used for training |
| sample_method | string | metric | none, stratified or other |
| step | int | dq | step number from docs/pipeline_steps.md |
| check_name | string | dq | short name of the check |
| expected | string | dq | expected value, for example a control total |
| observed | string | dq | observed value |
| passed | bool | dq | whether the check passed |
| note | string | dq, coverage | explanation or limitation |
| covered | bool | coverage | whether the scenario has at least one rule or model |
| threshold_change_pct | float | threshold | minus 20, minus 10, 0, plus 10 or plus 20 |
| alert_count | int | threshold | alerts at that threshold |
| detected_count | int | threshold | planted cases detected at that threshold |
| score_band | string | drift | score range, for example 0.0 to 0.1 |
| band_share | float | drift | share of records in the band that month |
| compare_stack | string | agreement | the other tool in the pair |
| source_id | string | edge | sending entity |
| target_id | string | edge | receiving entity |
| edge_weight | float | edge | total amount or count on the link |
| edge_count | int | edge | number of transactions on the link |
| first_digit | int | benford | leading digit 1 to 9 |
| observed_count | int | benford | count of amounts with that digit |
| expected_share | float | benford | Benford expected share for that digit |
| route | string | geo | T1 or T8 route |
| cell_id | string | geo | T1 or T9 cell id |
| latitude | float | geo | cell latitude (open question, see docs/open_questions.md) |
| longitude | float | geo | cell longitude (open question) |
| geo_minutes | float | geo | minutes on the route or cell that day |
| geo_settled_minutes | float | geo | settled minutes from T8, if any |
| runtime_seconds | float | run, metric | measured runtime |
| peak_memory_mb | float | run, metric | measured peak memory, if available |
| stage | string | run | stage name from docs/pipeline_steps.md |
