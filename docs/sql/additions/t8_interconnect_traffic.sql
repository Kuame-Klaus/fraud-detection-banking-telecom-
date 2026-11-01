-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset T8. Interconnect and gateway traffic, one row per route, carrier and day.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<traffic_date> AS traffic_date,
       t.<route> AS route,
       t.<carrier> AS carrier,
       t.<minutes> AS minutes,
       t.<settlement_amount> AS settlement_amount
FROM <interconnect_table> t
WHERE t.<traffic_date> >= :start_date AND t.<traffic_date> < :end_date;
