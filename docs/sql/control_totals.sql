-- Source: Fraud Audit Data Request and Extraction Pack, section 4 (verbatim)
-- Control totals per month, to compare with the client's own report
SELECT DATE_TRUNC('month', txn_timestamp) AS month, COUNT(*) AS row_count,
       SUM(amount) AS total_amount
FROM <extract_table>
GROUP BY DATE_TRUNC('month', txn_timestamp);
