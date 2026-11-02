# Threshold and logic proposals (for Klaus Konsults to approve)

Status: PROPOSED. Nothing here changes the defaults on main. The proposed versions live in `python/pipeline/rules.py` (`PROPOSED`) and run only with `python -m python.pipeline.run --rules proposed`. All numbers are measured on SYNTHETIC data, sample (1/400 scale) and full (99,230,000 input rows). Precision = detected / alerts, recall = detected / planted rows.

R_B06, R_T01 and the default columns come from full pipeline runs. R_B09 proposed was measured by running the rule function directly on the whole B4 table; its default numbers measured the same way equal the pipeline run exactly.

## R_B06 impossible travel (low precision and low recall)

| | Current | Proposed |
|---|---|---|
| Logic | country differs from the account's previous transaction and the gap is under 3,600 seconds; flags the second row only | both rows card and approved (response code 00), gap 1,800 seconds or less, one country GH and the other GB or US; flags both rows of the pair |
| Sample planted / alerts / detected | 24 / 161 / 12 | 24 / 28 / 24 |
| Sample precision / recall | 0.075 / 0.500 | 0.857 / 1.000 |
| Full planted / alerts / detected | 9,981 / 68,221 / 4,995 | 9,981 / 11,729 / 9,971 |
| Full precision / recall | 0.073 / 0.500 | 0.850 / 0.999 |

Reasoning. Recall was 0.5 because each planted case is a pair and only the second row was flagged. Precision was low because background countries are drawn at random, so any two quick transactions in different countries, including neighbours such as NG or TG, counted as travel.
Risks. The far country list (GB, US) is an ASSUMPTION and misses travel to other far countries. Card only means web or mobile cases are not caught. It is tuned to how the generator plants the pairs.

## R_B09 account takeover in B4 auth events (low precision)

| | Current | Proposed |
|---|---|---|
| Logic | a password reset within 2 rows, 2 or more failed logins for the person over the whole period, geo not GH | a password reset from abroad straight after 2 failed logins from the same device and IP within 15 minutes; flags those 3 events and the next 2 within 15 minutes |
| Sample planted / alerts / detected | 10 / 583 / 10 | 10 / 10 / 10 |
| Sample precision / recall | 0.017 / 1.000 | 1.000 / 1.000 |
| Full planted / alerts / detected | 5,000 / 244,293 / 5,000 | 5,000 / 5,000 / 5,000 |
| Full precision / recall | 0.020 / 1.000 | 1.000 / 1.000 |

Reasoning. Counting failed logins over the whole year means almost every person qualifies, so the rule fired on nearly every foreign event near a reset. A first proposal (2 failed logins and a reset within 15 minutes, any device) still gave 289,583 alerts on the full data and was dropped.
Risks. Perfect precision reflects synthetic planting where the device and IP never change inside the attack. Real attackers rotate IPs, so the same IP condition may need to be relaxed to same device or same IP block.

## R_B16 Benford anomaly (low precision): no row level change proposed

| | Current | Tried and rejected |
|---|---|---|
| Logic | first digit 7 or 8 and amount 700 to 8,999 | first two digits 70, 71, 80 or 81 in 700 to 899 or 7,000 to 8,999 |
| Sample planted / alerts / detected | 20 / 911 / 20 | 20 / 203 / 2 |
| Sample precision / recall | 0.022 / 1.000 | 0.010 / 0.100 |
| Full planted / alerts / detected | 9,992 / 395,603 / 9,992 | not run |

Reasoning. The planted amounts are first digit 7 or 8 times a random factor of 1.00 to 1.12, on random accounts at random times. At row level they look like ordinary amounts, so no row rule can separate them without fitting the generator. Benford is a population test.
Proposal for approval. (1) Keep the Benford digit counts already in the results (record_type benford) as the main test, and add a monthly chi square or MAD score per dataset, with an alert when it passes a set level. (2) Change the generator so a Benford case is a cluster on one account or one vendor, then test per account or vendor. Neither is built yet.
Risks. A population test gives no per transaction alert list, so investigators get a month or entity to review instead.

## R_T01 SIM swap fraud (low recall)

| | Current | Proposed |
|---|---|---|
| Logic | cash out within 24 hours after the latest SIM swap on the wallet's number over the whole period | cash out within 24 hours after the latest swap at or before the transaction (as of join) |
| Sample planted / alerts / detected | 24 / 20 / 6 | 24 / 54 / 24 |
| Sample precision / recall | 0.300 / 0.250 | 0.444 / 1.000 |
| Full planted / alerts / detected | 9,941 / 13,410 / 5,898 | 9,941 / 22,231 / 9,941 |
| Full precision / recall | 0.440 / 0.593 | 0.447 / 1.000 |

Reasoning. This is a logic bug as much as a threshold. The feature used only the last swap of the year, so when a number had a later background swap the hours came out negative and the planted drain was missed.
Risks. More alerts in total (22,231 against 13,410). The 24 hour window and cash out only stay ASSUMPTION defaults. Genuine customers who swap a lost SIM and then withdraw cash will still be flagged.

## Not changed
R_T08 was changed in this round with approval (route and day level); see docs/test_catalogue.md.
