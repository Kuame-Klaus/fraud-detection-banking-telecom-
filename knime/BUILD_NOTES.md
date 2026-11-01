# KNIME build notes (Klaus Konsults)

These are step by step notes and a config, not a packaged .knwf workflow. A valid .knwf file could not be authored or tested here because KNIME Analytics Platform is not available on the build machine. Nothing in this folder has been run in KNIME yet.

## Data source switch

1. Add a String Configuration node (or a workflow variable) named `source` with the value `sample_url` or `local_full`, matching config/data_source.yaml.
2. Read config/sources.csv with a CSV Reader node.
3. Use a Rule Engine node: `$${Ssource}$$ = "sample_url" => $raw_url$` and `TRUE => $local_full_path$`, then Table Row to Variable Loop Start.
4. For sample_url, the CSV Reader node accepts an https URL as its file path, so the raw URL can be passed in directly. For local_full, use the Parquet Reader node on the folder.
5. Example raw URL: https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T4_momo_wallet_txns.csv

## Six stages

1. Load and control totals: GroupBy for row counts and amount sums.
2. Data quality: Duplicate Row Filter, Missing Value and Rule-based Row Filter nodes.
3. Features: Lag Column and Moving Aggregation per entity, GroupBy plus Joiner for daily counts.
4. Scenario rules: Rule Engine nodes with the rule_id values and ASSUMPTION thresholds in python/pipeline/rules.py.
5. Model: XGBoost Tree Ensemble Learner and Predictor (KNIME XGBoost Integration) or Gradient Boosted Trees Learner, with the same time split as Python.
6. Output: Column Rename and Constant Value Column nodes to match docs/output_schema.md, stack = knime, CSV Writer to outputs/knime/results_<run_id>.csv.
