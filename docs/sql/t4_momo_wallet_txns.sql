-- Source: Fraud Audit Data Request and Extraction Pack, section 3 (verbatim)
-- Mobile money transactions (T4)

SELECT t.txn_id, t.wallet_id, t.txn_time AS timestamp, t.txn_type AS type, t.amount,
       t.counterparty_wallet AS counterparty, t.agent_id, t.balance_before,
       t.balance_after, t.status, t.reversal_of
FROM <momo_transaction_table> t
WHERE t.txn_time >= :start_date AND t.txn_time < :end_date;
