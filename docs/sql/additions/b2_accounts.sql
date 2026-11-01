-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset B2. Accounts.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<account_id> AS account_id,
       t.<person_id> AS person_id,
       t.<type> AS type,
       t.<open_date> AS open_date,
       t.<kyc_level> AS kyc_level,
       t.<expected_monthly_volume> AS expected_monthly_volume,
       t.<status> AS status,
       t.<branch> AS branch,
       t.<status_change_date> AS status_change_date,
       t.<kyc_change_date> AS kyc_change_date
FROM <account_table> t
WHERE t.<open_date> < :end_date;
