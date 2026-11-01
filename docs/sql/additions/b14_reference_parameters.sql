-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset B14. Reference and parameters: channel, response, product and MCC codes, branch list, limits, rule thresholds.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<reference_type> AS reference_type,
       t.<code> AS code,
       t.<description> AS description,
       t.<limit_value> AS limit_value,
       t.<threshold_value> AS threshold_value
FROM <reference_table> t;
