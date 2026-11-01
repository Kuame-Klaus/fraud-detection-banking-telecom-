"""Step 1: load SYNTHETIC (or local full) data and compute control totals."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

AMOUNT_COLS = {"B1_transactions": "amount", "B7_gl_journal": "debit", "B9_cards_and_authorisations": "amount",
               "B10_vendors_and_payments": "payment_amount", "B11_payroll_and_hr": "pay_amount",
               "T1_cdrs": "duration_sec", "T4_momo_wallet_txns": "amount", "T6_agents": "float_amount",
               "T7_topups_billing": "amount", "T8_interconnect_traffic": "minutes"}


def discover(data_dir: Path) -> dict[str, tuple[str, Path]]:
    """Map dataset name to (domain, path). Accepts Parquet part folders or single CSV files."""
    found = {}
    for domain in ("banking", "telecom"):
        d = data_dir / domain
        if not d.exists():
            continue
        for p in sorted(d.iterdir()):
            name = p.stem if p.suffix == ".csv" else p.name
            found[name] = (domain, p)
    return found


def read(path: Path, columns=None) -> pd.DataFrame:
    if path.suffix == ".csv":
        df = pd.read_csv(path, usecols=columns, keep_default_na=False, na_values=[""], low_memory=False)
        for c in df.columns:
            if c.endswith(("timestamp", "_time", "_date", "_at")) or c in ("timestamp", "dob", "last_seen", "first_seen"):
                df[c] = pd.to_datetime(df[c], errors="coerce", utc=True).dt.tz_localize(None)
        if "synthetic_scenario" in df:
            df["synthetic_scenario"] = df["synthetic_scenario"].fillna("")
        return df
    return pd.read_parquet(path, columns=columns)


def control_totals(name: str, df: pd.DataFrame) -> dict:
    col = AMOUNT_COLS.get(name)
    return {"rows": len(df), "amount_col": col or "", "amount_sum": float(df[col].sum()) if col else None}
