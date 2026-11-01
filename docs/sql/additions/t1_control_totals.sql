-- ADDITION: written by Klaus Konsults, not part of the pack. Provisional default; the client can override.
-- T1 cdrs control totals per day: row count and total duration.

SELECT CAST(start_time AS DATE) AS call_day, COUNT(*) AS row_count,
       SUM(duration_sec) AS total_duration_sec
FROM <extract_table>
GROUP BY CAST(start_time AS DATE);
