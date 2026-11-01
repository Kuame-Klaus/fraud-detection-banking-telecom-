-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset B9. Card master and authorisations, one row per authorisation.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<card_id> AS card_id,
       t.<account_id> AS account_id,
       t.<card_status> AS card_status,
       t.<issue_date> AS issue_date,
       t.<auth_id> AS auth_id,
       t.<auth_time> AS auth_time,
       t.<amount> AS amount,
       t.<response_code> AS response_code,
       t.<terminal_id> AS terminal_id,
       t.<terminal_type> AS terminal_type
FROM <card_auth_table> t
WHERE t.<auth_time> >= :start_date AND t.<auth_time> < :end_date;
