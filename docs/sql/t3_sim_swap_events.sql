-- Source: Fraud Audit Data Request and Extraction Pack, section 3 (verbatim)
-- SIM swaps (T3)

SELECT s.swap_id, s.sim_id, s.msisdn, s.swap_time, s.old_imei, s.new_imei,
       s.channel, s.performed_by_user, s.shop_id
FROM <sim_replacement_log> s
WHERE s.swap_time >= :start_date AND s.swap_time < :end_date;
