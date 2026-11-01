-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset B3. Persons. Hash names, phone, email and address unless a test needs them; the client keeps the key.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<person_id> AS person_id,
       t.<name_hash> AS name_hash,
       t.<national_id_hash> AS national_id_hash,
       t.<dob> AS dob,
       t.<region> AS region,
       t.<occupation> AS occupation,
       t.<income_band> AS income_band,
       t.<phone> AS phone,
       t.<email_hash> AS email_hash,
       t.<address_hash> AS address_hash,
       t.<address_change_date> AS address_change_date
FROM <customer_table> t;
