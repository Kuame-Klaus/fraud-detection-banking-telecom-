-- Source: Fraud Audit Data Request and Extraction Pack, section 3 (verbatim)
-- Authentication events (B4)

SELECT e.event_id, e.customer_id AS person_id, e.device_id, e.ip_address AS ip,
       e.geo_location AS geo, e.event_type, e.event_time AS timestamp
FROM <digital_banking_event_log> e
WHERE e.event_time >= :start_date AND e.event_time < :end_date;
