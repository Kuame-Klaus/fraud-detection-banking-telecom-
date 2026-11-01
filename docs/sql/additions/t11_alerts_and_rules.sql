-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset T11. Existing alerts (as B13) plus the fraud management system rule set.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<alert_id> AS alert_id,
       t.<rule_or_model> AS rule_or_model,
       t.<score> AS score,
       t.<entity_id> AS entity_id,
       t.<alert_date> AS alert_date,
       t.<analyst_id> AS analyst_id,
       t.<disposition> AS disposition,
       t.<rule_id> AS rule_id,
       t.<rule_definition> AS rule_definition,
       t.<rule_threshold> AS rule_threshold
FROM <fms_alert_table> t
WHERE t.<alert_date> >= :start_date AND t.<alert_date> < :end_date;
