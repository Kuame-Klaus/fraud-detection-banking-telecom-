# Engagement rules and extra requests

Verbatim from the Fraud Audit Data Request and Extraction Pack, sections 1 and 7.

## Ground rules before any extraction

* Get written authorisation, an engagement scope and an NDA. Confirm data protection duties (Ghana's Data Protection Act, 2012 (Act 843), client policy, cross-border rules) with legal.
* Ask for read-only access on a replica or reporting database, and run extracts off-peak.
* Minimise personal data. Hash national IDs, phone numbers and names unless a test needs them, and let the client keep the hashing key.
* Period: at least 12 months, plus 3 months before it for baselines. Six months is the floor.
* Format: UTF-8 CSV or Parquet, ISO 8601 timestamps with the time zone stated, decimal amounts with currency, one file per month for large tables.
* Control totals: ask the client to supply row counts and amount totals per table per month from their own reports, before you compare anything.
* Chain of custody: log the extract date, query, person and a SHA-256 hash of every file. Move files over an encrypted channel and delete them at the end as agreed.

## Extra requests in review or design mode

* The client's documented fraud typologies and risk assessment, and the date they were last updated.
* The complete rule inventory with thresholds, owners, change history and the date each rule last fired.
* Alert volumes, analyst dispositions, escalation times and confirmed fraud outcomes for at least 12 months.
* Model documents, validation reports, performance monitoring and the process for retraining.
* Fraud loss reports, recoveries, regulator returns and any internal audit findings.
* An organisation chart for the fraud and risk teams, plus the data flow from source systems to the monitoring tool, so you can test completeness at each hand-off.
