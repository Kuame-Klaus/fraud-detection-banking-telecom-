"""Step 2: data quality and reconciliation checks. Returns dq rows in the shared schema."""
from __future__ import annotations

import pandas as pd

KEYS = {"B1_transactions": "txn_id", "B4_auth_events": "event_id", "B7_gl_journal": "line_id",
        "B9_cards_and_authorisations": "auth_id", "B10_vendors_and_payments": "payment_id", "B2_accounts": "account_id",
        "B3_persons": "person_id", "T1_cdrs": "cdr_id", "T3_sims_and_sim_swap_events": "swap_id",
        "T4_momo_wallet_txns": "txn_id", "T2_subscribers": "msisdn", "T5_wallets": "wallet_id"}
TIME = {"B1_transactions": "timestamp", "B4_auth_events": "timestamp", "B7_gl_journal": "entry_timestamp",
        "T1_cdrs": "start_time", "T4_momo_wallet_txns": "timestamp", "T3_sims_and_sim_swap_events": "swap_time",
        "T7_topups_billing": "event_time", "T6_agents": "movement_time"}


def checks(dataset_id: str, name: str, domain: str, df: pd.DataFrame, ctl: dict) -> list[dict]:
    rows = []

    def add(step, check, expected, observed, passed, note=""):
        rows.append({"record_type": "dq", "domain": domain, "dataset_id": dataset_id, "step": step,
                     "check_name": check, "expected": str(expected), "observed": str(observed),
                     "passed": bool(passed), "note": note})

    add(1, "row_count_control_total", ctl["rows"], len(df), ctl["rows"] == len(df), "SYNTHETIC; recount after load")
    if ctl.get("amount_col"):
        s = float(df[ctl["amount_col"]].sum())
        add(1, f"sum_{ctl['amount_col']}_control_total", round(ctl["amount_sum"], 2), round(s, 2), abs(s - ctl["amount_sum"]) < 0.01)
    key = KEYS.get(name)
    if key and key in df:
        d = int(df[key].duplicated().sum())
        add(3, f"duplicate_{key}", 0, d, d == 0)
    nulls = int(df.drop(columns=[c for c in df.columns if c in ("synthetic_scenario", "original_txn_id", "reversal_of", "exit_date", "invoice_status", "limit_value", "threshold_value")]).isna().sum().sum())
    add(3, "null_cells", 0, nulls, nulls == 0, "optional columns excluded")
    t = TIME.get(name)
    if t and t in df:
        lo, hi = df[t].min(), df[t].max()
        add(4, f"{t}_range", "2025-01-01 to 2026-01-31", f"{lo} to {hi}",
            bool(lo >= pd.Timestamp("2024-12-31")) and bool(hi <= pd.Timestamp("2026-02-01")), "timezone UTC ASSUMPTION")
        for m, c in df[t].dt.strftime("%Y-%m").value_counts().sort_index().items():
            rows.append({"record_type": "dq", "domain": domain, "dataset_id": dataset_id, "step": 4, "month": m,
                         "check_name": "monthly_row_count", "expected": "", "observed": str(int(c)), "passed": True})
    if "amount" in df:
        neg = int((df["amount"] < 0).sum())
        add(3, "negative_amount", 0, neg, neg == 0)
    if {"balance_before", "balance_after", "amount"} <= set(df.columns):
        diff = (df["balance_after"] - df["balance_before"]).abs().round(2)
        bad = int((diff - df["amount"].round(2)).abs().gt(0.02).sum())
        add(5, "balance_continuity", 0, bad, bad == 0)
    return rows
