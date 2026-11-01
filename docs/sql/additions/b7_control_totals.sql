-- ADDITION: written by Klaus Konsults, not part of the pack. Provisional default; the client can override.
-- B7 gl_journal control totals per month, plus a debit equals credit check per entry.

SELECT DATE_TRUNC('month', entry_timestamp) AS month, COUNT(*) AS row_count,
       SUM(debit) AS total_debit, SUM(credit) AS total_credit,
       SUM(debit) - SUM(credit) AS difference
FROM <extract_table>
GROUP BY DATE_TRUNC('month', entry_timestamp);

-- Entries that do not balance (expect zero rows)
SELECT je_id, SUM(debit) AS total_debit, SUM(credit) AS total_credit
FROM <extract_table>
GROUP BY je_id
HAVING SUM(debit) <> SUM(credit);
