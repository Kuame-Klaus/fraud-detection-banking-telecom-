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

Further uses listed in the pack, such as dormant accounts, duplicate payments, wallet drain and impossible travel, are also listed there.

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

1. Alteryx, KNIME and Python each run the numbered steps in docs/pipeline_steps.md, starting with the pack's reconciliation and data quality checks.
2. All three read the same input files and use the same time based splits.
3. All three write the shared scores, metrics and data quality tables in docs/output_schema.md.
4. Python reads those outputs and produces the comparison charts.
5. Power BI is a placeholder and nothing is built there yet.

## 5. Repository structure

* python/ : synthetic generator, Python pipeline and charts.
* python/synthetic/ : generator plan and config file.
* alteryx/ : Alteryx workflows (.yxmd).
* knime/ : KNIME workflows (.knwf).
* powerbi/ : placeholder for Power BI visualization.
* data/ : local data only, ignored by git.
* outputs/ : local scores, metrics and charts, ignored by git.
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

## Credits

Klaus Konsults.
