# Data

No real data is ever committed to this public repository. Everything under data/ is ignored by git except data/sample/, which holds SYNTHETIC sample CSVs made by python/synthetic/generate.py (about 50,000 rows for each main table, all planted cases labelled in synthetic_scenario), and data/full/, which holds the full SYNTHETIC dataset as zstd Parquet parts of 90 MB or less with data/full/manifest.json (row counts and SHA256 checksums).

* data/raw/ holds downloaded public datasets used only for calibration.
* data/synthetic/ holds SYNTHETIC data regenerated locally with the command in python/synthetic/README.md. Files carry a synthetic_ prefix and their dataset ID.
* data/partner/ is reserved for approved real client extracts, handled under docs/engagement_rules.md, and must never be committed.

Dataset IDs and columns are in docs/data_dictionary.md.
