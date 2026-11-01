"""Step 6: write the shared long format results (docs/output_schema.md) as Parquet, plus CSV for Power BI."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

COLUMNS = ["record_type", "run_id", "created_at", "stack", "domain", "dataset_id", "scenario", "model", "rule_id", "split",
           "record_id", "entity_id", "entity_type", "event_timestamp", "month", "score", "threshold", "predicted_label",
           "true_label", "true_scenario", "amount", "currency", "metric", "value", "alert_rate", "train_rows", "sample_method",
           "step", "check_name", "expected", "observed", "passed", "note", "covered", "threshold_change_pct", "alert_count",
           "detected_count", "score_band", "band_share", "compare_stack", "source_id", "target_id", "edge_weight", "edge_count",
           "first_digit", "observed_count", "expected_share", "route", "cell_id", "latitude", "longitude", "geo_minutes",
           "geo_settled_minutes", "runtime_seconds", "peak_memory_mb", "stage"]


def write_results(rows: list, out: Path, run_id: str, csv: bool = True) -> Path:
    frames = [r for r in rows if isinstance(r, pd.DataFrame)]
    dicts = [r for r in rows if isinstance(r, dict)]
    df = pd.concat(frames + [pd.DataFrame(dicts)], ignore_index=True)
    df = df.reindex(columns=COLUMNS)
    df["run_id"] = run_id
    df["created_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    df["stack"] = "python"
    for c in ["record_type", "run_id", "created_at", "stack", "domain", "dataset_id", "scenario", "model", "rule_id", "split",
              "record_id", "entity_id", "entity_type", "event_timestamp", "month", "true_scenario", "currency", "metric",
              "sample_method", "check_name", "expected", "observed", "note", "score_band", "compare_stack", "source_id",
              "target_id", "route", "cell_id", "stage"]:
        df[c] = df[c].astype("string")
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"results_{run_id}.parquet"
    df.to_parquet(p, index=False)
    if csv:
        df.to_csv(out / "results_latest.csv", index=False)
    return p
