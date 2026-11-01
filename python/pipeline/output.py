"""Step 6: write the shared long format results (docs/output_schema.md), streamed to Parquet one frame at a time."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

STR = ["record_type", "run_id", "created_at", "stack", "domain", "dataset_id", "scenario", "model", "rule_id", "split",
       "record_id", "entity_id", "entity_type", "event_timestamp", "month", "true_scenario", "currency", "metric",
       "sample_method", "check_name", "expected", "observed", "note", "score_band", "compare_stack", "source_id",
       "target_id", "route", "cell_id", "stage"]
INT = ["predicted_label", "true_label", "train_rows", "step", "alert_count", "detected_count", "edge_count",
       "first_digit", "observed_count"]
BOOL = ["passed", "covered"]
COLUMNS = ["record_type", "run_id", "created_at", "stack", "domain", "dataset_id", "scenario", "model", "rule_id", "split",
           "record_id", "entity_id", "entity_type", "event_timestamp", "month", "score", "threshold", "predicted_label",
           "true_label", "true_scenario", "amount", "currency", "metric", "value", "alert_rate", "train_rows", "sample_method",
           "step", "check_name", "expected", "observed", "passed", "note", "covered", "threshold_change_pct", "alert_count",
           "detected_count", "score_band", "band_share", "compare_stack", "source_id", "target_id", "edge_weight", "edge_count",
           "first_digit", "observed_count", "expected_share", "route", "cell_id", "latitude", "longitude", "geo_minutes",
           "geo_settled_minutes", "runtime_seconds", "peak_memory_mb", "stage"]
SCHEMA = pa.schema([(c, pa.string() if c in STR else pa.int64() if c in INT else pa.bool_() if c in BOOL else pa.float64())
                    for c in COLUMNS])


class ResultsWriter:
    def __init__(self, out: Path, run_id: str):
        out.mkdir(parents=True, exist_ok=True)
        self.out, self.run_id = out, run_id
        self.path = out / f"results_{run_id}.parquet"
        self.created = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.w = pq.ParquetWriter(self.path, SCHEMA, compression="zstd")
        self.dicts: list[dict] = []
        self.counts: dict[str, int] = {}

    def add(self, row: dict) -> None:
        self.dicts.append(row)

    def write(self, df: pd.DataFrame) -> None:
        if df is None or not len(df):
            return
        df = df.reindex(columns=COLUMNS)
        df["run_id"] = self.run_id; df["created_at"] = self.created; df["stack"] = "python"
        for c in STR:
            df[c] = df[c].astype("string")
        for c in INT:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        for c in BOOL:
            df[c] = df[c].astype("boolean")
        for c in set(COLUMNS) - set(STR) - set(INT) - set(BOOL):
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
        for rt, n in df["record_type"].value_counts().items():
            self.counts[rt] = self.counts.get(rt, 0) + int(n)
        self.w.write_table(pa.Table.from_pandas(df, schema=SCHEMA, preserve_index=False))

    def close(self, csv_full: bool) -> Path:
        if self.dicts:
            self.write(pd.DataFrame(self.dicts)); self.dicts = []
        self.w.close()
        pf = pq.ParquetFile(self.path)
        summary = []
        for i in range(pf.num_row_groups):
            t = pf.read_row_group(i).to_pandas()
            if csv_full:
                summary.append(t)
            else:
                summary.append(t[t["record_type"] != "score"])
        df = pd.concat(summary, ignore_index=True)
        name = "results_latest.csv" if csv_full else "results_summary.csv"
        df.to_csv(self.out / name, index=False)
        return self.path


def write_results(rows: list, out: Path, run_id: str, csv: bool = True) -> Path:
    """Convenience for small runs: rows is a list of dicts and DataFrames."""
    w = ResultsWriter(out, run_id)
    for r in rows:
        w.write(r) if isinstance(r, pd.DataFrame) else w.add(r)
    return w.close(csv_full=csv)
