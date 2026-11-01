-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset B6. Beneficiaries.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<account_id> AS account_id,
       t.<payee_account> AS payee_account,
       t.<added_at> AS added_at,
       t.<added_via_device> AS added_via_device
FROM <beneficiary_table> t
WHERE t.<added_at> >= :start_date AND t.<added_at> < :end_date;
