# Data dictionary

The dataset request list below is copied faithfully from the Fraud Audit Data Request and Extraction Pack, section 2. Synthetic data uses these dataset IDs and names so the same pipeline runs unchanged on real client extracts.

Priority: M = must have, S = should have, N = nice to have.

## Banking (B1 to B14)

| ID | Dataset | Key fields | Used for | Typical source | P |
|---|---|---|---|---|---|
| B1 | transactions | txn_id, account_id, timestamp, amount, currency, channel, merchant_id, mcc, counterparty_account, terminal_id, country, response_code, direction, balance_before, balance_after, reversal flag, original txn id | Card testing, takeover, mules, structuring, velocity and amount tests | Core banking, card switch | M |
| B2 | accounts | account_id, person_id, type, open_date, kyc_level, expected_monthly_volume, status, branch, change dates | Baselines, dormant account activity, KYC mismatch | Core banking | M |
| B3 | persons | person_id, name (hashed), national_id_hash, dob, region, occupation, income band, phone, email, address change history | Identity linkage, synthetic identity, profile versus activity | CRM, KYC | M |
| B4 | auth_events | person_id, device_id, ip, geo, event_type (login, failed login, OTP, password reset, device change), timestamp | Account takeover | Internet and mobile banking logs | M |
| B5 | devices and person_device_link | device_id, imei or fingerprint, first_seen, last_seen, person link | Shared devices, device change | Digital banking platform | S |
| B6 | beneficiaries | account_id, payee_account, added_at, added_via_device | Mule and takeover patterns | Digital banking | M |
| B7 | gl_journal | line_id, je_id, posting_date, entry_timestamp, account_code, debit, credit, preparer_id, approver_id, is_manual, description, document type, reversal flag | Journal entry testing | SAP, Oracle, core GL | M |
| B8 | users_access | user_id, role, permissions, active flag, access change log, last login | Segregation of duties, privileged users | SAP, core banking, Active Directory | M |
| B9 | card master and authorisations | card id, status, issue date, auth log with declines, ATM and POS terminal data | Card fraud | Card switch | S |
| B10 | vendors and supplier payments | vendor_id, name, bank account, address, created_by, created_at, payments with approver | Ghost vendors, duplicate payments | ERP | S |
| B11 | payroll and HR | employee_id, bank account, hire and exit dates, department, pay run, attendance | Ghost employees, insider conflicts | HR, payroll | S |
| B12 | fraud cases, disputes, chargebacks, reversals | case id, entity, scenario, loss, reported date, confirmed date, outcome | Labels, loss trend | Fraud team, disputes | M |
| B13 | existing alerts | alert id, rule or model, score, entity, date, analyst, disposition | Review of current detection, false positive rate | Monitoring tool | M in review mode |
| B14 | reference and parameters | channel, response, product and MCC codes, branch list, limits, rule thresholds | Interpret fields, test threshold design | Core system, policy documents | M |

## Telecom and mobile money (T1 to T12)

| ID | Dataset | Key fields | Used for | Typical source | P |
|---|---|---|---|---|---|
| T1 | cdrs | cdr_id, caller, callee, start_time, duration_sec, call_type, cell_id, route or trunk, imsi, imei, charge, roaming flag | SIM box, bypass, bust-out, usage anomalies | Mediation, billing | M |
| T2 | subscribers | msisdn, person_id, activation_date, plan, kyc_status, id number hash, credit_limit, registration channel and shop | Subscription fraud, duplicate IDs | CRM, KYC registry | M |
| T3 | sims and sim_swap_events | sim_id, msisdn, imsi, imei, swap time, old and new imei, channel, staff or shop id | SIM swap fraud, insider involvement | CRM, provisioning | M |
| T4 | momo_wallet_txns | txn_id, wallet_id, timestamp, type, amount, counterparty, agent_id, balance_before, balance_after, status, reversal | Wallet drain, mules, structuring | Mobile money platform | M |
| T5 | wallets | wallet_id, msisdn, person_id, opened_at, status, KYC tier, limits | Tier limit breaches, dormant wallets | Mobile money platform | M |
| T6 | agents | agent_id, region, onboarded_at, commission_rate, status, float movements, commission payouts | Agent collusion, float anomalies | Mobile money platform, finance | M |
| T7 | topups_billing | msisdn, event_time, event_type, amount, channel, invoice status, collections, bad debt | Bust-out, recharge fraud | Billing | M |
| T8 | interconnect and gateway traffic | route, carrier, minutes, settlement amounts per day | SIM box, grey routes, revenue leakage | Interconnect billing | S |
| T9 | cell site master and roaming | cell_id, location, roaming records | Location checks, impossible travel | Network | N |
| T10 | complaints, blocked SIMs, fraud cases | case, msisdn, scenario, date, outcome | Labels | Fraud team, customer care | M |
| T11 | existing alerts and rules | as B13, plus fraud management system rule set | Review of current detection | Fraud management system | M in review mode |
| T12 | reference and parameters | tariffs, limits, KYC tiers, agent commission scheme | Interpret fields, check thresholds | Policy, finance | M |

## Target column names

Where the pack gives a SQL template, the output aliases in that template are the exact target column names. These are used as is by the generator and by every stack:

