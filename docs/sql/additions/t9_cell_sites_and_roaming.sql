-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset T9. Cell site master joined to roaming records.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<cell_id> AS cell_id,
       t.<location> AS location,
       t.<roaming_record_id> AS roaming_record_id,
       t.<msisdn> AS msisdn,
       t.<roaming_country> AS roaming_country,
       t.<roaming_start_time> AS roaming_start_time
FROM <roaming_table> t
WHERE t.<roaming_start_time> >= :start_date AND t.<roaming_start_time> < :end_date;
