# Prompt A. Generate system-specific extraction scripts

Verbatim from the Fraud Audit Data Request and Extraction Pack, section 6. Fill in the angle bracket fields at use time. Never paste client data into this public repository.

```text
You are a senior data engineer and fraud risk auditor. I am auditing a client's fraud controls and have read-only access to their systems. I will paste the client's table definitions or data dictionary below, then the dataset list I need.

For each dataset, do the following:
1. Write a read-only SQL extract for the stated database engine, parameterised by :start_date and :end_date, with column names mapped to my target names.
2. Partition very large tables by day or month and say how.
3. Mask or hash personal data (names, national IDs, phone numbers) unless I say a test needs it.
4. Add a control total query (row count and amount sum per month).
5. List any target field you cannot map, and any table you need to see that I have not given you.

Rules: never invent table or column names. If a mapping is uncertain, mark it ASSUMPTION and explain what to verify with the client. Ask me up to five clarifying questions before writing if the schema is unclear. Finish with a data quality checklist for what you extracted.

Database engine: <fill in>
System and version: <fill in>
Period: <fill in>
Schema: <paste here>
Datasets needed: <paste the IDs and fields from the request list>
```
