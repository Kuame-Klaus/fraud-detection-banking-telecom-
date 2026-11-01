# Alteryx build notes (Klaus Konsults)

These are step by step notes and a config, not a packaged .yxmd workflow. A valid .yxmd file could not be authored or tested here because Alteryx Designer is not available on the build machine. Nothing in this folder has been run in Alteryx yet.

## Data source switch

1. Add a Text Input tool named `source` with one field `source` and the value `sample_url` or `local_full`, matching config/data_source.yaml.
2. Add an Input Data tool that reads config/sources.csv (the dataset list with both locations).
3. Add a Filter tool on the dataset you need, then a Formula tool: `IF [source] = "sample_url" THEN [raw_url] ELSE [local_full_path] ENDIF`.
4. For sample_url, feed that field into a Download tool (Developer category), then a Text To Columns or CSV parse step. For local_full, use a Dynamic Input tool pointed at the Parquet folder (Designer 2023.1 or later reads Parquet).
5. Example raw URL: https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B1_transactions.csv

## Six stages

1. Load and control totals: Summarize tool for row counts and amount sums per dataset, compared with the Python dq rows in outputs/sample/results_latest.csv.
2. Data quality: Unique tool for duplicate keys, Data Cleansing and Filter tools for nulls, negative amounts and timestamp range.
3. Features: Multi Row Formula for time since previous event per account or wallet, Summarize plus Join for counts per entity per day.
4. Scenario rules: one Filter tool per rule, matching python/pipeline/rules.py (same rule_id values and ASSUMPTION thresholds).
5. Model: Boosted Model or Forest Model tool, trained on rows before 2025-10-01, validated on October, tested on November and December (same time split as Python).
6. Output: Select and Formula tools to shape rows into docs/output_schema.md, stack = alteryx, written to outputs/alteryx/results_<run_id>.csv.

## Full data from the repo (data/full)

The full SYNTHETIC dataset is committed under data/full/<domain>/<dataset>/part_00000.parquet, part_00001.parquet and so on (zstd Parquet, each part 90 MB or less). data/full/manifest.json lists every part with its row count and SHA256 checksum.

1. Clone the repo (raw URLs are not practical for 20 million rows).
2. Add an Input Data tool and set the file path to a wildcard, for example `C:\repo\data\full\banking\B1_transactions\part_*.parquet`. Input Data unions every matching file into one stream (Parquet input needs Designer 2023.1 or later).
3. Tick "Output File Name as Field" if you want the part name kept for checks.
4. Compare the row count with the `rows` value for that dataset in data/full/manifest.json.

This has not been run in Alteryx here.
