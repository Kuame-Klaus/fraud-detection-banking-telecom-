-- Source: Fraud Audit Data Request and Extraction Pack, section 3 (verbatim)
-- Call detail records (T1). CDR tables are huge. Extract one day at a time, and also run the daily summary below, which is often enough for SIM box and bust-out tests.

SELECT cdr_id, caller_msisdn AS caller, called_number AS callee, start_time,
       duration_sec, call_type, cell_id, route_id AS route, imsi, imei, charge
FROM <cdr_table>
WHERE start_time >= :day_start AND start_time < :day_end;

-- Daily summary per subscriber
SELECT caller_msisdn, CAST(start_time AS DATE) AS call_day,
       COUNT(*) AS outbound_calls,
       SUM(CASE WHEN call_type = 'intl_voice' THEN 1 ELSE 0 END) AS intl_calls,
       AVG(duration_sec) AS avg_duration,
       SUM(CASE WHEN duration_sec < 30 THEN 1 ELSE 0 END) AS short_calls,
       COUNT(DISTINCT called_number) AS distinct_callees,
       COUNT(DISTINCT cell_id) AS distinct_cells
FROM <cdr_table>
WHERE start_time >= :start_date AND start_time < :end_date
GROUP BY caller_msisdn, CAST(start_time AS DATE);
