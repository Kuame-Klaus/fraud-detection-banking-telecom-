# Test catalogue

A Klaus Konsults project. All data in this repo is SYNTHETIC.

This catalogue explains, in plain English, every test the project runs: what fraud it looks for, which data it reads, how it decides, what it writes, how the planted synthetic cases check it, and where it can go wrong. It describes the code as it stands in python/pipeline/ (rules.py, features.py, model.py, run.py) and python/synthetic/generate.py. Where the code differs from the plan in docs/scenario_coverage.md or docs/pipeline_steps.md, the difference is noted under "Differs from plan".

No results are quoted here. Measured figures live only in the shared results file (docs/output_schema.md), for example outputs/sample/results_latest.csv.

## How every test works

1. **Rules.** Each test has a transparent rule in python/pipeline/rules.py with an id such as R_B01. Every threshold in rules.py is an ASSUMPTION default, not a client parameter. On real work each one is set from the client's own limits (B14, T12) or calibrated on their data.
2. **Model.** One XGBoost model per domain, trained on the event table only: B1 for banking and T4 for telecom. It learns from every planted scenario at once (label is 1 when synthetic_scenario is not empty). Training uses a fixed time split: before 1 October 2025 is train, October 2025 is validation, later is test. The alert threshold is set on validation so that 1% of records alert (an ASSUMPTION alert budget). Model features are listed in features.py (BANK_FEATURES and TEL_FEATURES).
3. **Combining.** The code does not merge rule and model scores into one number. Rules write score rows with model = rule and score = 1.0 for each hit. The model writes its own score rows with model = xgboost, for the test split only. A reviewer sees both and can compare them. A combined score is not built yet.
4. **Outputs.** For each rule, run.py writes metric rows (planted_rows, alerts, recall, precision) with record_type metric, domain, model = rule, rule_id, scenario, dataset_id, split = all. Model results are metric, score, threshold and drift rows. Tests on tables other than B1 and T4 are covered only by their rule.
5. **Planted cases.** The generator plants labelled cases for each scenario into the right tables, writing the scenario name into synthetic_scenario. About 0.05% of event rows per scenario are planted (PLANT_SHARE, an ASSUMPTION). Recall and precision per rule are measured against these labels. Because the plants were designed alongside the rules, good scores on synthetic data show the pipeline works end to end; they do not show how the test performs on real fraud.

## Index

| # | Group | Test | Source | Datasets | Rule id |
|---|---|---|---|---|---|
| 1 | Banking | Card testing | Pack | B1, B9 | R_B01 |
| 2 | Banking | Account takeover | Pack | B1, B4 | R_B08, R_B09 |
| 3 | Banking | Mule network | Pack | B1, B6 | R_B03 |
| 4 | Banking | Structuring | Pack | B1, B14 | R_B02 |
| 5 | Banking | Journal abuse | Pack | B7 | R_B10 |
| 6 | Banking | Segregation of duties | Pack | B7 | R_B11 |
| 7 | Banking | Ghost vendor or employee | Pack | B10 | R_B13 |
| 8 | Banking | Dormant account wake up | Added | B1, B2 | R_B04 |
| 9 | Banking | KYC mismatch with expected volume | Added | B1, B2 | R_B05 |
| 10 | Banking | Impossible travel | Added | B1 | R_B06 |
| 11 | Banking | Duplicate vendor payments | Added | B10 | R_B14 |
| 12 | Banking | Payroll after exit | Added | B11 | R_B15 |
| 13 | Banking | Privileged access changes before journals | Added | B7, B8 | R_B12 |
| 14 | Banking | Benford's law | Added | B1, B7 | R_B16 |
| 15 | Banking | Reversal abuse | Added | B1 | R_B07 |
| 16 | Telecom | SIM swap fraud | Pack | T3, T4, T5 | R_T01 |
| 17 | Telecom | SIM box and bypass | Pack | T1 | R_T05 |
| 18 | Telecom | Subscription and bust out | Pack | T1, T7 | R_T07, R_T12 |
| 19 | Telecom | Agent fraud | Pack | T4 | R_T04 |
| 20 | Telecom | Insider SIM swap or access abuse | Pack | T3 | R_T09 |
| 21 | Telecom | Wallet tier breach | Added | T4, T5 | R_T02 |
| 22 | Telecom | Dormant wallet drain | Added | T4, T5 | R_T03 |
| 23 | Telecom | Wangiri | Added | T1 | R_T06 |
| 24 | Telecom | IMEI churn | Added | T3 | R_T10 |
| 25 | Telecom | Recharge fraud | Added | T7 | R_T11 |
| 26 | Telecom | Interconnect leakage | Added | T1, T8 | R_T08 |
| 27 | Telecom | Agent float anomalies | Added | T6 | R_T13 |
| 28 | Detection review | Rule coverage gaps | Added | all | none |
| 29 | Detection review | Threshold sensitivity | Added | B1, T4 | none |
| 30 | Detection review | Monthly score drift | Added | B1, T4 | none |
| 31 | Detection review | Agreement between the three tools | Added | all | none |

