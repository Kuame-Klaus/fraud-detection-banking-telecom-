# Chart plan

The same 12 charts are planned for Python (python/viz/) and Power BI (powerbi/, planned only). Both read only the shared results files in docs/output_schema.md. No values are shown until real runs produce them.

| # | Chart | record_type | Main columns |
|---|---|---|---|
| 1 | KPI overview | score, metric | stack, domain, scenario, predicted_label, true_label, amount, metric, value |
| 2 | Detection heat map by scenario and tool | metric | scenario, stack, metric, value |
| 3 | Precision and recall curves and confusion matrices | score | stack, model, split, score, true_label, predicted_label |
| 4 | Alert trends | score | event_timestamp, month, scenario, predicted_label, stack |
| 5 | Risk leaderboards | score | entity_id, entity_type, score, amount, scenario |
| 6 | Mule and agent network graphs | edge | source_id, target_id, edge_weight, edge_count, entity_type |
| 7 | Hour by weekday heat maps | score | event_timestamp, predicted_label, scenario |
| 8 | Benford chart | benford | dataset_id, first_digit, observed_count, expected_share |
| 9 | Threshold slider | threshold, score | rule_id, model, threshold_change_pct, threshold, alert_count, detected_count, score |
| 10 | Data quality and reconciliation page | dq | step, dataset_id, month, check_name, expected, observed, passed, note |
| 11 | Tool runtime and memory | run, metric | stack, stage, runtime_seconds, peak_memory_mb, train_rows |
| 12 | Telecom route and cell maps | geo | route, cell_id, latitude, longitude, geo_minutes, geo_settled_minutes |

Review checks also feed the charts: coverage rows feed chart 2, drift rows feed chart 4, and agreement rows feed charts 1 and 2.
