-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset B10. Vendors and supplier payments, one row per payment.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<vendor_id> AS vendor_id,
       t.<vendor_name> AS vendor_name,
       t.<vendor_bank_account> AS vendor_bank_account,
       t.<vendor_address> AS vendor_address,
       t.<created_by> AS created_by,
       t.<created_at> AS created_at,
       t.<payment_id> AS payment_id,
       t.<payment_date> AS payment_date,
       t.<payment_amount> AS payment_amount,
       t.<payment_approver_id> AS payment_approver_id
FROM <vendor_payment_table> t
WHERE t.<payment_date> >= :start_date AND t.<payment_date> < :end_date;
