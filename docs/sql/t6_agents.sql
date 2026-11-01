-- Source: Fraud Audit Data Request and Extraction Pack, section 3 (verbatim)
-- Agent float and commission (T6)

SELECT a.agent_id, a.region, a.onboarded_at, a.commission_rate, a.status,
       f.movement_time, f.movement_type, f.amount AS float_amount,
       c.payout_date, c.commission_amount
FROM <agent_master> a
LEFT JOIN <agent_float_ledger> f ON f.agent_id = a.agent_id AND f.movement_time >= :start_date
LEFT JOIN <agent_commission_ledger> c ON c.agent_id = a.agent_id AND c.payout_date >= :start_date;
