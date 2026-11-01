-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset T7. Top ups and billing events.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<msisdn> AS msisdn,
       t.<event_time> AS event_time,
       t.<event_type> AS event_type,
       t.<amount> AS amount,
       t.<channel> AS channel,
       t.<invoice_status> AS invoice_status,
       t.<collections_amount> AS collections_amount,
       t.<bad_debt_amount> AS bad_debt_amount
FROM <billing_event_table> t
WHERE t.<event_time> >= :start_date AND t.<event_time> < :end_date;