Counts: banking 15 (7 pack, 8 added), telecom 12 (5 pack, 7 added), detection review 4. Total 31.

## Banking

### 1. Card testing (pack)

* **What it catches.** Criminals checking stolen card numbers with many tiny purchases before a big one. Catching it early stops the larger losses that follow.
* **Data.** B1 amount, channel, merchant_id, account_id, timestamp, response_code. The plan also lists B9 authorisations.
* **Rule R_B01.** Flags a card transaction under 10 when the same account hits the same merchant 10 or more times that day. Both 10s are ASSUMPTION defaults.
* **Model features.** merch_day_count, ent_day_count, log_amount, declined, secs_since_prev, channel_card.
* **Outputs.** Rule metric and score rows with scenario card_testing, rule_id R_B01, dataset_id B1.
* **Planted cases.** Bursts of 20 card attempts between 0.5 and 5, on one merchant within 10 minutes, mostly declined. Bursts are also planted in B9.
* **Differs from plan.** The rule reads B1 only; B9 plants exist but no rule reads B9 yet. Decline codes are a model feature, not part of the rule.
* **Limits and false positives.** Small repeat purchases at one merchant (transport, vending, parking) look similar. Real testing may spread across merchants.

### 2. Account takeover (pack)

* **What it catches.** Someone else taking control of an online account and moving money out.
* **Data.** B4 person_id, event_type, timestamp, geo. B1 channel, amount, timestamp.
* **Rules.** R_B09 on B4: a password reset among a person's nearby events (a rolling window of 5), at least 2 failed logins, and a login location outside GH. R_B08 on B1: a web transfer over 2,500 within 30 minutes of the previous transaction. All values are ASSUMPTION defaults.
* **Model features.** channel_web, log_amount, secs_since_prev, amount_z, is_debit.
* **Outputs.** Two sets of rule rows under scenario account_takeover, rule_ids R_B08 (B1) and R_B09 (B4).
* **Planted cases.** In B4, a burst of 5 events within 15 minutes; in B1, 3 large web debits within 30 minutes.
* **Differs from plan.** The plan links logins to new beneficiaries (B6) and devices (B5). The code does not yet join B4 to B1 events, so the two rules fire separately.
* **Limits and false positives.** Travellers and people who forget passwords. The GH home country is hard coded for the synthetic data.

### 3. Mule network (pack)

