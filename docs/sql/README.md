# SQL templates

Copied verbatim from the Fraud Audit Data Request and Extraction Pack. Only file headers were added. No client names, credentials or personal data are included.

From the pack:

> These are generic templates. Replace the table names in angle brackets with the client's, use the parameters :start_date and :end_date, and run each one with a row count check. Verify every column mapping against the client's data dictionary before use.

Files

* b1_transactions.sql : Transactions (B1)
* b7_gl_journal.sql : Journal lines (B7)
* b8_users_access.sql : Access and role changes (B8)
* b4_auth_events.sql : Authentication events (B4)
* t1_cdrs_and_daily_summary.sql : Call detail records (T1)
* t4_momo_wallet_txns.sql : Mobile money transactions (T4)
* t3_sim_swap_events.sql : SIM swaps (T3)
* t6_agents.sql : Agent float and commission (T6)
* control_totals.sql : control totals per month (section 4)

Provisional default templates for the other datasets, and extra control totals, are kept separately in additions/ and are not part of the pack.

## Starting points by system

From the pack: "These are from general knowledge and must be checked against the client's version."

| System | Where to look |
|---|---|
| Oracle Flexcube | Customer account and customer master tables, accounting entry history, user and role tables |
| Finacle | Transaction detail, general account master and customer master tables |
| Temenos T24 | Statement entries, account, customer and funds transfer applications |
| SAP or S/4HANA | Accounting documents (header and line, ACDOCA in S/4HANA), authorisation tables for roles and users, change document tables |
| Mobile money, CDR, billing | Vendor data dictionaries, mediation outputs and billing extracts. Ask the vendor for the schema |
