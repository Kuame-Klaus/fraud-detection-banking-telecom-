-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset T5. Wallets.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<wallet_id> AS wallet_id,
       t.<msisdn> AS msisdn,
       t.<person_id> AS person_id,
       t.<opened_at> AS opened_at,
       t.<status> AS status,
       t.<kyc_tier> AS kyc_tier,
       t.<wallet_limit> AS wallet_limit
FROM <wallet_table> t
WHERE t.<opened_at> < :end_date;