1. B1 transactions: txn_id, account_id, timestamp, amount, currency, channel, merchant_id, mcc, counterparty_account, terminal_id, country, response_code, direction, balance_before, balance_after, reversal_flag, original_txn_id
2. B4 auth_events: event_id, person_id, device_id, ip, geo, event_type, timestamp
3. B7 gl_journal: line_id, je_id, posting_date, entry_timestamp, account_code, debit, credit, preparer_id, approver_id, is_manual, description, document_type, reversal_ind
4. B8 users_access: user_id, is_active, role, permission, last_login, change_time, changed_by, change_type
5. T1 cdrs: cdr_id, caller, callee, start_time, duration_sec, call_type, cell_id, route, imsi, imei, charge
6. T1 daily summary: caller_msisdn, call_day, outbound_calls, intl_calls, avg_duration, short_calls, distinct_callees, distinct_cells
7. T3 sim_swap_events: swap_id, sim_id, msisdn, swap_time, old_imei, new_imei, channel, performed_by_user, shop_id
8. T4 momo_wallet_txns: txn_id, wallet_id, timestamp, type, amount, counterparty, agent_id, balance_before, balance_after, status, reversal_of
9. T6 agents: agent_id, region, onboarded_at, commission_rate, status, movement_time, movement_type, float_amount, payout_date, commission_amount

## Provisional default columns (ASSUMPTION)

These are defaults set by Klaus Konsults for datasets without a pack SQL template. The client can override any of them. Names marked ASSUMPTION were turned into snake_case from the pack's wording. Unmarked names already appear as column names in the pack.

| ID | Columns |
|---|---|
| B2 | account_id, person_id, type, open_date, kyc_level, expected_monthly_volume, status, branch, status_change_date (ASSUMPTION), kyc_change_date (ASSUMPTION) |
| B3 | person_id, name_hash (ASSUMPTION), national_id_hash, dob, region, occupation, income_band (ASSUMPTION), phone (hashed under the pack ground rules), email_hash (ASSUMPTION), address_hash (ASSUMPTION), address_change_date (ASSUMPTION) |
| B5 | device_id, imei_or_fingerprint (ASSUMPTION), first_seen, last_seen, person_id (ASSUMPTION) |
| B6 | account_id, payee_account, added_at, added_via_device |
| B9 | card_id (ASSUMPTION), account_id (ASSUMPTION), card_status (ASSUMPTION), issue_date (ASSUMPTION), auth_id (ASSUMPTION), auth_time (ASSUMPTION), amount (ASSUMPTION), response_code (ASSUMPTION), terminal_id (ASSUMPTION), terminal_type (ASSUMPTION) |
| B10 | vendor_id, vendor_name (ASSUMPTION), vendor_bank_account (ASSUMPTION), vendor_address (ASSUMPTION), created_by, created_at, payment_id (ASSUMPTION), payment_date (ASSUMPTION), payment_amount (ASSUMPTION), payment_approver_id (ASSUMPTION) |
| B11 | employee_id, employee_bank_account (ASSUMPTION), hire_date (ASSUMPTION), exit_date (ASSUMPTION), department, pay_run_id (ASSUMPTION), pay_date (ASSUMPTION), pay_amount (ASSUMPTION), attendance_days (ASSUMPTION) |
| B12 | case_id (ASSUMPTION), entity_id (ASSUMPTION), entity_type (ASSUMPTION), scenario, loss_amount (ASSUMPTION), reported_date (ASSUMPTION), confirmed_date (ASSUMPTION), outcome |
| B13 | alert_id (ASSUMPTION), rule_or_model (ASSUMPTION), score, entity_id (ASSUMPTION), alert_date (ASSUMPTION), analyst_id (ASSUMPTION), disposition |
| B14 | reference_type (ASSUMPTION), code (ASSUMPTION), description (ASSUMPTION), limit_value (ASSUMPTION), threshold_value (ASSUMPTION) |
| T2 | msisdn, person_id, activation_date, plan, kyc_status, id_number_hash (ASSUMPTION), credit_limit, registration_channel (ASSUMPTION), registration_shop_id (ASSUMPTION) |
| T5 | wallet_id, msisdn, person_id, opened_at, status, kyc_tier (ASSUMPTION), wallet_limit (ASSUMPTION) |
| T7 | msisdn, event_time, event_type, amount, channel, invoice_status (ASSUMPTION), collections_amount (ASSUMPTION), bad_debt_amount (ASSUMPTION) |
| T8 | traffic_date (ASSUMPTION), route, carrier, minutes, settlement_amount (ASSUMPTION) |
| T9 | cell_id, location, roaming_record_id (ASSUMPTION), msisdn (ASSUMPTION), roaming_country (ASSUMPTION), roaming_start_time (ASSUMPTION) |
| T10 | case_id (ASSUMPTION), msisdn, scenario, case_date (ASSUMPTION), outcome |
| T11 | alert_id (ASSUMPTION), rule_or_model (ASSUMPTION), score, entity_id (ASSUMPTION), alert_date (ASSUMPTION), analyst_id (ASSUMPTION), disposition, rule_id (ASSUMPTION), rule_definition (ASSUMPTION), rule_threshold (ASSUMPTION) |
| T12 | reference_type (ASSUMPTION), code (ASSUMPTION), description (ASSUMPTION), value (ASSUMPTION) |
| T1 | roaming_flag (ASSUMPTION), added to the T1 SQL columns because the field list includes it |

## Separate entities

Banking (B datasets) and telecom (T datasets) are two separate entities. No keys are shared between them and no joins are made across them. Where person_id appears in both a B and a T dataset, as in the pack, it is a key local to that entity only.
