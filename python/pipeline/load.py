"""Step 1: find SYNTHETIC (or local full) datasets and stream them one chunk at a time.

A chunk is one manifest part (data/full), one Parquet part file (data/synthetic/<mode>) or one CSV file
(data/sample). Nothing reads a whole large table into memory here."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

AMOUNT_COLS = {"B1_transactions": "amount", "B7_gl_journal": "debit", "B9_cards_and_authorisations": "amount",
               "B10_vendors_and_payments": "payment_amount", "B11_payroll_and_hr": "pay_amount",
               "T1_cdrs": "duration_sec", "T4_momo_wallet_txns": "amount", "T6_agents": "float_amount",
               "T7_topups_billing": "amount", "T8_interconnect_traffic": "minutes"}


def _fix_csv(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        if c.endswith(("timestamp", "_time", "_date", "_at")) or c in ("timestamp", "dob", "last_seen", "first_seen"):
            df[c] = pd.to_datetime(df[c], errors="coerce", utc=True).dt.tz_localize(None)
    if "synthetic_scenario" in df:
        df["synthetic_scenario"] = df["synthetic_scenario"].fillna("")
    if "response_code" in df:  # CSV readers turn "00" into 0; keep the code as a two character string like the Parquet data
        df["response_code"] = df["response_code"].astype("Int64").astype(str).str.zfill(2)
    for c in ("original_txn_id", "reversal_of"):
        if c in df:
            df[c] = df[c].fillna("")
    return df


class Source:
    def __init__(self, data_dir: Path):
        self.dir = Path(data_dir)
        mf = self.dir / "manifest.json"
        self.manifest = json.loads(mf.read_text())["datasets"] if mf.exists() else None
        self.datasets: dict[str, tuple[str, list[Path]]] = {}
        for domain in ("banking", "telecom"):
            d = self.dir / domain
            if not d.exists():
                continue
            for p in sorted(d.iterdir()):
                if p.suffix == ".csv":
                    self.datasets[p.stem] = (domain, [p])
                elif p.is_dir():
                    if self.manifest and p.name in self.manifest:
                        parts = [self.dir / x["path"] for x in self.manifest[p.name]["parts"]]
                    else:
                        parts = sorted(p.glob("*.parquet"))
                    self.datasets[p.name] = (domain, parts)

    def expected_rows(self, name: str):
        return self.manifest[name]["rows"] if self.manifest and name in self.manifest else None

    def rows(self, name: str) -> int:
        e = self.expected_rows(name)
        if e is not None:
            return e
        return sum(pq.ParquetFile(p).metadata.num_rows if p.suffix == ".parquet" else
                   sum(1 for _ in open(p)) - 1 for p in self.datasets[name][1])

    def chunks(self, name: str, columns=None):
        for p in self.datasets[name][1]:
            if p.suffix == ".csv":
                yield _fix_csv(pd.read_csv(p, usecols=columns, keep_default_na=False, na_values=[""], low_memory=False))
            else:
                yield pd.read_parquet(p, columns=columns)

    def read_all(self, name: str, columns=None) -> pd.DataFrame:
        """Only for small dimension tables (B2, B8, T3, T5, T8)."""
        return pd.concat(list(self.chunks(name, columns)), ignore_index=True)


def read_manifest_dataset(full_dir: Path, name: str, verify: bool = False, columns=None) -> pd.DataFrame:
    """Combine every part listed in data/full/manifest.json for one dataset (optionally checking SHA256)."""
    m = json.loads((Path(full_dir) / "manifest.json").read_text())["datasets"][name]
    frames = []
    for p in m["parts"]:
        f = Path(full_dir) / p["path"]
        if verify and hashlib.sha256(f.read_bytes()).hexdigest() != p["sha256"]:
            raise ValueError(f"checksum mismatch: {f}")
        frames.append(pd.read_parquet(f, columns=columns))
    df = pd.concat(frames, ignore_index=True)
    if len(df) != m["rows"] and columns is None:
        raise ValueError(f"{name}: expected {m['rows']} rows, read {len(df)}")
    return df
