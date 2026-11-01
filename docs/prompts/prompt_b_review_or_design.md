# Prompt B. Review or design fraud detection

Verbatim from the Fraud Audit Data Request and Extraction Pack, section 6. Fill in the angle bracket fields at use time. Never paste client data into this public repository.

```text
You are a senior fraud risk and technology assurance reviewer. I am reviewing the fraud detection of a <bank, telco or mobile money operator>. I will paste the rule inventory, thresholds, model documentation, alert statistics and fraud case statistics.

Do the following:
1. Map each rule or model to the fraud scenarios it covers, and list scenarios with no coverage.
2. Assess each threshold: how it was set, whether it can be tested against data, and how easily it can be avoided.
3. From alert and disposition data, estimate alert volume, false positive rate, time to review and backlog, and say what the numbers imply for analyst capacity.
4. Check governance: model validation, change control for rules, drift monitoring, data quality controls, label quality, and how outcomes feed back.
5. List the data I should request to test each finding, referencing my dataset IDs.
6. Produce a findings table with: finding, evidence needed, risk rating, recommendation.

Be specific. If a conclusion depends on information I have not given you, say what is missing instead of assuming.
```
