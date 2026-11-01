-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset T12. Reference and parameters: tariffs, limits, KYC tiers, agent commission scheme.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<reference_type> AS reference_type,
       t.<code> AS code,
       t.<description> AS description,
       t.<value> AS value
FROM <telecom_reference_table> t;
