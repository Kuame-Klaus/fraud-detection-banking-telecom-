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

## Klaus Konsults extensions beyond the pack

The tests below are not in the pack. They are Klaus Konsults extensions. Banking tests use only B datasets and telecom tests use only T datasets. Columns marked (open) are not in docs/data_dictionary.md and are listed in docs/open_questions.md.

### Banking

13. Dormant account wake up (B1, B2): B2 account_id, status, open_date, status_change_date. B1 account_id, timestamp, amount, direction. Flags accounts with no activity for a long period followed by sudden large activity.
14. KYC mismatch with expected volume (B1, B2): B2 account_id, kyc_level, expected_monthly_volume. B1 account_id, timestamp, amount. Compares actual monthly volume with expected volume and KYC level.
15. Impossible travel (B1, B9): B1 account_id, timestamp, country, terminal_id. B9 account_id, auth_time, terminal_id, terminal_type. Terminal location below country level (open).
16. Duplicate vendor payments (B10): vendor_id, vendor_bank_account, payment_id, payment_date, payment_amount. Invoice number (open).
17. Payroll after exit (B11): employee_id, exit_date, pay_date, pay_amount, employee_bank_account.
18. Privileged access changes before journals (B7, B8): B8 user_id, role, permission, change_time, changed_by, change_type. B7 preparer_id, approver_id, entry_timestamp, is_manual, debit, credit.
19. Benford's law (B7, B10): B7 debit, credit, account_code, preparer_id. B10 payment_amount, vendor_id.
20. Reversal abuse (B1, B7): B1 txn_id, reversal_flag, original_txn_id, amount, timestamp. B7 je_id, reversal_ind, document_type, preparer_id, entry_timestamp.

### Telecom

21. Wallet tier breach (T4, T5): T5 wallet_id, kyc_tier, wallet_limit. T4 wallet_id, timestamp, type, amount, balance_after. Tier limit values from T12 (reference_type, code, value).
22. Dormant wallet drain (T4, T5): T5 wallet_id, status, opened_at. T4 wallet_id, timestamp, type, amount, balance_before, balance_after.
23. Wangiri (T1): caller, callee, start_time, duration_sec, call_type. Call direction (inbound or outbound) and originating country (open).
24. IMEI churn (T1, T3): T1 caller, imei, imsi, start_time. T3 msisdn, swap_time, old_imei, new_imei.
25. Recharge fraud (T7): msisdn, event_time, event_type, amount, channel. Voucher or serial number (open).
26. Interconnect leakage (T1, T8): T1 route, call_type, duration_sec, start_time. T8 traffic_date, route, carrier, minutes, settlement_amount. Compares CDR minutes per route and day with settled minutes.
27. Agent float anomalies (T6): agent_id, region, movement_time, movement_type, float_amount, commission_amount.

## Planted synthetic cases

The generator plants labelled synthetic cases for all 27 scenarios above, and writes the scenario name to the label column (see python/synthetic/README.md).
