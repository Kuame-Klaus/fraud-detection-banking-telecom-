-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset B12. Fraud cases, disputes, chargebacks and reversals.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<case_id> AS case_id,
       t.<entity_id> AS entity_id,
       t.<entity_type> AS entity_type,
       t.<scenario> AS scenario,
       t.<loss_amount> AS loss_amount,
       t.<reported_date> AS reported_date,
       t.<confirmed_date> AS confirmed_date,
       t.<outcome> AS outcome
FROM <fraud_case_table> t
WHERE t.<reported_date> >= :start_date AND t.<reported_date> < :end_date;
