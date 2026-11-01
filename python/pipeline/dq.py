"""Step 2: data quality and reconciliation checks, accumulated one chunk at a time."""
from __future__ import annotations

import numpy as np
import pandas as pd

KEYS = {"B1_transactions": "txn_id", "B4_auth_events": "event_id", "B7_gl_journal": "line_id",
        "B9_cards_and_authorisations": "auth_id", "B10_vendors_and_payments": "payment_id", "B2_accounts": "account_id",
        "B3_persons": "person_id", "T1_cdrs": "cdr_id", "T3_sims_and_sim_swap_events": "swap_id",
        "T4_momo_wallet_txns": "txn_id", "T2_subscribers": "msisdn", "T5_wallets": "wallet_id"}
TIME = {"B1_transactions": "timestamp", "B4_auth_events": "timestamp", "B7_gl_journal": "entry_timestamp",
        "T1_cdrs": "start_time", "T4_momo_wallet_txns": "timestamp", "T3_sims_and_sim_swap_events": "swap_time",
        "T7_topups_billing": "event_time", "T6_agents": "movement_time"}
OPTIONAL = {"synthetic_scenario", "original_txn_id", "reversal_of", "exit_date", "invoice_status", "limit_value", "threshold_value"}


class DQ:
    def __init__(self, dataset_id: str, name: str, domain: str, amount_col: str | None, expected_rows: int | None):
        self.id, self.name, self.domain, self.acol, self.expected = dataset_id, name, domain, amount_col, expected_rows
        self.rows = 0; self.amount = 0.0; self.nulls = 0; self.neg = 0; self.bal_bad = 0
        self.key_hashes = []; self.tmin = None; self.tmax = None; self.months = {}
        self.has_amount = self.has_bal = False

    def update(self, df: pd.DataFrame) -> None:
        self.rows += len(df)
        if self.acol:
            self.amount += float(df[self.acol].sum())
        key = KEYS.get(self.name)
        if key and key in df:
            self.key_hashes.append(pd.util.hash_pandas_object(df[key], index=False).to_numpy())
        self.nulls += int(df.drop(columns=[c for c in df.columns if c in OPTIONAL]).isna().sum().sum())
        t = TIME.get(self.name)
        if t and t in df:
            lo, hi = df[t].min(), df[t].max()
            self.tmin = lo if self.tmin is None else min(self.tmin, lo)
            self.tmax = hi if self.tmax is None else max(self.tmax, hi)
            for m, c in df[t].dt.strftime("%Y-%m").value_counts().items():
                self.months[m] = self.months.get(m, 0) + int(c)
        if "amount" in df:
            self.has_amount = True; self.neg += int((df["amount"] < 0).sum())
        if {"balance_before", "balance_after", "amount"} <= set(df.columns):
            self.has_bal = True
            diff = (df["balance_after"] - df["balance_before"]).abs().round(2)
            self.bal_bad += int((diff - df["amount"].round(2)).abs().gt(0.02).sum())

    def finish(self) -> list[dict]:
        rows = []

        def add(step, check, expected, observed, passed, note="", month=None):
            r = {"record_type": "dq", "domain": self.domain, "dataset_id": self.id, "step": step, "check_name": check,
                 "expected": str(expected), "observed": str(observed), "passed": bool(passed), "note": note}
            if month:
                r["month"] = month
            rows.append(r)

        exp = self.expected if self.expected is not None else self.rows
        add(1, "row_count_control_total", exp, self.rows, exp == self.rows,
            "expected from data/full/manifest.json" if self.expected is not None else "SYNTHETIC; no manifest, count recorded")
        if self.acol:
            add(1, f"sum_{self.acol}_control_total", "", round(self.amount, 2), True,
                "recorded; no source system control total exists for SYNTHETIC data")
        if self.key_hashes:
            h = np.concatenate(self.key_hashes); d = int(len(h) - len(np.unique(h)))
            add(3, f"duplicate_{KEYS[self.name]}", 0, d, d == 0)
        add(3, "null_cells", 0, self.nulls, self.nulls == 0, "optional columns excluded")
        t = TIME.get(self.name)
        if self.tmin is not None:
            add(4, f"{t}_range", "2025-01-01 to 2026-01-31", f"{self.tmin} to {self.tmax}",
                bool(self.tmin >= pd.Timestamp("2024-12-31")) and bool(self.tmax <= pd.Timestamp("2026-02-01")), "timezone UTC ASSUMPTION")
            for m in sorted(self.months):
                add(4, "monthly_row_count", "", self.months[m], True, month=m)
        if self.has_amount:
            add(3, "negative_amount", 0, self.neg, self.neg == 0)
        if self.has_bal:
            add(5, "balance_continuity", 0, self.bal_bad, self.bal_bad == 0)
        return rows