* **What it catches.** Accounts used to receive stolen money and pass it on quickly.
* **Data.** B1 account_id, direction, amount, timestamp, counterparty_account. The plan also lists B6 beneficiaries.
* **Rule R_B03.** Flags a credit over 4,000 followed by another transaction within an hour, or a debit within an hour of the previous one on a day with 5 or more transactions. ASSUMPTION defaults.
* **Model features.** secs_to_next, secs_since_prev, ent_day_count, ent_day_sum, is_debit, log_amount.
* **Outputs.** Rule rows for mule_network, plus edge rows (source_id, target_id, edge_weight, edge_count) for the network chart.
* **Planted cases.** One large inbound credit then 5 fast outbound debits to other accounts within an hour. B6 also has planted hub payees.
* **Differs from plan.** B6 is not read by the rule.
* **Limits and false positives.** Busy small businesses and payroll accounts move money fast too. A real mule chain spans many accounts, which a single account rule cannot see.

### 4. Structuring (pack)

* **What it catches.** Splitting cash into amounts just under a reporting limit to avoid reports.
* **Data.** B1 amount, account_id, timestamp. B14 holds the threshold.
* **Rule R_B02.** Flags amounts between 9,000 and 10,000 when the account has 3 or more such amounts. The 10,000 limit and the count of 3 are ASSUMPTION defaults; on real work the limit comes from B14.
* **Model features.** near_threshold, log_amount, ent_day_count.
* **Outputs.** Rule rows for structuring.
* **Planted cases.** 6 branch credits between 90% and 99.5% of the limit within 3 days.
* **Differs from plan.** The count is over the whole period, not a rolling window, and the limit is fixed in the code rather than read from B14.
* **Limits and false positives.** Businesses with regular takings near the limit. Structuring below the band (for example at 8,000) is missed.

### 5. Journal abuse (pack)

* **What it catches.** Manual ledger entries used to hide fraud or move results.
* **Data.** B7 is_manual, debit, credit, entry_timestamp, description.
* **Rule R_B10.** Flags a manual entry with a round amount (a multiple of 10,000) posted at the weekend or before 5 am. ASSUMPTION defaults.
* **Model features.** None. B7 is not in the model.
* **Outputs.** Rule rows for journal_abuse, dataset_id B7.
* **Planted cases.** Manual round amount entries out of hours with a vague description.
* **Differs from plan.** The plan also uses preparer and approver patterns and B8; those are separate tests here (6 and 13). Description text is not tested.
* **Limits and false positives.** Month end closing often runs late with round accruals.

### 6. Segregation of duties (pack)

* **What it catches.** One person both preparing and approving an entry, which removes the check a second person gives.
* **Data.** B7 preparer_id, approver_id.
* **Rule R_B11.** Flags lines where preparer_id equals approver_id. No threshold.
* **Model features.** None.
* **Outputs.** Rule rows for segregation_of_duties.
* **Planted cases.** Manual lines where the approver is set to the preparer.
* **Differs from plan.** The plan also uses B8 roles and B10 vendor creators and approvers. The code checks B7 only.
* **Limits and false positives.** Small teams may allow self approval under a documented policy.

### 7. Ghost vendor or employee (pack)

* **What it catches.** Payments to vendors or staff who do not exist.
* **Data.** B10 vendor_id, vendor_bank_account, payment_amount, payment_date.
* **Rule R_B13.** Flags payments where vendor_bank_account starts with "BEBANK".
* **Model features.** None.
* **Outputs.** Rule rows for ghost_vendor_or_employee, dataset_id B10.
* **Planted cases.** Ghost vendors whose bank account uses the BEBANK prefix.
* **Differs from plan.** The plan compares vendor and employee bank accounts, addresses and creators. The rule only finds the synthetic marker, so it **works on synthetic data only** and must be replaced before real use. Ghost employees in B11 are not tested.
* **Limits and false positives.** As written it has no value on client data.

### 8. Dormant account wake up (added)

* **What it catches.** A quiet account suddenly used to move money, often after takeover or sale to a fraudster.
* **Data.** B2 account_id, status. B1 account_id, amount.
* **Rule R_B04.** Flags transactions over 5,000 on accounts whose B2 status is dormant. ASSUMPTION default.
* **Model features.** acct_dormant, log_amount, amount_z.
* **Outputs.** Rule rows for dormant_account_wake_up.
* **Planted cases.** 3 debits between 8,000 and 50,000 on a dormant account.
* **Differs from plan.** The plan measures time since last activity; the code uses the status flag only.
* **Limits and false positives.** Genuine customers returning after a long gap.

