-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset B5. Devices and person_device_link.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<device_id> AS device_id,
       t.<imei_or_fingerprint> AS imei_or_fingerprint,
       t.<first_seen> AS first_seen,
       t.<last_seen> AS last_seen,
       t.<person_id> AS person_id
FROM <device_table> t
WHERE t.<last_seen> >= :start_date;
