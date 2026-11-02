# Open questions and defaults

Every item below has a provisional default so work can proceed. Each default is an assumption that the client can override.

## 1. Differences between the pack field lists and the pack SQL

Default: keep the SQL names.

1. B1: field list "timestamp" is aliased from txn_timestamp; "reversal flag" becomes reversal_flag; "original txn id" becomes original_txn_id; "channel" from channel_code; "country" from country_code; "direction" from dr_cr_ind.
2. B4: the SQL adds event_id, which is not in the field list. person_id comes from customer_id, ip from ip_address, geo from geo_location, timestamp from event_time.
3. B7: "document type" becomes document_type; "reversal flag" becomes reversal_ind; preparer_id from created_by; approver_id from approved_by; is_manual from manual_flag.
4. B8: "permissions" in the list is permission in the SQL; "active flag" becomes is_active (from status); "access change log" is split into change_time, changed_by and change_type; role from role_name.
5. T1: caller from caller_msisdn; callee from called_number; route from route_id ("route or trunk" in the list); the field list has "roaming flag" but the SQL does not return it (default: add roaming_flag as ASSUMPTION).
6. T1 daily summary keeps the raw names caller_msisdn and called_number instead of caller and callee. Default: keep as written.
7. T3: "swap time" becomes swap_time; "old and new imei" become old_imei and new_imei; "staff or shop id" becomes performed_by_user and shop_id. The field list includes imsi and imei, which the SQL does not return.
8. T4: field list "reversal" is reversal_of in the SQL; type from txn_type; counterparty from counterparty_wallet; timestamp from txn_time. B1 uses reversal_flag plus original_txn_id while T4 uses reversal_of; the naming styles differ and are kept as is.
9. T6: "float movements" become movement_time, movement_type and float_amount; "commission payouts" become payout_date and commission_amount.

## 2. Missing column names

Default: snake_case names from the pack's wording, marked ASSUMPTION in docs/data_dictionary.md.

## 3. Missing SQL templates

Default: templates for B2, B3, B5, B6, B9 to B14, T2, T5 and T7 to T12 in docs/sql/additions/, each with an ASSUMPTION header.

## 4. Control totals for other tables

Default: B7 and T1 queries in docs/sql/additions/, marked ADDITION.

## 5. Banking and telecom as separate entities (RESOLVED)

Decision: banking and telecom are two separate entities, with no shared keys and no joins between them. The SIM swap scenario uses telecom data only (T3, T4 and T2); its B4 dependency from the pack is removed. Open point: the pack mentions OTP requests for SIM swap, which no T dataset holds, so the client may supply an OTP or SMS log if wanted.

## 6. Sizing

Default: about 20 million rows in B1 and in T1, with T4 at a similar scale. Other table sizes in python/synthetic/config.yaml are assumptions chosen to look realistic, not measured from any client.

## 7. Still open

1. The pack gives no fraud rates or thresholds. They will come from calibration to public data and from B14 and T12, not invented.
2. Whether synthetic alerts (B13, T11) are needed outside review mode. Default: generate them, since templates exist.
3. The time zone for synthetic timestamps. Default: UTC, stated in the manifest.

## 8. Columns missing for the Klaus Konsults extensions

1. Impossible travel needs terminal or transaction location below country level (city or coordinates). B1 has only country and B9 terminal data is not defined in detail.
2. Duplicate vendor payments would be stronger with an invoice number in B10.
3. Wangiri needs call direction (inbound or outbound) and originating country in T1. The T1 SQL has neither.
4. Recharge fraud would need a voucher or serial number in T7.
5. Interconnect leakage joins T1 and T8 on route; T1 has no carrier column, so the join is by route and day only.
6. Telecom maps (chart 12) need cell latitude and longitude. T9 has only "location". Round 7: SYNTHETIC locations near Ghana towns are used for now (python/pipeline/geo.py); the client site list is still needed.
7. Insider SIM swap uses B8 in the pack, which crosses into banking. With the entities kept separate, telecom staff access data is needed; the pack has no telecom equivalent of B8. Default: use T3 performed_by_user and shop_id only until a telecom access log is supplied.
8. Planted case shares per scenario are not given anywhere. Default: set from calibration where public data allows, otherwise a documented provisional value.