### 9. KYC mismatch with expected volume (added)

* **What it catches.** Accounts moving far more money than the customer declared when opening, a sign of laundering.
* **Data.** B2 expected_monthly_volume. B1 amount.
* **Rule R_B05.** Flags a transaction larger than 20 times the expected monthly volume (1,000 when missing). ASSUMPTION defaults.
* **Model features.** amount_vs_expected, log_amount.
* **Outputs.** Rule rows for kyc_mismatch_expected_volume.
* **Planted cases.** 2 credits between 80,000 and 300,000.
* **Differs from plan.** The plan compares monthly totals and KYC level. The code compares single transactions and ignores kyc_level.
* **Limits and false positives.** Out of date KYC profiles and one off events such as a house sale.

### 10. Impossible travel (added)

* **What it catches.** A card used in two countries too close in time for one person, so one use is likely fraud.
* **Data.** B1 account_id, country, timestamp.
* **Rule R_B06.** Flags a country change within an hour of the previous transaction. ASSUMPTION default.
* **Model features.** country_change_fast, foreign.
* **Outputs.** Rule rows for impossible_travel.
* **Planted cases.** A GH card transaction then one in the US or GB within 30 minutes.
* **Differs from plan.** The plan uses B9 terminals; the code uses B1 country only.
* **Limits and false positives.** Online merchants that report a foreign country.

### 11. Duplicate vendor payments (added)

* **What it catches.** The same invoice paid twice, by mistake or on purpose.
* **Data.** B10 vendor_id, payment_amount, payment_date.
* **Rule R_B14.** Flags any later payment with the same vendor and the same amount as an earlier one. No threshold.
* **Model features.** None.
* **Outputs.** Rule rows for duplicate_vendor_payments.
* **Planted cases.** A copy of a payment placed straight after the original.
* **Differs from plan.** No time window and no invoice number (open question).
* **Limits and false positives.** Fixed monthly fees repeat genuinely. This needs an invoice number or a day window before real use.

### 12. Payroll after exit (added)

* **What it catches.** Salary still paid to people who have left, often redirected to someone else.
* **Data.** B11 exit_date, pay_date, pay_amount.
* **Rule R_B15.** Flags a positive payment dated after the exit date. No threshold.
* **Model features.** None.
* **Outputs.** Rule rows for payroll_after_exit.
* **Planted cases.** Pay runs dated after exit.
* **Limits and false positives.** Final pay, leave payouts and back pay are paid after exit genuinely.

### 13. Privileged access changes before journals (added)

* **What it catches.** A user given powerful ledger rights who then posts manual entries.
* **Data.** B8 user_id, permission. B7 preparer_id, is_manual.
* **Rule R_B12.** Flags manual B7 lines whose preparer holds the admin_gl permission in B8. No threshold.
* **Model features.** None.
* **Outputs.** Rule rows for privileged_access_before_journals.
* **Planted cases.** A few accountants are given admin_gl and post manual lines.
* **Differs from plan.** The plan checks the order in time (change_time before entry_timestamp). The code checks the permission only, not timing.
* **Limits and false positives.** Legitimate system administrators who also post.

### 14. Benford's law (added)

* **What it catches.** Made up amounts, which often break the natural pattern of first digits (more 1s than 9s).
* **Data.** B1 amount; B7 debit for the chart.
* **Rule R_B16.** Flags B1 amounts from 700 to under 9,000 that start with 7 or 8. ASSUMPTION choice.
* **Model features.** lead_digit.
* **Outputs.** Rule rows for benford_anomaly, and benford rows (first_digit, observed_count, expected_share) for B1, B7 and T4.
* **Planted cases.** Clusters of 10 amounts forced to start with 7 or 8.
* **Differs from plan.** The plan uses B7 and B10 for the test. The rule reads B1 and the chart covers B1, B7 and T4. B10 is not included.
* **Limits and false positives.** Benford is a population check, not a single transaction test. Many genuine amounts start with 7 or 8, so this rule will raise many false alerts on real data.

