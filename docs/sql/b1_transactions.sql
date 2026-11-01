-- Source: Fraud Audit Data Request and Extraction Pack, section 3 (verbatim)
-- Transactions (B1)

SELECT t.txn_id, t.account_id, t.txn_timestamp AS timestamp, t.amount, t.currency,
       t.channel_code AS channel, t.merchant_id, t.mcc, t.counterparty_account,
       t.terminal_id, t.country_code AS country, t.response_code,
       t.dr_cr_ind AS direction, t.balance_before, t.balance_after,
       t.reversal_flag, t.original_txn_id
FROM <transaction_table> t
WHERE t.txn_timestamp >= :start_date AND t.txn_timestamp < :end_date;
