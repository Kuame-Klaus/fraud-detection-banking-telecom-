# SQL additions (provisional defaults)

Nothing in this folder comes from the pack. Klaus Konsults wrote these files as provisional defaults, and the client can override any of them. The pack's own SQL stays unchanged in docs/sql/.

1. b7_control_totals.sql and t1_control_totals.sql are marked ADDITION. They extend the pack's control totals to tables without txn_timestamp and amount.
2. Every other file is marked ASSUMPTION. Each is a template for a dataset the pack gives no SQL for, written in the pack's style: names in angle brackets, :start_date and :end_date parameters, and output aliases matching docs/data_dictionary.md. Source columns are shown as <placeholder> and must be mapped from the client's schema.
