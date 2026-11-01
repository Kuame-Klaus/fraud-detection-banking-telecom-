# Pipeline steps

Every stack (Alteryx, KNIME, Python) runs these steps in this order, on synthetic data and on real client extracts alike. Steps 3 to 12 are the reconciliation and quality checks from the pack, section 4. The pack says to run them before any analysis and file the results with the working papers. Their results are written to the dq_results table in docs/output_schema.md.

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
13. Feature preparation and the scenario tests in docs/scenario_coverage.md.
14. Fixed time based splits, identical across stacks.
15. Train, score and evaluate models.
16. Write scores, metrics and dq_results in the shared schema.

On synthetic data, checks 4 and 6 compare against control totals and tie out figures that the generator writes alongside the data, since there is no client report.
