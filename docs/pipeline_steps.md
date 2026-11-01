# Pipeline steps

## Stages

1. Load and control totals (steps 1 to 4).
2. Data quality checks (steps 5 to 12).
3. Features (step 13).
4. Scenario rules (step 14).
5. Model: XGBoost in Python, built in learners in Alteryx and KNIME (steps 15 to 16).
6. Shared results output, including the detection review checks (steps 17 to 22).

## Steps

Every stack (Alteryx, KNIME, Python) runs the same six stages and the numbered steps below in this order, on synthetic data and on real client extracts alike. Steps 3 to 12 are the reconciliation and quality checks from the pack, section 4. The pack says to run them before any analysis and file the results with the working papers. Their results are written as dq rows in the shared results file (docs/output_schema.md).

1. Log chain of custody for each input file: extract date, query, person and a SHA 256 hash (pack section 1).
2. Load inputs from data/synthetic/ or the approved client location, using the dataset IDs and column names in docs/data_dictionary.md.
3. Control totals per month: row count and amount total per table per month, using docs/sql/control_totals.sql, plus the ADDITION queries docs/sql/additions/b7_control_totals.sql (debits and credits by month) and docs/sql/additions/t1_control_totals.sql (row count and duration by day), or the stack equivalent.
4. Compare control totals with the client's own totals per month. Row counts and amount totals must match.
5. Journal debits equal credits per entry (B7).
6. Bank totals tie to the GL and trial balance. Mobile money totals tie to the trust account. Billing totals tie to revenue.
7. No gaps: every day in the period has data, and sudden volume drops are flagged as possible missing files.
8. Keys are unique, and no transaction points to a missing account, wallet or agent (orphans).
9. Timestamps are in one time zone, none sit in the future, and entry time is not before posting logic allows.
10. Amounts are in a known currency, negatives and zero values are explained, and reversals link to their originals.
11. Null rates per column are reported. High null rates in device, IP, preparer or approver fields are flagged for explanation before use.
12. Any field that cannot be supplied is recorded as a limitation, with the tests it blocks (see docs/scenario_coverage.md).
13. Feature preparation, within banking or within telecom only.
14. Scenario rules for all 27 scenarios in docs/scenario_coverage.md, including the Klaus Konsults extensions.
15. Fixed time based splits, identical across stacks.
16. Train, score and evaluate the model: XGBoost in Python, and the built in learners in Alteryx and KNIME (for example their gradient boosted trees).
17. Rule coverage gaps: list scenarios with no rule or model firing, and rules that map to no scenario.
18. Threshold sensitivity: rerun each rule and model threshold at minus 20%, minus 10%, plus 10% and plus 20% of its base value, and record alert counts and detection for each.
19. Monthly score drift: compare the score distribution of each month with the training period.
20. Agreement between the three tools: compare predicted labels and scores for the same record_id across Alteryx, KNIME and Python.
21. Build the chart inputs listed in docs/charts.md (network edges, Benford counts, route and cell aggregates).
22. Write everything to the shared results file in docs/output_schema.md.

On synthetic data, checks 4 and 6 compare against control totals and tie out figures that the generator writes alongside the data, since there is no client report.