### 15. Reversal abuse (added)

* **What it catches.** Repeated reversals used to create money or hide withdrawals.
* **Data.** B1 reversal_flag, original_txn_id, account_id.
* **Rule R_B07.** Flags reversals on accounts with 3 or more reversals. ASSUMPTION default.
* **Model features.** reversal_flag.
* **Outputs.** Rule rows for reversal_abuse.
* **Planted cases.** 4 reversals on one account.
* **Differs from plan.** B7 reversals are not tested, and the link to the original transaction is not checked.
* **Limits and false positives.** Merchants with genuine refund volumes.

## Telecom

### 16. SIM swap fraud (pack)

* **What it catches.** A fraudster moves a victim's number to a new SIM, then drains their mobile money wallet.
* **Data.** T3 msisdn, swap_time. T4 wallet_id, timestamp, type, amount. T5 wallet_id, msisdn (links wallets to numbers within telecom).
* **Rule R_T01.** Flags a cash out within 24 hours after the latest SIM swap on the wallet's number. ASSUMPTION default.
* **Model features.** hours_since_swap, type_cash_out, log_amount, secs_since_prev.
* **Outputs.** Rule rows for sim_swap_fraud, dataset_id T4.
* **Planted cases.** Swaps in T3, followed within hours by cash outs in T4 for the same wallet.
* **Differs from plan.** The pack also uses OTP requests, which no T dataset holds. The plan lists T2; the code uses T5 instead. Only the latest swap per number is used.
* **Limits and false positives.** Customers who replace a lost phone and withdraw cash the same day.

### 17. SIM box and bypass (pack)

* **What it catches.** International calls routed through banks of local SIMs to avoid interconnect fees.
* **Data.** T1 caller, call_type, duration_sec, start_time.
* **Rule R_T05.** Flags voice calls under 150 seconds from callers with 20 or more calls that day. ASSUMPTION defaults.
* **Model features.** None. T1 is not in the model.
* **Outputs.** Rule rows for sim_box_and_bypass, dataset_id T1.
* **Planted cases.** One SIM making 50 short calls to many numbers from one cell within 4 hours.
* **Differs from plan.** The plan also uses cell_id, imei and T8. The rule does not.
* **Limits and false positives.** Call centres and sales staff.

### 18. Subscription and bust out (pack)

* **What it catches.** Subscribers who sign up, run up heavy usage and never pay.
* **Data.** T1 duration_sec, roaming_flag. T7 bad_debt_amount.
* **Rules.** R_T07: calls of 30 minutes or more while roaming. R_T12: bad debt over 1,000. ASSUMPTION defaults.
* **Model features.** None.
* **Outputs.** Rule rows for subscription_and_bust_out, rule_ids R_T07 (T1) and R_T12 (T7).
* **Planted cases.** Bust out subscribers in T2, heavy usage in T1 and unpaid invoices in T7.
* **Differs from plan.** T2 (activation date, credit limit, duplicate IDs) is not read.
* **Limits and false positives.** Genuine roaming customers. Bad debt is only known after the loss.

### 19. Agent fraud (pack)

* **What it catches.** Mobile money agents splitting deposits or faking transactions to earn extra commission.
* **Data.** T4 agent_id, type, amount, timestamp.
* **Rule R_T04.** Flags cash ins with a round amount (multiple of 100) by agents with 8 or more transactions that day. ASSUMPTION defaults.
* **Model features.** agent_day_count, round_amount, has_reversal, type_cash_in.
* **Outputs.** Rule rows for agent_fraud, plus agent to wallet edge rows for the network chart.
* **Planted cases.** One agent with 10 round cash ins, half later reversed.
* **Differs from plan.** T6 commission is a separate test (27). Reversals are a model feature, not in the rule.
* **Limits and false positives.** Busy agents in markets with round cash habits.

