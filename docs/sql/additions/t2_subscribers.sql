-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset T2. Subscribers.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<msisdn> AS msisdn,
       t.<person_id> AS person_id,
       t.<activation_date> AS activation_date,
       t.<plan> AS plan,
       t.<kyc_status> AS kyc_status,
       t.<id_number_hash> AS id_number_hash,
       t.<credit_limit> AS credit_limit,
       t.<registration_channel> AS registration_channel,
       t.<registration_shop_id> AS registration_shop_id
FROM <subscriber_table> t
WHERE t.<activation_date> < :end_date;
