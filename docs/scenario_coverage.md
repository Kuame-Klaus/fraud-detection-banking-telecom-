# Scenario to data coverage

Copied faithfully from the pack, section 5, with one decided change: the SIM swap row uses T3, T4 and T2 instead of T3, T4 and B4, because banking and telecom are separate entities.

| Scenario | Datasets needed | Core tests |
|---|---|---|
| Card testing | B1, B9 | Bursts of small transactions across many merchants, high decline rate |
| Account takeover | B4, B5, B6, B1 | New device, password reset, new beneficiary, large transfer within hours |
| Mule network | B1, B6, B3 | Many unrelated senders to one account, quick withdrawal |
| Structuring | B1, B14 | Repeated amounts just under a limit to the same counterparty |
| Journal abuse | B7, B8 | Night or weekend entries, same preparer and approver, round amounts, suspense accounts |
| Segregation of duties | B8, B10 | Users who can create vendors and approve payments |
| Ghost vendor or employee | B10, B11, B3 | Vendor or payroll bank accounts matching staff, no HR or attendance trail |
| SIM swap fraud | T3, T4, T2 | Swap followed by OTP requests and wallet drain |
| SIM box and bypass | T1, T8 | Many short outbound international calls, almost no inbound |
| Subscription and bust-out | T2, T1, T7 | Shared ID numbers, usage ramp, unpaid invoices |
| Agent fraud | T4, T6 | Repeated cash-in and cash-out pairs just under a threshold, odd hours |
| Insider SIM swap or access abuse | T3, B8 | Swaps by the same staff or shop, access changes before incidents |

## Columns each test uses

Column names come from docs/data_dictionary.md. Columns marked (open) are described in words in the pack and are not yet fixed; see docs/open_questions.md.

1. Card testing (B1, B9): B1 merchant_id, mcc, amount, response_code, timestamp, terminal_id. B9 card id, auth log with declines (open).
2. Account takeover (B4, B5, B6, B1): B4 person_id, device_id, ip, geo, event_type, timestamp. B5 device_id, first_seen, person link (open). B6 account_id, payee_account, added_at, added_via_device. B1 account_id, amount, timestamp, counterparty_account.
3. Mule network (B1, B6, B3): B1 counterparty_account, account_id, direction, amount, timestamp. B6 payee_account, added_at. B3 person_id, national_id_hash, phone.
4. Structuring (B1, B14): B1 amount, counterparty_account, account_id, timestamp. B14 limits, rule thresholds.
5. Journal abuse (B7, B8): B7 entry_timestamp, posting_date, preparer_id, approver_id, debit, credit, account_code, is_manual, description. B8 user_id, role, permission.
6. Segregation of duties (B8, B10): B8 user_id, role, permission, change_time, change_type. B10 vendor_id, created_by, payments with approver (open).
7. Ghost vendor or employee (B10, B11, B3): B10 vendor_id, bank account (open), address, created_by. B11 employee_id, bank account (open), hire and exit dates (open), attendance. B3 person_id, address change history (open).
8. SIM swap fraud (T3, T4, T2): T3 msisdn, swap_time, old_imei, new_imei, channel. T4 wallet_id, timestamp, type, amount, balance_after. T2 msisdn, activation_date, kyc_status. T4 wallet_id maps to msisdn through T5 within telecom. OTP requests are not in any T dataset, so the test uses the swap followed by wallet drain.
9. SIM box and bypass (T1, T8): T1 caller, callee, call_type, duration_sec, cell_id, route, imei, and the daily summary columns. T8 route, carrier, minutes, settlement amounts per day (open).
10. Subscription and bust out (T2, T1, T7): T2 msisdn, person_id, activation_date, id number hash (open), credit_limit. T1 caller, start_time, charge. T7 msisdn, event_time, event_type, amount, invoice status (open), bad debt (open).
11. Agent fraud (T4, T6): T4 agent_id, type, amount, timestamp. T6 agent_id, movement_time, movement_type, float_amount, commission_amount. T12 agent commission scheme and limits for the threshold.
12. Insider SIM swap or access abuse (T3, B8): T3 performed_by_user, shop_id, swap_time. B8 user_id, change_time, changed_by, change_type.

## Other uses listed in the request list

These appear in the "Used for" column but not in the scenario table. They are carried as extra tests: velocity and amount tests (B1), dormant account activity and KYC mismatch (B2), synthetic identity and profile versus activity (B3), duplicate payments (B10), duplicate IDs (T2), wallet drain and tier limit breaches (T4, T5), dormant wallets (T5), recharge fraud (T7), grey routes and revenue leakage (T8), impossible travel (T9), and review of current detection using B13 and T11.

## Labels

B12 and T10 supply fraud labels for the true_label column in the shared output schema.
