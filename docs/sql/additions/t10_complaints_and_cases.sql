-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset T10. Complaints, blocked SIMs and fraud cases.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<case_id> AS case_id,
       t.<msisdn> AS msisdn,
       t.<scenario> AS scenario,
       t.<case_date> AS case_date,
       t.<outcome> AS outcome
FROM <telecom_case_table> t
WHERE t.<case_date> >= :start_date AND t.<case_date> < :end_date;