### 20. Insider SIM swap or access abuse (pack)

* **What it catches.** Shop staff doing swaps for fraudsters.
* **Data.** T3 performed_by_user, swap_time.
* **Rule R_T09.** Flags night swaps (before 5 am) when the same user does 5 or more night swaps on the same day. ASSUMPTION defaults. Changed from a top 0.1% quantile cut, which found nothing at sample size.
* **Model features.** None.
* **Outputs.** Rule rows for insider_sim_swap_or_access_abuse, dataset_id T3.
* **Planted cases.** Blocks of 8 call centre swaps between midnight and 4 am, each block by one user on one night (8 rows in the sample).
* **Differs from plan.** The plan pairs T3 with B8. Since banking and telecom are separate, the code uses T3 only. shop_id is not used.
* **Limits and false positives.** Genuine night shift staff with a busy queue.

### 21. Wallet tier breach (added)

* **What it catches.** Wallets moving more than their KYC tier allows, a sign of a mule or a weak check.
* **Data.** T5 wallet_limit. T4 amount.
* **Rule R_T02.** Flags T4 amounts above the wallet's limit. The limit comes from the data.
* **Model features.** over_tier, wallet_limit.
* **Outputs.** Rule rows for wallet_tier_breach.
* **Planted cases.** 4 successful transactions above the limit on tier 1 wallets.
* **Differs from plan.** Limits come from T5, not T12. Totals over a day or month are not checked.
* **Limits and false positives.** Limit changes not yet updated in T5.

### 22. Dormant wallet drain (added)

* **What it catches.** A quiet wallet suddenly emptied, often after a takeover.
* **Data.** T5 status. T4 type, amount.
* **Rule R_T03.** Flags cash outs over 500 from wallets with dormant status. ASSUMPTION default.
* **Model features.** wallet_dormant, type_cash_out, log_amount.
* **Outputs.** Rule rows for dormant_wallet_drain.
* **Planted cases.** 3 cash outs from a dormant wallet.
* **Limits and false positives.** Owners returning after a long gap.

### 23. Wangiri (added)

* **What it catches.** "One ring" scams that trick people into calling back premium numbers.
* **Data.** T1 caller, duration_sec.
* **Rule R_T06.** Flags calls of 3 seconds or less from callers with 10 or more such calls. ASSUMPTION defaults.
* **Model features.** None.
* **Outputs.** Rule rows for wangiri.
* **Planted cases.** One roaming number making 30 calls of 0 to 3 seconds within 30 minutes.
* **Differs from plan.** Call direction and origin country are open questions and not used.
* **Limits and false positives.** Dropped calls and auto diallers.

### 24. IMEI churn (added)

* **What it catches.** A number moved between many handsets, often linked to stolen phones or SIM swap rings.
* **Data.** T3 msisdn, swap_id.
* **Rule R_T10.** Flags every swap in a run of 4 or more swaps on the same number within 30 days. ASSUMPTION defaults. Changed from 4 or more swaps over the whole year.
* **Model features.** None.
* **Outputs.** Rule rows for imei_churn, dataset_id T3.
* **Planted cases.** Blocks of 6 swaps on one number within 30 days, each new IMEI becoming the next old IMEI (6 rows in the sample).
* **Differs from plan.** The plan also uses T1 imei and the old and new IMEI. The code counts swaps in a 30 day window; the planted IMEI chain is not used by the rule yet.
* **Limits and false positives.** Phone repair and upgrades.

### 25. Recharge fraud (added)

