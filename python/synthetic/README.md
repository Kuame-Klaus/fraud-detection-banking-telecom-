# Synthetic data generator (plan)

All data produced here is SYNTHETIC. It is not real customer, client or partner data.

## Purpose

Generate about 20 million rows for banking and about 20 million rows for telecom, reproducibly, using the dataset IDs and column names in docs/data_dictionary.md. Alteryx, KNIME and Python then run on identical inputs, and the same pipeline later runs unchanged on real client extracts.

## Datasets

1. Banking: B1 transactions, B2 accounts, B3 persons, B4 auth_events, B5 devices and person_device_link, B6 beneficiaries, B7 gl_journal, B8 users_access, B9 card master and authorisations, B10 vendors and supplier payments, B11 payroll and HR, B12 fraud cases, B13 existing alerts, B14 reference and parameters.
2. Telecom and mobile money: T1 cdrs, T2 subscribers, T3 sims and sim_swap_events, T4 momo_wallet_txns, T5 wallets, T6 agents, T7 topups_billing, T8 interconnect and gateway traffic, T9 cell site master and roaming, T10 complaints, blocked SIMs and fraud cases, T11 existing alerts and rules, T12 reference and parameters.

Columns follow docs/data_dictionary.md: pack SQL names where they exist, and provisional default names marked ASSUMPTION elsewhere. The client can override any default.

## Sizing (ASSUMPTION)

About 20 million rows in B1 for banking and in T1 for telecom, with T4 at a similar scale. Other tables are sized in config.yaml with proportions chosen to look realistic. These proportions are assumptions, not client figures.

## Separate entities

Banking and telecom are generated as two separate entities, with no shared keys and no joins between them.

## Design

1. Fixed seed: the same config and seed always give the same files.
2. Config file: config.yaml holds the seed, row counts, chunk size, output format, period and scenario settings.
3. Calibration: amount, time and type distributions and fraud rates come from the public Kaggle credit card fraud dataset and PaySim. Only summary statistics are used and no records are copied. Telecom scenarios use documented assumptions recorded in docs/.
4. Planted cases: labelled synthetic cases are planted for every one of the 27 scenarios in docs/scenario_coverage.md, including the Klaus Konsults extensions. Every row of every event table carries a label column, synthetic_scenario, holding the scenario name (empty for normal rows). Confirmed cases are also written to B12 and T10. Banking cases stay in banking tables and telecom cases in telecom tables. The share of planted cases per scenario is set in config.yaml and is a provisional default, not a measured rate.
5. Pack format rules: UTF 8, ISO 8601 timestamps with the time zone stated, decimal amounts with currency, and one file per month for large tables.
6. Output: chunked Parquet by default, with a CSV option. Files are named with a synthetic_ prefix and the dataset ID, for example synthetic_B1_transactions_2025_01_part_0001.parquet.
7. Control totals: each run also writes row counts and amount totals per table per month, plus tie out figures, so pipeline steps 3 to 6 can be tested, including the B7 and T1 control totals in docs/sql/additions/.
8. Manifest: seed, config hash, row counts, SHA 256 hash of each file and a synthetic flag.
9. Location: data/synthetic/banking/ and data/synthetic/telecom/, both ignored by git.

## Command (planned)

    python python/synthetic/generate.py --config python/synthetic/config.yaml

Set format: csv in the config for CSV. Delete the local data/synthetic/ folder and rerun the command to regenerate.
