# Alteryx build prompt

A Klaus Konsults project. All data is SYNTHETIC.

**Status: UNTESTED in Alteryx.** This prompt was written from the Python code and the committed data, not from a working Alteryx build. Tool and node names, settings and macros are a design to follow; check each one in Alteryx. The rule logic, schemas, row counts and expected values are real and were read from the repo.

## How to use this prompt

Paste this whole file into an AI assistant and ask it to guide you through building the Alteryx workflow, or follow it by hand. The goal is an Alteryx build that reads the same files as the Python pipeline, runs the same six stages, and writes the same shared results file, so the three tools can be compared record by record. Banking and telecom are separate entities: never join a B table to a T table.

Sources used for this prompt: pipeline code, data/full/manifest.json and data/sample at commit a689b4b, which includes the fixed insider SIM swap (R_T09) and IMEI churn (R_T10) rules. The committed outputs/sample/results_latest.csv (commit 6949f0b) predates that fix, so every expected value below was recomputed by running `python -m python.pipeline.run --data data/sample` at commit a689b4b (run_id python_sample_recheck, not committed).

## Inputs and the source switch

config/data_source.yaml holds `source: sample_url` (default) or `local_full`.

1. **sample_url.** Read each dataset straight from GitHub as CSV. No download or clone is needed. Timestamps in the CSVs look like 2025-01-22T23:21:46Z. Empty cells are empty strings.
2. **local_full.** Clone the repo and read the numbered Parquet parts under data/full/<domain>/<dataset_name>/, listed in data/full/manifest.json. Note: config/sources.csv and config/data_source.yaml still point local_full at data/synthetic/full (the generator's own output folder). The committed full parts are in data/full. Use data/full for this build unless you generated your own data. At commit a689b4b the T3 sample CSV was regenerated with the fixed planting, but the committed full T3 parts were not changed in that commit, so check full size T3 results again once the full data is regenerated.

| dataset | sample rows | sample raw URL | full parts (local) |
|---|---|---|---|
| B1 | 50,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B1_transactions.csv | data/full/banking/B1_transactions/part_00000.parquet to part_00019.parquet |
| B2 | 1,875 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B2_accounts.csv | data/full/banking/B2_accounts/part_00000.parquet to part_00000.parquet |
| B3 | 1,250 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B3_persons.csv | data/full/banking/B3_persons/part_00000.parquet to part_00000.parquet |
| B4 | 25,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B4_auth_events.csv | data/full/banking/B4_auth_events/part_00000.parquet to part_00009.parquet |
| B5 | 2,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B5_devices.csv | data/full/banking/B5_devices/part_00000.parquet to part_00000.parquet |
| B6 | 3,750 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B6_beneficiaries.csv | data/full/banking/B6_beneficiaries/part_00000.parquet to part_00000.parquet |
| B7 | 5,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B7_gl_journal.csv | data/full/banking/B7_gl_journal/part_00000.parquet to part_00001.parquet |
| B8 | 50 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B8_users_access.csv | data/full/banking/B8_users_access/part_00000.parquet to part_00000.parquet |
| B9 | 15,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B9_cards_and_authorisations.csv | data/full/banking/B9_cards_and_authorisations/part_00000.parquet to part_00005.parquet |
| B10 | 250 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B10_vendors_and_payments.csv | data/full/banking/B10_vendors_and_payments/part_00000.parquet to part_00000.parquet |
| B11 | 180 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B11_payroll_and_hr.csv | data/full/banking/B11_payroll_and_hr/part_00000.parquet to part_00000.parquet |
| B12 | 50 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B12_fraud_cases.csv | data/full/banking/B12_fraud_cases/part_00000.parquet to part_00000.parquet |
| B13 | 500 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B13_existing_alerts.csv | data/full/banking/B13_existing_alerts/part_00000.parquet to part_00000.parquet |
| B14 | 5 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/banking/B14_reference_parameters.csv | data/full/banking/B14_reference_parameters/part_00000.parquet to part_00000.parquet |
| T1 | 50,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T1_cdrs.csv | data/full/telecom/T1_cdrs/part_00000.parquet to part_00019.parquet |
| T2 | 2,500 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T2_subscribers.csv | data/full/telecom/T2_subscribers/part_00000.parquet to part_00000.parquet |
| T3 | 2,750 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T3_sims_and_sim_swap_events.csv | data/full/telecom/T3_sims_and_sim_swap_events/part_00000.parquet to part_00000.parquet |
| T4 | 50,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T4_momo_wallet_txns.csv | data/full/telecom/T4_momo_wallet_txns/part_00000.parquet to part_00019.parquet |
| T5 | 2,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T5_wallets.csv | data/full/telecom/T5_wallets/part_00000.parquet to part_00000.parquet |
| T6 | 5,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T6_agents.csv | data/full/telecom/T6_agents/part_00000.parquet to part_00001.parquet |
| T7 | 30,000 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T7_topups_billing.csv | data/full/telecom/T7_topups_billing/part_00000.parquet to part_00011.parquet |
| T8 | 125 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T8_interconnect_traffic.csv | data/full/telecom/T8_interconnect_traffic/part_00000.parquet to part_00000.parquet |
| T9 | 500 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T9_cell_sites_and_roaming.csv | data/full/telecom/T9_cell_sites_and_roaming/part_00000.parquet to part_00000.parquet |
| T10 | 37 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T10_complaints_and_cases.csv | data/full/telecom/T10_complaints_and_cases/part_00000.parquet to part_00000.parquet |
| T11 | 250 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T11_alerts_and_rules.csv | data/full/telecom/T11_alerts_and_rules/part_00000.parquet to part_00000.parquet |
| T12 | 2 | https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/data/sample/telecom/T12_reference_parameters.csv | data/full/telecom/T12_reference_parameters/part_00000.parquet to part_00000.parquet |

### Part files and manifest

Parts are named part_00000.parquet, part_00001.parquet and so on, in data/full/<domain>/<dataset_name>/. Each part is Parquet with zstd compression and at most 94,371,840 bytes. The manifest is JSON with this shape (B1 shown, cut after two parts):

```json
{
 "label": "SYNTHETIC data, Klaus Konsults",
 "format": "parquet",
 "compression": "zstd level 9",
 "max_part_bytes": 94371840,
 "datasets": {
  "B1_transactions": {
   "domain": "banking",
   "rows": 20000000,
   "parts": [
    {
     "path": "banking/B1_transactions/part_00000.parquet",
     "rows": 1000000,
     "bytes": 28952076,
     "sha256": "e89ea180c41d727370f0808a7effc015cf7c001b4fb00088af70e43ad9d8187d"
    },
    {
     "path": "banking/B1_transactions/part_00001.parquet",
     "rows": 1000000,
     "bytes": 28983247,
     "sha256": "6a1b90a632a2178e8d4a4c54146a26846ca1a0a94854cb6e0dd48ef0fb92c434"
    },
    "... 18 more parts"
   ]
  }
 }
}
```

For each part check that the part's row count matches parts[].rows, and if you can, that its SHA 256 matches parts[].sha256. The dataset rows value is the sum of its parts.

## Table schemas (B1 to B14, T1 to T12)

Types are the Parquet types in the full parts. Every table has two extra columns: synthetic_scenario (the planted scenario name, empty for normal rows) and synthetic (always true). Keys marked "not checked" are natural keys the Python code does not test for uniqueness. Example values come from the first row of each sample CSV.

### B1 B1_transactions

Domain banking. Key: txn_id. Full rows 20,000,000 in 20 part(s). Sample rows 50,000.

| column | type | example (first sample row) |
|---|---|---|
| txn_id | string | BT000000000 |
| account_id | string | BA000000491 |
| timestamp | datetime (ms, no time zone) | 2025-01-22T23:21:46Z |
| amount | double | 9.94 |
| currency | string | GHS |
| channel | string | card |
| merchant_id | string | BM000029080 |
| mcc | int64 | 5732 |
| counterparty_account | string | BA000001382 |
| terminal_id | string | BTM000012041 |
| country | string | TG |
| response_code | string | 00 |
| direction | string | debit |
| balance_before | double | 2709.19 |
| balance_after | double | 2699.25 |
| reversal_flag | int64 | 0 |
| original_txn_id | string | (empty) |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B2 B2_accounts

Domain banking. Key: account_id. Full rows 750,000 in 1 part(s). Sample rows 1,875.

| column | type | example (first sample row) |
|---|---|---|
| account_id | string | BA000000000 |
| person_id | string | BP000000930 |
| open_date | datetime (ms, no time zone) | 2016-06-07T00:00:00Z |
| status | string | active |
| type | string | current |
| kyc_level | string | tier3 |
| expected_monthly_volume | double | 3437.76 |
| branch | string | BR003 |
| status_change_date | datetime (ms, no time zone) | 2025-05-21T08:24:54Z |
| kyc_change_date | datetime (ms, no time zone) | 2025-09-11T04:29:29Z |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B3 B3_persons

Domain banking. Key: person_id. Full rows 500,000 in 1 part(s). Sample rows 1,250.

| column | type | example (first sample row) |
|---|---|---|
| person_id | string | BP000000000 |
| name_hash | string | SYNNAME000000000 |
| national_id_hash | string | SYNNID000000000 |
| dob | datetime (ms, no time zone) | 1988-06-10T00:00:00Z |
| region | string | R03 |
| occupation | string | trader |
| income_band | string | middle |
| phone | string | SYNPHONE000000000 |
| email_hash | string | SYNMAIL000000000 |
| address_hash | string | SYNADDR000000000 |
| address_change_date | datetime (ms, no time zone) | 2025-09-07T10:55:39Z |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B4 B4_auth_events

Domain banking. Key: event_id. Full rows 10,000,000 in 10 part(s). Sample rows 25,000.

| column | type | example (first sample row) |
|---|---|---|
| event_id | string | BE000000000 |
| person_id | string | BP000000289 |
| device_id | string | BD000000670 |
| ip | string | SYNIP011810481 |
| geo | string | CI |
| event_type | string | login |
| timestamp | datetime (ms, no time zone) | 2025-09-24T15:57:19Z |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B5 B5_devices

Domain banking. Key: device_id. Full rows 800,000 in 1 part(s). Sample rows 2,000.

| column | type | example (first sample row) |
|---|---|---|
| device_id | string | BD000000000 |
| imei_or_fingerprint | string | SYNFP000000000 |
| first_seen | datetime (ms, no time zone) | 2025-05-01T02:02:34Z |
| last_seen | datetime (ms, no time zone) | 2025-11-23T04:04:01Z |
| person_id | string | BP000000461 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B6 B6_beneficiaries

Domain banking. Key: account_id + payee_account (not checked). Full rows 1,500,000 in 1 part(s). Sample rows 3,750.

| column | type | example (first sample row) |
|---|---|---|
| account_id | string | BA000000390 |
| payee_account | string | BA000001839 |
| added_at | datetime (ms, no time zone) | 2025-01-01T14:15:30Z |
| added_via_device | string | BD000001391 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B7 B7_gl_journal

Domain banking. Key: line_id (je_id groups lines). Full rows 2,000,000 in 2 part(s). Sample rows 5,000.

| column | type | example (first sample row) |
|---|---|---|
| line_id | string | BL000000000 |
| je_id | string | BJ000000000 |
| posting_date | datetime (ms, no time zone) | 2025-02-01T00:00:00Z |
| entry_timestamp | datetime (ms, no time zone) | 2025-02-01T00:29:42Z |
| account_code | string | GL00073 |
| debit | double | 252.41 |
| credit | double | 0.0 |
| preparer_id | string | BU000000013 |
| approver_id | string | BU000000040 |
| is_manual | bool | False |
| description | string | settlement |
| document_type | string | FA |
| reversal_ind | bool | False |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B8 B8_users_access

Domain banking. Key: user_id (not checked). Full rows 20,000 in 1 part(s). Sample rows 50.

| column | type | example (first sample row) |
|---|---|---|
| user_id | string | BU000000000 |
| is_active | bool | True |
| role | string | teller |
| permission | string | read |
| last_login | datetime (ms, no time zone) | 2025-09-19T23:31:36Z |
| change_time | datetime (ms, no time zone) | 2025-12-14T20:59:11Z |
| changed_by | string | BU000000048 |
| change_type | string | grant |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B9 B9_cards_and_authorisations

Domain banking. Key: auth_id. Full rows 6,000,000 in 6 part(s). Sample rows 15,000.

| column | type | example (first sample row) |
|---|---|---|
| card_id | string | BC000001356 |
| account_id | string | BA000001356 |
| card_status | string | active |
| issue_date | datetime (ms, no time zone) | 2024-01-06T00:00:00Z |
| auth_id | string | BZ000000000 |
| auth_time | datetime (ms, no time zone) | 2025-07-18T22:42:13Z |
| amount | double | 24.04 |
| response_code | string | 05 |
| terminal_id | string | BTM000005819 |
| terminal_type | string | pos |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B10 B10_vendors_and_payments

Domain banking. Key: payment_id. Full rows 100,000 in 1 part(s). Sample rows 250.

| column | type | example (first sample row) |
|---|---|---|
| vendor_id | string | BV000000010 |
| vendor_name | string | SYNVENDOR000000010 |
| vendor_bank_account | string | BEBANK000000002 |
| vendor_address | string | SYNADDR000000010 |
| created_by | string | BU000000005 |
| created_at | datetime (ms, no time zone) | 2023-01-16T00:00:00Z |
| payment_id | string | BPAY000000000 |
| payment_date | datetime (ms, no time zone) | 2025-05-14T08:49:58Z |
| payment_amount | double | 1585.28 |
| payment_approver_id | string | BU000000033 |
| synthetic_scenario | string | ghost_vendor_or_employee |
| synthetic | bool | True |

### B11 B11_payroll_and_hr

Domain banking. Key: employee_id + pay_run_id (not checked). Full rows 72,000 in 1 part(s). Sample rows 180.

| column | type | example (first sample row) |
|---|---|---|
| employee_id | string | BEMP000000000 |
| employee_bank_account | string | BEBANK000000000 |
| hire_date | datetime (ms, no time zone) | 2017-10-01T00:00:00Z |
| exit_date | datetime (ms, no time zone) | (empty) |
| department | string | sales |
| pay_run_id | string | BRUN000000000 |
| pay_date | datetime (ms, no time zone) | 2025-01-26T00:00:00Z |
| pay_amount | double | 2265.69 |
| attendance_days | int64 | 20 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B12 B12_fraud_cases

Domain banking. Key: case_id (not checked). Full rows 20,000 in 1 part(s). Sample rows 50.

| column | type | example (first sample row) |
|---|---|---|
| case_id | string | BCASE000000000 |
| entity_id | string | BA000001615 |
| entity_type | string | account |
| scenario | string | duplicate_vendor_payments |
| loss_amount | double | 920.01 |
| reported_date | datetime (ms, no time zone) | 2025-12-21T03:46:21Z |
| confirmed_date | datetime (ms, no time zone) | 2026-01-01T02:24:44Z |
| outcome | string | confirmed |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B13 B13_existing_alerts

Domain banking. Key: alert_id (not checked). Full rows 200,000 in 1 part(s). Sample rows 500.

| column | type | example (first sample row) |
|---|---|---|
| alert_id | string | BAL000000000 |
| rule_or_model | string | legacy_country |
| score | double | 0.8645 |
| entity_id | string | BA000000698 |
| alert_date | datetime (ms, no time zone) | 2025-08-29T15:46:17Z |
| analyst_id | string | BU000000008 |
| disposition | string | false_positive |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### B14 B14_reference_parameters

Domain banking. Key: reference_type + code (not checked). Full rows 2,000 in 1 part(s). Sample rows 5.

| column | type | example (first sample row) |
|---|---|---|
| reference_type | string | mcc |
| code | string | REF000000000 |
| description | string | synthetic reference row |
| limit_value | double | (empty) |
| threshold_value | double | (empty) |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T1 T1_cdrs

Domain telecom. Key: cdr_id. Full rows 20,000,000 in 20 part(s). Sample rows 50,000.

| column | type | example (first sample row) |
|---|---|---|
| cdr_id | string | TC000000000 |
| caller | string | TM000000987 |
| callee | string | TM000000608 |
| start_time | datetime (ms, no time zone) | 2025-07-24T07:01:11Z |
| duration_sec | int64 | 87 |
| call_type | string | data |
| cell_id | string | TCELL000000015 |
| route | string | TR000000026 |
| imsi | string | TIMSI000000987 |
| imei | string | TIMEI050485709 |
| charge | double | 0.174 |
| roaming_flag | bool | False |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T2 T2_subscribers

Domain telecom. Key: msisdn. Full rows 1,000,000 in 1 part(s). Sample rows 2,500.

| column | type | example (first sample row) |
|---|---|---|
| msisdn | string | TM000000000 |
| person_id | string | TP000000000 |
| activation_date | datetime (ms, no time zone) | 2024-12-18T13:44:48Z |
| plan | string | prepaid |
| kyc_status | string | verified |
| id_number_hash | string | SYNTID000001961 |
| credit_limit | double | 0.0 |
| registration_channel | string | online |
| registration_shop_id | string | TSHOP000000200 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T3 T3_sims_and_sim_swap_events

Domain telecom. Key: swap_id. Full rows 1,100,000 in 1 part(s). Sample rows 2,750.

| column | type | example (first sample row) |
|---|---|---|
| swap_id | string | TSW000000000 |
| sim_id | string | TSIM000004630 |
| msisdn | string | TM000000326 |
| swap_time | datetime (ms, no time zone) | 2025-05-31T10:19:02Z |
| old_imei | string | TIMEI059860489 |
| new_imei | string | TIMEI002165576 |
| channel | string | call_centre |
| performed_by_user | string | TU000001916 |
| shop_id | string | TSHOP000000181 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T4 T4_momo_wallet_txns

Domain telecom. Key: txn_id. Full rows 20,000,000 in 20 part(s). Sample rows 50,000.

| column | type | example (first sample row) |
|---|---|---|
| txn_id | string | TT000000000 |
| wallet_id | string | TW000001521 |
| timestamp | datetime (ms, no time zone) | 2025-12-16T10:16:34Z |
| type | string | cash_in |
| amount | double | 13.86 |
| counterparty | string | TW000000599 |
| agent_id | string | TAG000000007 |
| balance_before | double | 183.8 |
| balance_after | double | 197.66 |
| status | string | success |
| reversal_of | string | (empty) |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T5 T5_wallets

Domain telecom. Key: wallet_id. Full rows 800,000 in 1 part(s). Sample rows 2,000.

| column | type | example (first sample row) |
|---|---|---|
| wallet_id | string | TW000000000 |
| msisdn | string | TM000002274 |
| person_id | string | TP000002274 |
| opened_at | datetime (ms, no time zone) | 2021-09-07T00:00:00Z |
| status | string | active |
| kyc_tier | string | tier1 |
| wallet_limit | double | 2000.0 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T6 T6_agents

Domain telecom. Key: agent_id + movement_time (not checked). Full rows 2,000,000 in 2 part(s). Sample rows 5,000.

| column | type | example (first sample row) |
|---|---|---|
| agent_id | string | TAG000000010 |
| region | string | R02 |
| onboarded_at | datetime (ms, no time zone) | 2021-02-21T00:00:00Z |
| commission_rate | double | 0.01 |
| status | string | active |
| movement_time | datetime (ms, no time zone) | 2025-10-11T00:28:06Z |
| movement_type | string | withdraw |
| float_amount | double | 1241.87 |
| payout_date | datetime (ms, no time zone) | 2025-11-10T00:00:00Z |
| commission_amount | double | 12.42 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T7 T7_topups_billing

Domain telecom. Key: msisdn + event_time (not checked). Full rows 12,000,000 in 12 part(s). Sample rows 30,000.

| column | type | example (first sample row) |
|---|---|---|
| msisdn | string | TM000001657 |
| event_time | datetime (ms, no time zone) | 2025-11-06T05:28:09Z |
| event_type | string | topup |
| amount | double | 1.0 |
| channel | string | ussd |
| invoice_status | string | (empty) |
| collections_amount | double | 0.0 |
| bad_debt_amount | double | 0.0 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T8 T8_interconnect_traffic

Domain telecom. Key: traffic_date + route (not checked). Full rows 50,000 in 1 part(s). Sample rows 125.

| column | type | example (first sample row) |
|---|---|---|
| traffic_date | datetime (ms, no time zone) | 2025-09-17T00:00:00Z |
| route | string | TR000000028 |
| carrier | string | TCARRIER000000004 |
| minutes | double | 15322.7 |
| settlement_amount | double | 153.23 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T9 T9_cell_sites_and_roaming

Domain telecom. Key: cell_id + roaming_record_id (not checked). Full rows 200,000 in 1 part(s). Sample rows 500.

| column | type | example (first sample row) |
|---|---|---|
| cell_id | string | TCELL000000000 |
| location | string | TLOC000000000 |
| roaming_record_id | string | TRR000000000 |
| msisdn | string | TM000000129 |
| roaming_country | string | CI |
| roaming_start_time | datetime (ms, no time zone) | 2025-08-24T23:19:56Z |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T10 T10_complaints_and_cases

Domain telecom. Key: case_id (not checked). Full rows 15,000 in 1 part(s). Sample rows 37.

| column | type | example (first sample row) |
|---|---|---|
| case_id | string | TCASE000000000 |
| msisdn | string | TM000000437 |
| scenario | string | agent_float_anomalies |
| case_date | datetime (ms, no time zone) | 2025-10-23T14:45:08Z |
| outcome | string | confirmed |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T11 T11_alerts_and_rules

Domain telecom. Key: alert_id (not checked). Full rows 100,000 in 1 part(s). Sample rows 250.

| column | type | example (first sample row) |
|---|---|---|
| alert_id | string | TAL000000000 |
| rule_or_model | string | legacy_rule |
| score | double | 0.0586 |
| entity_id | string | TM000001168 |
| alert_date | datetime (ms, no time zone) | 2025-09-30T08:03:15Z |
| analyst_id | string | TU000000120 |
| disposition | string | closed |
| rule_id | string | TRULE000000004 |
| rule_definition | string | synthetic legacy rule |
| rule_threshold | double | 50.0 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

### T12 T12_reference_parameters

Domain telecom. Key: reference_type + code (not checked). Full rows 1,000 in 1 part(s). Sample rows 2.

| column | type | example (first sample row) |
|---|---|---|
| reference_type | string | route |
| code | string | TREF000000000 |
| description | string | synthetic reference row |
| value | double | 0.20736104507761732 |
| synthetic_scenario | string | (empty) |
| synthetic | bool | True |

## The six stages and 22 steps

These follow docs/pipeline_steps.md. The Python code writes some dq rows with its own step numbers (see the data quality section); copy the code's numbers so the outputs match.

| Stage | Steps | Python module |
|---|---|---|
| 1 Load and control totals | 1 chain of custody, 2 load, 3 control totals per month, 4 compare with client totals | python/pipeline/load.py |
| 2 Data quality | 5 journal debits equal credits, 6 tie outs, 7 no gaps, 8 unique keys and orphans, 9 timestamps, 10 amounts and reversals, 11 null rates, 12 limitations | python/pipeline/dq.py |
| 3 Features | 13 features within one domain | python/pipeline/features.py |
| 4 Rules | 14 scenario rules | python/pipeline/rules.py |
| 5 Model | 15 time splits, 16 train, score and evaluate | python/pipeline/model.py |
| 6 Output | 17 coverage gaps, 18 threshold sensitivity, 19 drift, 20 agreement, 21 chart inputs, 22 write results | python/pipeline/output.py and run.py |

Not every planned step is in the Python code yet. Implemented today: control totals, duplicate keys, null cells, time range and monthly counts, negative amounts and balance continuity. Not implemented in Python yet: journal debits equal credits per entry (step 5), tie outs to GL and trust accounts (6), missing day detection (7), orphan keys (8), reversal links (10) and agreement rows (20). Build those only after Python has them, so the outputs stay comparable, or mark them as alteryx only.

## Data quality checks, exactly as python/pipeline/dq.py

Run for every loaded dataset. Counters are summed chunk by chunk, so the result is the same as one pass over the whole table. Each check writes one dq row (record_type dq) with domain, dataset_id, step, check_name, expected, observed, passed, note. The step numbers below are the ones the Python code writes today; they do not yet follow the 22 step numbering in docs/pipeline_steps.md, so copy them as is to match Python.

| step written | check_name | applies to | logic |
|---|---|---|---|
| 1 | row_count_control_total | all | observed = rows loaded (summed over chunks). Full data: expected = rows in data/full/manifest.json, note "expected from data/full/manifest.json". Sample: expected = observed, note "SYNTHETIC; no manifest, count recorded" |
| 1 | sum_<col>_control_total | tables with an amount column: B1 amount, B7 debit, B9 amount, B10 payment_amount, B11 pay_amount, T1 duration_sec, T4 amount, T6 float_amount, T7 amount, T8 minutes | observed = sum rounded to 2 decimals; expected empty; passed true; note "recorded; no source system control total exists for SYNTHETIC data" |
| 3 | duplicate_<key> | B1 txn_id, B2 account_id, B3 person_id, B4 event_id, B7 line_id, B9 auth_id, B10 payment_id, T1 cdr_id, T2 msisdn, T3 swap_id, T4 txn_id, T5 wallet_id | count of repeated key values; expected 0 |
| 3 | null_cells | all | count of empty cells, ignoring synthetic_scenario, original_txn_id, reversal_of, exit_date, invoice_status, limit_value, threshold_value; expected 0; note "optional columns excluded" |
| 4 | <time>_range | B1 timestamp, B4 timestamp, B7 entry_timestamp, T1 start_time, T3 swap_time, T4 timestamp, T6 movement_time, T7 event_time | expected text "2025-01-01 to 2026-01-31"; observed "min to max"; pass when min >= 2024-12-31 and max <= 2026-02-01; note "timezone UTC ASSUMPTION" |
| 4 | monthly_row_count | same tables | one row per month (YYYY-MM in month) with observed = rows; expected empty; passed true |
| 3 | negative_amount | tables with a column named amount | count of amount < 0; expected 0 |
| 5 | balance_continuity | tables with balance_before, balance_after and amount (B1, T4) | count of rows where abs(abs(balance_after minus balance_before) rounded to 2, minus amount rounded to 2) > 0.02; expected 0 |

On the sample the row count check compares the data with itself and the amount sum is only recorded, so both always pass. On client data the expected values come from the client's own totals (pack section 4).

## Features (step 13), exactly as python/pipeline/features.py

Features are built for B1 (with B2) and for T4 (with T5 and T3) only. Sort by entity then time before every window calculation.

Shared entity window, run on B1 with entity account_id, time timestamp, amount amount, and on T4 with entity wallet_id, time timestamp, amount amount:

| feature | how it is computed |
|---|---|
| secs_since_prev | seconds since the previous row of the same entity; 10,000,000 when there is none; capped at 10,000,000 |
| secs_to_next | seconds until the next row of the same entity; 10,000,000 when there is none; capped at 10,000,000 |
| day | time floored to the day |
| ent_day_count | rows for the entity on that day |
| ent_day_sum | sum of amount for the entity on that day |
| amount_z | (amount minus entity mean amount) divided by (entity standard deviation plus 1); standard deviation of a single row entity is 0 |
| ent_count | rows for the entity over the whole period |

Banking only (B1 joined to B2 on account_id):

| feature | how it is computed |
|---|---|
| hour, weekday | hour 0 to 23; weekday 0 is Monday, 6 is Sunday |
| log_amount | natural log of (1 plus amount) |
| near_threshold | 1 when 9,000 <= amount < 10,000 |
| declined | 1 when response_code is not "00" |
| is_debit | 1 when direction is "debit" |
| foreign | 1 when country is not "GH" |
| country_change_fast | 1 when country differs from the previous row of the same account and secs_since_prev < 3,600 |
| lead_digit | first digit of amount for amounts >= 1, else 0 |
| merch_day_count | rows for the same merchant_id, account_id and day |
| acct_dormant | 1 when B2 status is "dormant" |
| amount_vs_expected | amount divided by B2 expected_monthly_volume (1,000 when missing) |
| channel_card, channel_mobile, channel_web, channel_branch, channel_atm | 1 when channel equals that value |

Telecom only (T4 joined to T5 on wallet_id, and to T3 through T5 msisdn):

| feature | how it is computed |
|---|---|
| hour, weekday, log_amount | as banking |
| wallet_limit | T5 wallet_limit |
| over_tier | 1 when amount > wallet_limit |
| wallet_dormant | 1 when T5 status is "dormant" |
| round_amount | 1 when amount is a multiple of 100 |
| has_reversal | 1 when reversal_of is not empty |
| agent_day_count | rows for the same agent_id and day across the whole T4 table (counted over all chunks) |
| hours_since_swap | hours from the latest T3 swap_time on the wallet's msisdn to the transaction; 100,000 when negative or no swap; capped at 100,000 |
| type_p2p, type_cash_in, type_cash_out, type_merchant, type_airtime | 1 when type equals that value |

Model feature lists. Banking: log_amount, hour, weekday, secs_since_prev, secs_to_next, ent_day_count, ent_day_sum, amount_z, ent_count, near_threshold, declined, is_debit, foreign, country_change_fast, lead_digit, merch_day_count, acct_dormant, amount_vs_expected, reversal_flag, channel_card, channel_mobile, channel_web, channel_branch, channel_atm. Telecom: log_amount, hour, weekday, secs_since_prev, secs_to_next, ent_day_count, ent_day_sum, amount_z, ent_count, wallet_limit, over_tier, wallet_dormant, round_amount, has_reversal, agent_day_count, hours_since_swap, type_p2p, type_cash_in, type_cash_out, type_merchant, type_airtime.

## Rules (step 14), exactly as python/pipeline/rules.py

Every threshold is an ASSUMPTION default from the code, not a client parameter. Each rule flags rows of one table. "Count per X" means over the whole loaded period unless a day is named.

| rule_id | scenario | table | entity (type) | time column | logic |
|---|---|---|---|---|---|
| R_B01 | card_testing | B1 | account_id (account) | timestamp | amount < 10 AND merch_day_count >= 10 AND channel = "card" |
| R_B02 | structuring | B1 | account_id | timestamp | near_threshold = 1 AND count of near_threshold rows for the account >= 3 |
| R_B03 | mule_network | B1 | account_id | timestamp | (direction = "credit" AND amount > 4,000 AND secs_to_next < 3,600) OR (direction = "debit" AND secs_since_prev < 3,600 AND ent_day_count >= 5) |
| R_B04 | dormant_account_wake_up | B1 | account_id | timestamp | acct_dormant = 1 AND amount > 5,000 |
| R_B05 | kyc_mismatch_expected_volume | B1 | account_id | timestamp | amount_vs_expected > 20 |
| R_B06 | impossible_travel | B1 | account_id | timestamp | country_change_fast = 1 |
| R_B07 | reversal_abuse | B1 | account_id | timestamp | reversal_flag = 1 AND sum of reversal_flag for the account >= 3 |
| R_B08 | account_takeover | B1 | account_id | timestamp | channel = "web" AND amount > 2,500 AND secs_since_prev < 1,800 |
| R_B09 | account_takeover | B4 | person_id (person) | timestamp | sort by person_id, timestamp. near = 1 when any of the 5 rows centred on this row (2 before, itself, 2 after, same person) has event_type "password_reset". fails = count of "login_failed" rows for the person over the whole period. Flag when near = 1 AND fails >= 2 AND geo is not "GH" |
| R_B10 | journal_abuse | B7 | preparer_id (user) | entry_timestamp | is_manual is true AND (debit + credit) is a multiple of 10,000 AND (debit + credit) > 0 AND (weekday of entry_timestamp is Saturday or Sunday OR hour < 5) |
| R_B11 | segregation_of_duties | B7 | preparer_id | entry_timestamp | preparer_id = approver_id |
| R_B12 | privileged_access_before_journals | B7 | preparer_id | entry_timestamp | preparer_id is in the list of B8 user_id where permission = "admin_gl" AND is_manual is true |
| R_B13 | ghost_vendor_or_employee | B10 | vendor_id (vendor) | payment_date | vendor_bank_account starts with "BEBANK" (synthetic marker only) |
| R_B14 | duplicate_vendor_payments | B10 | vendor_id | payment_date | sort by payment_date; flag every row whose (vendor_id, payment_amount) pair already appeared earlier |
| R_B15 | payroll_after_exit | B11 | employee_id (employee) | pay_date | exit_date not empty AND pay_date > exit_date AND pay_amount > 0 |
| R_B16 | benford_anomaly | B1 | account_id | timestamp | lead_digit is 7 or 8 AND 700 <= amount < 9,000 |
| R_T01 | sim_swap_fraud | T4 | wallet_id (wallet) | timestamp | hours_since_swap < 24 AND type = "cash_out" |
| R_T02 | wallet_tier_breach | T4 | wallet_id | timestamp | over_tier = 1 |
| R_T03 | dormant_wallet_drain | T4 | wallet_id | timestamp | wallet_dormant = 1 AND type = "cash_out" AND amount > 500 |
| R_T04 | agent_fraud | T4 | agent_id (agent) | timestamp | type = "cash_in" AND round_amount = 1 AND agent_day_count >= 8 |
| R_T05 | sim_box_and_bypass | T1 | caller (msisdn) | start_time | call_type = "voice" AND rows for the caller that day >= 20 AND duration_sec < 150 |
| R_T06 | wangiri | T1 | caller | start_time | duration_sec <= 3 AND count of such short calls for the caller over the period >= 10 |
| R_T07 | subscription_and_bust_out | T1 | caller | start_time | duration_sec >= 1,800 AND roaming_flag is true |
| R_T08 | interconnect_leakage | T8 joined to T1 | route (route), one row per route and day | traffic_date | see the route day test below |
| R_T09 | insider_sim_swap_or_access_abuse | T3 | performed_by_user (user) | swap_time | night = hour of swap_time < 5 (UTC). c = count of night swaps by the same user on the same calendar day. Flag night AND c >= 5 |
| R_T10 | imei_churn | T3 | msisdn (msisdn) | swap_time | sort by msisdn, swap_time. A row starts a run when the swap 3 rows later for the same msisdn is within 30 days of it. Flag every row that starts a run or is one of the 3 rows after a run start (same msisdn). In short: 4 or more swaps on one number within 30 days |
| R_T11 | recharge_fraud | T7 | msisdn | event_time | event_type = "topup" AND rows for the msisdn that day (any event_type) >= 8 |
| R_T12 | subscription_and_bust_out | T7 | msisdn | event_time | bad_debt_amount > 1,000 |
| R_T13 | agent_float_anomalies | T6 | agent_id | movement_time | hour of movement_time < 5 AND float_amount > 30,000 |

Route day test for R_T08 (changed in this round; it used to flag every T1 call on a leaky route): t1 = sum of T1 duration_sec per route and UTC calendar day of start_time, divided by 60. For each route and day in T8: settled = sum of T8 minutes, amount = sum of T8 settlement_amount, unsettled_minutes = t1 minus settled (t1 is 0 when T1 has no calls that day), unsettled_share = unsettled_minutes / t1 (0 when t1 is 0), settlement_rate = amount / settled. Flag the route day when unsettled_share >= 0.35 AND settlement_rate < 0.6 times the median settlement_rate over all T8 route days. Output one rule row per flagged route day: record_id = route + "_" + day, entity_id = route, event_timestamp = day at 00:00:00Z, amount = unsettled_minutes, true_scenario from the T8 synthetic_scenario. Route days with T1 traffic but no T8 row are counted in a metric row route_days_without_settlement_row, not flagged. The join is on route and day only, since T1 has no carrier.

Privileged user list for R_B12: all B8 user_id where permission = "admin_gl".

## Model (steps 15 and 16), as python/pipeline/model.py

1. Label: 1 when synthetic_scenario is not empty, else 0. On client data the label comes from B12 or T10.
2. Split on the event time: before 2025-10-01 is train, 2025-10-01 up to before 2025-11-01 is validation, from 2025-11-01 is test.
3. Python uses XGBoost, trained on a stratified sample when the training split is large (all positives kept, negatives sampled so training stays at or under 2,000,000 rows; on the sample no sampling happens). Settings: (300 trees, depth 6, learning rate 0.1, subsample 0.8, column sample 0.8, positive class weight = negatives divided by positives in train, early stopping 30 rounds on validation PR AUC, seed 42). This build uses the tool's own learner instead (see the step table), so scores will differ from Python by design.
4. Threshold: the 99th percentile of validation scores (an ASSUMPTION 1% alert budget). predicted_label = 1 when score >= threshold.
5. Metrics per split (train, validation, test): rows, positives, alert_rate, and when both classes exist pr_auc, roc_auc, precision, recall. Also test recall per planted scenario.
6. Threshold sweep: on the test split, threshold times (1 + p/100) for p in minus 20, minus 10, 0, 10, 20; record alert_count and detected_count.
7. Drift: score bands 0.0 to 0.1 up to 0.9 to 1.0, share of rows per band per month, over all splits.
8. Score rows are written for the test split only.

## Step 6 extras, as python/pipeline/run.py

1. Rule metrics per rule: planted_rows (rows whose synthetic_scenario equals the rule's scenario), alerts, detected (alerts that are planted rows of that scenario), recall = detected / planted_rows, precision = detected / alerts, with model = "rule", split = "all".
2. Coverage: one row per scenario in python/synthetic/config.yaml, covered = true when any rule has that scenario, note "rule present" or "no rule yet".
3. Benford: first digit counts for B1 amount, B7 debit and T4 amount (values >= 1 only), digits 1 to 9, expected_share = log10(1 + 1/d).
4. Edges, banking: B1 rows where synthetic_scenario = "mule_network" OR (direction = "debit" AND amount > 5,000); keep debits; group by account_id and counterparty_account; edge_weight = sum of amount, edge_count = rows; entity_type "account".
5. Edges, telecom: T4 rows with agent_day_count >= 8; group by agent_id and wallet_id; entity_type "agent".
6. Geo: T1 minutes (duration_sec / 60) per route and day, joined (outer) to T8 minutes per route and traffic_date; the day goes in month; note "latitude and longitude not available, see docs/open_questions.md".
7. Run rows: runtime_seconds and peak_memory_mb per stage (load, data_quality, features, rules, model, output) and a total row.
8. Agreement rows are not written by Python yet. When this build exists, compare its predicted labels with Python's on the same record_id.

## Build steps in Alteryx (UNTESTED DESIGN)

Build one workflow, fraud_pipeline.yxmd, with six Tool Containers named "1 Load and control totals" to "6 Output". Run it twice, with a Workflow constant DOMAIN set to banking, then telecom (or build two copies). Use the AMP engine for full data. Store paths in Workflow constants: SOURCE (sample_url or local_full), REPO_DIR (the local clone).

### Macros to build first

1. **KK_ReadDataset.yxmc (batch macro).** Control parameter: one row per part. In sample mode the only row is the dataset's raw_url, read with Download (Output: To a Field, String, Encoding UTF 8) then Text To Columns on newline, then Text To Columns on comma (or save to a temp file and read with Input Data as CSV, First Row Contains Field Names, Field Length 254). In local_full mode the rows come from manifest.json: REPO_DIR\data\full\ plus parts.path, read with Input Data (File Format Parquet). Inside the macro, Record ID plus Summarize Count checks the part's rows against manifest rows; a Message tool stops on mismatch. Output is the union of all parts.
2. **KK_ControlTotals.yxmc.** Summarize: Count rows, Sum of the amount column for the dataset (see the data quality table). Output one row per check.
3. **KK_DQChecks.yxmc.** Implements every row of the data quality table: Unique (duplicates output, then Count), Formula IsNull counts per column with a Transpose and Summarize for null_cells, Summarize Min and Max on the time column, Formula DateTimeFormat([time],"%Y-%m") plus Summarize Count for monthly_row_count, Filter amount < 0 plus Count, Formula for balance_continuity. Output in the dq columns.
4. **KK_Rule_<rule_id>.yxmc.** One per rule in the rules table. Input: the table with features. Output: the flagged rows plus Formula fields rule_id, scenario, model = "rule", score = 1.0, threshold = 1.0, predicted_label = 1.
5. **KK_ToResults.yxmc.** Select with all 56 shared columns in order (Unknown fields off), adds run_id, created_at (DateTimeNow in UTC, format %Y-%m-%dT%H:%M:%SZ) and stack = "alteryx".

### Container 1: Load and control totals (steps 1 to 4)

1. Input Data on config\sources.csv; Filter domain = DOMAIN.
2. Formula: SHA 256 of each input is not built into Alteryx; record the manifest sha256 for each part as chain of custody (step 1). In sample mode record the raw URL and the time of the download.
3. Local full mode: Input Data on data\full\manifest.json (JSON), JSON Parse, Text To Columns to get dataset, path, rows, sha256 per part; Filter to the dataset; feed KK_ReadDataset.
4. Sample mode: feed raw_url to KK_ReadDataset.
5. Select: set types as in the schemas section (string, Double, Int64, Bool, DateTime). Parse timestamps with DateTime tool, custom format %Y-%m-%dT%H:%M:%SZ, and drop the Z (no time zone).
6. KK_ControlTotals per dataset. Wildcard option: Input Data with path data\full\banking\B1_transactions\part_*.parquet reads all parts at once without the per part check.

### Container 2: Data quality (steps 5 to 12)

KK_DQChecks per dataset, Union, KK_ToResults.

### Container 3: Features (step 13)

1. Sort by entity then time.
2. Multi Row Formula (group by entity): secs_since_prev = IF IsNull([Row-1:time]) THEN 10000000 ELSE Min(DateTimeDiff([time],[Row-1:time],"seconds"),10000000) ENDIF; secs_to_next likewise with Row+1.
3. Formula day = DateTimeTrim([time],"day"). Summarize by entity and day (Count, Sum) and Join back for ent_day_count and ent_day_sum. Summarize by entity (Avg, StdDev, Count) and Join back for amount_z and ent_count (treat a null StdDev as 0).
4. Formula for every other feature in the features tables. Join B2 (banking) or T5 (telecom) on the key with a Left outer join (Join plus Union of the left unmatched output). For hours_since_swap, Summarize T3 Max swap_time by msisdn and join through T5 msisdn.

### Container 4: Rules (step 14)

One KK_Rule macro per rule for the domain. Count per entity rules use Summarize then Join back. R_B09 uses Multi Row Formula with Row-2 to Row+2 inside the person group. R_T09 uses Summarize count of night swaps by performed_by_user and day, joined back. R_T10 uses Multi Row Formula with Row+3 inside each msisdn to test the 30 day window, then marks the 3 following rows. Union the outputs. Rule metrics: Summarize per rule on the flagged rows and on all rows where synthetic_scenario equals the scenario.

### Container 5: Model (steps 15 and 16)

1. Formula split = IF [time] < "2025-10-01" THEN "train" ELSEIF [time] < "2025-11-01" THEN "validation" ELSE "test" ENDIF; label = IIF([synthetic_scenario] != "",1,0).
2. Filter train. Boosted Model (target label, the model feature list, Bernoulli loss for a binary target, sampling weights off). Forest Model is an accepted alternative.
3. Score on all rows. Threshold: Summarize Percentile 99 of score on validation, Append Fields, Formula predicted_label = IIF([score] >= [threshold],1,0).
4. Summarize metrics per split. Formula for the five threshold changes. Tile or Formula for score bands, Summarize by month for drift.

### Container 6: Output (steps 17 to 22)

Coverage from Text Input of the scenario list joined to the rule list; Benford with Formula first digit and Summarize; edges and geo with Summarize and Join as in the Step 6 extras section; agreement by Join on record_id to the Python score rows read from outputs/sample/results_latest.csv; KK_ToResults; Union; Output Data to outputs\alteryx\results_<run_id>.csv (and .parquet if wanted). Add run rows from the workflow log times if available, else leave peak_memory_mb empty.


## Output the build must write

Write outputs/alteryx/results_<run_id>.csv with stack = "alteryx", in long format, with exactly the 56 columns below in this order. Leave columns that do not apply to a row empty. record_id must be the input row's id (txn_id for B1 and T4) so agreement can be checked against Python.


Every stack (Alteryx, KNIME, Python) writes one shared results file per run, outputs/<stack>/results_<run_id>.parquet (CSV option). All 12 charts in docs/charts.md, in Python and later in Power BI, read only these files. The file is in long format: a record_type column says what each row holds, and columns that do not apply to a row are left empty.

## record_type values

1. score: one row per scored record per model.
2. metric: one row per metric per model and split.
3. dq: one row per data quality or reconciliation check.
4. coverage: one row per scenario and rule for the rule coverage gap check.
5. threshold: one row per rule or model per threshold change.
6. drift: one row per model, month and score band.
7. agreement: one row per pair of tools per model and scenario.
8. edge: one row per link in the mule or agent network.
9. benford: one row per first digit per dataset.
10. geo: one row per route or cell per day.
11. run: one row per run with runtime and memory.

## Columns

| column | type | used by | meaning |
|---|---|---|---|
| record_type | string | all | one of the values above |
| run_id | string | all | unique id of the run |
| created_at | string | all | ISO 8601 timestamp of the run |
| stack | string | all | alteryx, knime or python |
| domain | string | all | banking or telecom |
| dataset_id | string | dq, benford, geo | for example B1 or T8 |
| scenario | string | score, metric, coverage, threshold, agreement | scenario name from docs/scenario_coverage.md, or all |
| model | string | score, metric, threshold, drift, agreement | for example xgboost, rule, or the built in learner name |
| rule_id | string | score, coverage, threshold | rule identifier, if a rule fired |
| split | string | score, metric | train, validation or test |
| record_id | string | score | id of the input row, identical across stacks |
| entity_id | string | score, edge | account, wallet, agent, msisdn, user, vendor or employee id |
| entity_type | string | score, edge | type of entity_id |
| event_timestamp | string | score | ISO 8601 time of the event, for alert trends and hour by weekday heat maps |
| month | string | score, dq, drift | YYYY MM month of the row |
| score | float | score | fraud score between 0 and 1 |
| threshold | float | score, threshold | threshold applied |
| predicted_label | int | score | 1 for alert, 0 for no alert |
| true_label | int | score | 1 for fraud, 0 for not fraud |
| true_scenario | string | score | planted scenario label, empty when not fraud |
| amount | float | score | amount of the event, for KPI and leaderboard totals |
| currency | string | score | currency of amount |
| metric | string | metric | for example pr_auc, recall_at_alert_rate, expected_cost |
| value | float | metric, drift, agreement | metric value, drift statistic or agreement rate |
| alert_rate | float | metric | alert rate used, if relevant |
| train_rows | int | metric | rows used for training |
| sample_method | string | metric | none, stratified or other |
| step | int | dq | step number from docs/pipeline_steps.md |
| check_name | string | dq | short name of the check |
| expected | string | dq | expected value, for example a control total |
| observed | string | dq | observed value |
| passed | bool | dq | whether the check passed |
| note | string | dq, coverage | explanation or limitation |
| covered | bool | coverage | whether the scenario has at least one rule or model |
| threshold_change_pct | float | threshold | minus 20, minus 10, 0, plus 10 or plus 20 |
| alert_count | int | threshold | alerts at that threshold |
| detected_count | int | threshold | planted cases detected at that threshold |
| score_band | string | drift | score range, for example 0.0 to 0.1 |
| band_share | float | drift | share of records in the band that month |
| compare_stack | string | agreement | the other tool in the pair |
| source_id | string | edge | sending entity |
| target_id | string | edge | receiving entity |
| edge_weight | float | edge | total amount or count on the link |
| edge_count | int | edge | number of transactions on the link |
| first_digit | int | benford | leading digit 1 to 9 |
| observed_count | int | benford | count of amounts with that digit |
| expected_share | float | benford | Benford expected share for that digit |
| route | string | geo | T1 or T8 route |
| cell_id | string | geo | T1 or T9 cell id |
| latitude | float | geo | cell latitude (open question, see docs/open_questions.md) |
| longitude | float | geo | cell longitude (open question) |
| geo_minutes | float | geo | minutes on the route or cell that day |
| geo_settled_minutes | float | geo | settled minutes from T8, if any |
| runtime_seconds | float | run, metric | measured runtime |
| peak_memory_mb | float | run, metric | measured peak memory, if available |
| stage | string | run | stage name from docs/pipeline_steps.md |


## Acceptance checks on the sample

Expected values come from the sample pipeline rerun at commit a689b4b (run_id python_sample_recheck). They will differ from the older committed outputs/sample file until that file is regenerated. That file holds these rows per record_type: score 22,971, geo 14,139, edge 1,201, drift 216, metric 215, dq 184, coverage 27, benford 27, threshold 10, run 7.

### Control totals and data quality

Every check in that run passed. Sample row counts are compared with themselves (no manifest for the sample) and amount sums are recorded only. A Alteryx build on the same sample must reproduce these values exactly.

| dataset | check | expected | observed |
|---|---|---|---|
| B1 | row_count_control_total | 50000 | 50000 |
| B1 | sum_amount_control_total | nan | 16332191.53 |
| B1 | duplicate_txn_id | 0 | 0 |
| B1 | null_cells | 0 | 0 |
| B1 | timestamp_range | 2025-01-01 to 2026-01-31 | 2025-01-01 00:01:01 to 2025-12-31 23:38:32 |
| B1 | negative_amount | 0 | 0 |
| B1 | balance_continuity | 0 | 0 |
| B2 | row_count_control_total | 1875 | 1875 |
| B2 | duplicate_account_id | 0 | 0 |
| B2 | null_cells | 0 | 0 |
| B3 | row_count_control_total | 1250 | 1250 |
| B3 | duplicate_person_id | 0 | 0 |
| B3 | null_cells | 0 | 0 |
| B4 | row_count_control_total | 25000 | 25000 |
| B4 | duplicate_event_id | 0 | 0 |
| B4 | null_cells | 0 | 0 |
| B4 | timestamp_range | 2025-01-01 to 2026-01-31 | 2025-01-01 01:24:30 to 2025-12-31 23:51:49 |
| B5 | row_count_control_total | 2000 | 2000 |
| B5 | null_cells | 0 | 0 |
| B6 | row_count_control_total | 3750 | 3750 |
| B6 | null_cells | 0 | 0 |
| B7 | row_count_control_total | 5000 | 5000 |
| B7 | sum_debit_control_total | nan | 8812072.12 |
| B7 | duplicate_line_id | 0 | 0 |
| B7 | null_cells | 0 | 0 |
| B7 | entry_timestamp_range | 2025-01-01 to 2026-01-31 | 2025-01-01 01:47:18 to 2025-12-31 23:22:33 |
| B8 | row_count_control_total | 50 | 50 |
| B8 | null_cells | 0 | 0 |
| B9 | row_count_control_total | 15000 | 15000 |
| B9 | sum_amount_control_total | nan | 1643411.59 |
| B9 | duplicate_auth_id | 0 | 0 |
| B9 | null_cells | 0 | 0 |
| B9 | negative_amount | 0 | 0 |
| B10 | row_count_control_total | 250 | 250 |
| B10 | sum_payment_amount_control_total | nan | 1212170.81 |
| B10 | duplicate_payment_id | 0 | 0 |
| B10 | null_cells | 0 | 0 |
| B11 | row_count_control_total | 180 | 180 |
| B11 | sum_pay_amount_control_total | nan | 570823.8 |
| B11 | null_cells | 0 | 0 |
| B12 | row_count_control_total | 50 | 50 |
| B12 | null_cells | 0 | 0 |
| B13 | row_count_control_total | 500 | 500 |
| B13 | null_cells | 0 | 0 |
| B14 | row_count_control_total | 5 | 5 |
| B14 | null_cells | 0 | 0 |
| T1 | row_count_control_total | 50000 | 50000 |
| T1 | sum_duration_sec_control_total | nan | 6030418.0 |
| T1 | duplicate_cdr_id | 0 | 0 |
| T1 | null_cells | 0 | 0 |
| T1 | start_time_range | 2025-01-01 to 2026-01-31 | 2025-01-01 00:03:26 to 2025-12-31 23:58:24 |
| T2 | row_count_control_total | 2500 | 2500 |
| T2 | duplicate_msisdn | 0 | 0 |
| T2 | null_cells | 0 | 0 |
| T3 | row_count_control_total | 2750 | 2750 |
| T3 | duplicate_swap_id | 0 | 0 |
| T3 | null_cells | 0 | 0 |
| T3 | swap_time_range | 2025-01-01 to 2026-01-31 | 2025-01-01 07:08:28 to 2025-12-31 20:35:28 |
| T4 | row_count_control_total | 50000 | 50000 |
| T4 | sum_amount_control_total | nan | 4863627.29 |
| T4 | duplicate_txn_id | 0 | 0 |
| T4 | null_cells | 0 | 0 |
| T4 | timestamp_range | 2025-01-01 to 2026-01-31 | 2025-01-01 00:22:19 to 2025-12-31 23:25:26 |
| T4 | negative_amount | 0 | 0 |
| T4 | balance_continuity | 0 | 0 |
| T5 | row_count_control_total | 2000 | 2000 |
| T5 | duplicate_wallet_id | 0 | 0 |
| T5 | null_cells | 0 | 0 |
| T6 | row_count_control_total | 5000 | 5000 |
| T6 | sum_float_amount_control_total | nan | 9744348.85 |
| T6 | null_cells | 0 | 0 |
| T6 | movement_time_range | 2025-01-01 to 2026-01-31 | 2025-01-01 01:47:51 to 2025-12-31 23:39:13 |
| T7 | row_count_control_total | 30000 | 30000 |
| T7 | sum_amount_control_total | nan | 471354.76 |
| T7 | null_cells | 0 | 0 |
| T7 | event_time_range | 2025-01-01 to 2026-01-31 | 2025-01-01 00:15:56 to 2025-12-31 23:51:57 |
| T7 | negative_amount | 0 | 0 |
| T8 | row_count_control_total | 125 | 125 |
| T8 | sum_minutes_control_total | nan | 1263537.3 |
| T8 | null_cells | 0 | 0 |
| T9 | row_count_control_total | 500 | 500 |
| T9 | null_cells | 0 | 0 |
| T10 | row_count_control_total | 37 | 37 |
| T10 | null_cells | 0 | 0 |
| T11 | row_count_control_total | 250 | 250 |
| T11 | null_cells | 0 | 0 |
| T12 | row_count_control_total | 2 | 2 |
| T12 | null_cells | 0 | 0 |

Monthly row counts (step 4) for the event tables:

| dataset | month | rows |
|---|---|---|
| B1 | 2025-01 | 4274 |
| B1 | 2025-02 | 3827 |
| B1 | 2025-03 | 4219 |
| B1 | 2025-04 | 4101 |
| B1 | 2025-05 | 4386 |
| B1 | 2025-06 | 4007 |
| B1 | 2025-07 | 4319 |
| B1 | 2025-08 | 4213 |
| B1 | 2025-09 | 3985 |
| B1 | 2025-10 | 4225 |
| B1 | 2025-11 | 4114 |
| B1 | 2025-12 | 4330 |
| B4 | 2025-01 | 2073 |
| B4 | 2025-02 | 1888 |
| B4 | 2025-03 | 2046 |
| B4 | 2025-04 | 2038 |
| B4 | 2025-05 | 2188 |
| B4 | 2025-06 | 2065 |
| B4 | 2025-07 | 2109 |
| B4 | 2025-08 | 2212 |
| B4 | 2025-09 | 2027 |
| B4 | 2025-10 | 2153 |
| B4 | 2025-11 | 2068 |
| B4 | 2025-12 | 2133 |
| B7 | 2025-01 | 414 |
| B7 | 2025-02 | 428 |
| B7 | 2025-03 | 424 |
| B7 | 2025-04 | 418 |
| B7 | 2025-05 | 429 |
| B7 | 2025-06 | 405 |
| B7 | 2025-07 | 410 |
| B7 | 2025-08 | 413 |
| B7 | 2025-09 | 430 |
| B7 | 2025-10 | 402 |
| B7 | 2025-11 | 407 |
| B7 | 2025-12 | 420 |
| T1 | 2025-01 | 4298 |
| T1 | 2025-02 | 3781 |
| T1 | 2025-03 | 4145 |
| T1 | 2025-04 | 4027 |
| T1 | 2025-05 | 4234 |
| T1 | 2025-06 | 4153 |
| T1 | 2025-07 | 4323 |
| T1 | 2025-08 | 4282 |
| T1 | 2025-09 | 4108 |
| T1 | 2025-10 | 4255 |
| T1 | 2025-11 | 4117 |
| T1 | 2025-12 | 4277 |
| T3 | 2025-01 | 239 |
| T3 | 2025-02 | 217 |
| T3 | 2025-03 | 221 |
| T3 | 2025-04 | 221 |
| T3 | 2025-05 | 244 |
| T3 | 2025-06 | 224 |
| T3 | 2025-07 | 224 |
| T3 | 2025-08 | 232 |
| T3 | 2025-09 | 234 |
| T3 | 2025-10 | 219 |
| T3 | 2025-11 | 229 |
| T3 | 2025-12 | 246 |
| T4 | 2025-01 | 4318 |
| T4 | 2025-02 | 3826 |
| T4 | 2025-03 | 4128 |
| T4 | 2025-04 | 4125 |
| T4 | 2025-05 | 4194 |
| T4 | 2025-06 | 4090 |
| T4 | 2025-07 | 4334 |
| T4 | 2025-08 | 4144 |
| T4 | 2025-09 | 4178 |
| T4 | 2025-10 | 4236 |
| T4 | 2025-11 | 4113 |
| T4 | 2025-12 | 4314 |
| T6 | 2025-01 | 414 |
| T6 | 2025-02 | 375 |
| T6 | 2025-03 | 419 |
| T6 | 2025-04 | 422 |
| T6 | 2025-05 | 462 |
| T6 | 2025-06 | 419 |
| T6 | 2025-07 | 396 |
| T6 | 2025-08 | 459 |
| T6 | 2025-09 | 414 |
| T6 | 2025-10 | 406 |
| T6 | 2025-11 | 377 |
| T6 | 2025-12 | 437 |
| T7 | 2025-01 | 2644 |
| T7 | 2025-02 | 2238 |
| T7 | 2025-03 | 2647 |
| T7 | 2025-04 | 2547 |
| T7 | 2025-05 | 2470 |
| T7 | 2025-06 | 2426 |
| T7 | 2025-07 | 2532 |
| T7 | 2025-08 | 2566 |
| T7 | 2025-09 | 2458 |
| T7 | 2025-10 | 2527 |
| T7 | 2025-11 | 2454 |
| T7 | 2025-12 | 2491 |

### Alerts per rule

Rule outputs are deterministic, so the Alteryx build must match these alert counts exactly. R_T09 (insider SIM swap) and R_T10 (IMEI churn) show the counts after the fix in commit b9371e2, with T3 planting fixed in 9b5c210. If those rules change again, rerun the sample and update this table.

| rule_id | scenario | dataset | planted rows | alerts | detected (alerts that are planted cases of this scenario) |
|---|---|---|---|---|---|
| R_B01 | card_testing | B1 | 20 | 20 | 20 |
| R_B02 | structuring | B1 | 24 | 24 | 24 |
| R_B03 | mule_network | B1 | 24 | 44 | 24 |
| R_B04 | dormant_account_wake_up | B1 | 24 | 30 | 24 |
| R_B05 | kyc_mismatch_expected_volume | B1 | 24 | 51 | 20 |
| R_B06 | impossible_travel | B1 | 24 | 161 | 12 |
| R_B07 | reversal_abuse | B1 | 24 | 24 | 24 |
| R_B08 | account_takeover | B1 | 24 | 16 | 16 |
| R_B09 | account_takeover | B4 | 10 | 583 | 10 |
| R_B10 | journal_abuse | B7 | 3 | 3 | 3 |
| R_B11 | segregation_of_duties | B7 | 2 | 2 | 2 |
| R_B12 | privileged_access_before_journals | B7 | 2 | 53 | 2 |
| R_B13 | ghost_vendor_or_employee | B10 | 25 | 25 | 25 |
| R_B14 | duplicate_vendor_payments | B10 | 1 | 1 | 1 |
| R_B15 | payroll_after_exit | B11 | 9 | 9 | 9 |
| R_B16 | benford_anomaly | B1 | 20 | 911 | 20 |
| R_T01 | sim_swap_fraud | T4 | 24 | 20 | 6 |
| R_T02 | wallet_tier_breach | T4 | 24 | 66 | 24 |
| R_T03 | dormant_wallet_drain | T4 | 24 | 43 | 24 |
| R_T04 | agent_fraud | T4 | 20 | 20 | 20 |
| R_T05 | sim_box_and_bypass | T1 | 50 | 69 | 38 |
| R_T06 | wangiri | T1 | 30 | 30 | 30 |
| R_T07 | subscription_and_bust_out | T1 | 20 | 20 | 20 |
| R_T08 | interconnect_leakage (route days, changed rule) | T8 | 11 | 11 | 11 |
| R_T09 | insider_sim_swap_or_access_abuse (fixed rule) | T3 | 8 | 8 | 8 |
| R_T10 | imei_churn (fixed rule) | T3 | 6 | 7 | 6 |
| R_T11 | recharge_fraud | T7 | 15 | 15 | 15 |
| R_T12 | subscription_and_bust_out | T7 | 14 | 14 | 14 |
| R_T13 | agent_float_anomalies | T6 | 8 | 9 | 8 |

### Model

The Alteryx learner differs from XGBoost, so model scores, alerts and metrics are not expected to match Python. Check instead that the split sizes match, the threshold sits at the validation 99th percentile, and every metric, threshold and drift row is present in the right columns. Compare predicted labels with Python on record_id for step 20.