* **What it catches.** Stolen or fake vouchers and card funded top ups in bursts.
* **Data.** T7 msisdn, event_time, event_type.
* **Rule R_T11.** Flags top ups by numbers with 8 or more top ups that day. ASSUMPTION default.
* **Model features.** None.
* **Outputs.** Rule rows for recharge_fraud.
* **Planted cases.** 15 top ups on one number within 15 minutes.
* **Differs from plan.** No voucher serial number (open question).
* **Limits and false positives.** Resellers who top up for others.

### 26. Interconnect leakage (added)

* **What it catches.** Traffic carried on a route that is under settled, so revenue is lost.
* **Data.** T1 route, duration_sec. T8 route, minutes, settlement_amount.
* **Rule R_T08.** Works out each route's settlement per minute from T8 and flags all T1 calls on routes below 60% of the median. ASSUMPTION default.
* **Model features.** None.
* **Outputs.** Rule rows for interconnect_leakage, plus geo rows with geo_minutes and geo_settled_minutes per route and day.
* **Planted cases.** Traffic placed on routes 37 to 39, which are unsettled in T8.
* **Differs from plan.** The plan compares T1 minutes with settled minutes per day. The rule compares settlement rates per route over the whole period. The minutes comparison exists only in the geo rows.
* **Limits and false positives.** Routes with genuinely cheaper rates. Flags whole routes, not single calls.

### 27. Agent float anomalies (added)

* **What it catches.** Agents moving float at odd times or in odd sizes, which can hide cash theft or commission gaming.
* **Data.** T6 movement_time, float_amount.
* **Rule R_T13.** Flags float movements over 30,000 before 5 am. ASSUMPTION defaults.
* **Model features.** None.
* **Outputs.** Rule rows for agent_float_anomalies, dataset_id T6.
* **Planted cases.** 8 night rebalances with large float and high commission.
* **Differs from plan.** commission_amount and region are not used.
* **Limits and false positives.** Agents who rebalance at night on purpose.

## Detection review

### 28. Rule coverage gaps

* **What it checks.** Whether every scenario has at least one rule, so no fraud type goes untested.
* **How.** run.py compares the scenario list in python/synthetic/config.yaml with the scenarios that have a rule in rules.py.
* **Outputs.** coverage rows with domain, scenario, covered and note ("rule present" or "no rule yet").
* **Differs from plan.** The plan also lists scenarios where no alert fires and rules mapped to no scenario. The code only checks that a rule exists.
* **Limits.** A rule that exists but catches nothing still counts as covered. The per rule recall metric rows show that separately.

### 29. Threshold sensitivity

* **What it checks.** How alerts and detection change if the threshold moves by minus 20%, minus 10%, 0, plus 10% and plus 20%.
* **How.** Run for the XGBoost model in each domain, around its validation based threshold.
* **Outputs.** threshold rows with threshold_change_pct, threshold, alert_count and detected_count.
* **Differs from plan.** Rules are not swept yet; their thresholds stay fixed.
* **Limits.** Only five fixed points, so it shows direction, not the best threshold.

### 30. Monthly score drift

* **What it checks.** Whether the model's scores shift month by month, which can mean the data or behaviour has changed.
* **How.** The share of scored records in each score band per month.
* **Outputs.** drift rows with month, score_band and band_share.
* **Differs from plan.** The plan compares with the training period using a drift statistic in value. The code writes band shares only, and the comparison is left to the reader or chart.
* **Limits.** Synthetic data has no real seasonality, so drift on it means little.

### 31. Agreement between the three tools

* **What it checks.** Whether Alteryx, KNIME and Python flag the same records, using the shared record_id.
* **Outputs.** Planned as agreement rows with stack, compare_stack, scenario and value.
* **Differs from plan.** **Not built.** No code writes agreement rows yet, because the Alteryx and KNIME flows do not exist yet (see docs/alteryx_knime_design.md).
* **Limits.** The models differ by design (XGBoost against built in learners), so some disagreement is expected; rules should agree exactly.
