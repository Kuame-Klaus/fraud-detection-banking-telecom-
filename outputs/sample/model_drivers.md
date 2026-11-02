# Model drivers: logistic regression (run python_sample)

SYNTHETIC data only. Prepared by Klaus Konsults. Each feature is log transformed (signed) and standardised, so a coefficient is the change in log odds of fraud for one standard deviation of the feature. The odds ratio is exp(coefficient): above 1 raises the fraud score, below 1 lowers it. These drivers describe the synthetic planting and must be re-estimated on real client data. Related features (for example amount, daily total and how unusual the amount is) share signal, so one of them can take a negative sign while the group together raises the score. Read a driver together with its related features.

## Banking: top 10 drivers

| rank | feature | coefficient | odds ratio | plain English |
|---|---|---|---|---|
| 1 | amount_z | -3.121 | 0.044 | A higher value of how unusual the amount is for this account or wallet lowers the fraud score |
| 2 | ent_day_sum | 2.440 | 11.468 | A higher value of the total amount of the account or wallet that day raises the fraud score |
| 3 | secs_to_next | -2.157 | 0.116 | A higher value of the time until the next event of the same account or wallet lowers the fraud score |
| 4 | log_amount | 1.544 | 4.685 | A higher value of the size of the amount raises the fraud score |
| 5 | acct_dormant | 1.075 | 2.930 | A dormant account raises the fraud score |
| 6 | amount_vs_expected | 1.072 | 2.920 | A higher value of the amount against the account's expected monthly volume raises the fraud score |
| 7 | reversal_flag | 0.863 | 2.369 | A reversal raises the fraud score |
| 8 | country_change_fast | 0.783 | 2.187 | A change of country within an hour raises the fraud score |
| 9 | channel_card | 0.622 | 1.863 | The card channel raises the fraud score |
| 10 | merch_day_count | 0.532 | 1.702 | A higher value of repeat payments to the same merchant that day raises the fraud score |

## Telecom: top 10 drivers

| rank | feature | coefficient | odds ratio | plain English |
|---|---|---|---|---|
| 1 | log_amount | 4.930 | 138.330 | A higher value of the size of the amount raises the fraud score |
| 2 | ent_day_sum | 4.392 | 80.825 | A higher value of the total amount of the account or wallet that day raises the fraud score |
| 3 | amount_z | -2.747 | 0.064 | A higher value of how unusual the amount is for this account or wallet lowers the fraud score |
| 4 | type_cash_out | 1.968 | 7.155 | A cash out raises the fraud score |
| 5 | wallet_dormant | 1.852 | 6.370 | A dormant wallet raises the fraud score |
| 6 | type_merchant | -1.498 | 0.224 | A merchant payment lowers the fraud score |
| 7 | type_cash_in | -1.248 | 0.287 | A cash in lowers the fraud score |
| 8 | round_amount | 1.120 | 3.064 | A round amount (a multiple of 100) raises the fraud score |
| 9 | wallet_limit | -0.883 | 0.413 | A higher value of the wallet tier limit lowers the fraud score |
| 10 | type_p2p | 0.816 | 2.262 | A person to person transfer raises the fraud score |
