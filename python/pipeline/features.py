"""Step 3: features for the event tables B1 and T4 (vectorised, one pass per table)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _entity_window(df, ent, t, amt):
    df = df.sort_values([ent, t]).copy()
    g = df.groupby(ent, sort=False)
    gap = g[t].diff().dt.total_seconds().fillna(1e7)
    df["secs_since_prev"] = gap.clip(upper=1e7)
    df["secs_to_next"] = (-g[t].diff(-1).dt.total_seconds()).fillna(1e7).clip(upper=1e7)
    df["day"] = df[t].dt.floor("D")
    df["ent_day_count"] = df.groupby([ent, "day"])[amt].transform("size")
    df["ent_day_sum"] = df.groupby([ent, "day"])[amt].transform("sum")
    m = g[amt].transform("mean"); s = g[amt].transform("std").fillna(0)
    df["amount_z"] = ((df[amt] - m) / (s + 1)).astype(float)
    df["ent_count"] = g[amt].transform("size")
    return df


def first_digit(x):
    x = np.abs(np.asarray(x, dtype=float))
    x = x[x >= 1]
    return (x / 10 ** np.floor(np.log10(x))).astype(int)


def prior_swap_hours(ms: pd.Series, ts: pd.Series, swaps: pd.DataFrame) -> np.ndarray:
    """Hours from the latest swap of the same msisdn at or before each timestamp (an as of join), 100,000 when none.
    One combined sort of swaps and transactions by (msisdn code, time, swap first on ties), then a forward fill
    of the last swap position within each msisdn. Same result as pandas merge_asof(direction="backward")."""
    sw = swaps[["msisdn", "swap_time"]].dropna()
    st = pd.to_datetime(sw["swap_time"]).astype(ts.dtype).to_numpy().view("int64")
    cats = pd.Index(sw["msisdn"].unique())
    sc = cats.get_indexer(sw["msisdn"]); tc = cats.get_indexer(ms.fillna("").to_numpy())
    tt = ts.to_numpy().view("int64"); n_s, n_t = len(st), len(tt)
    code = np.concatenate([sc, tc]); tim = np.concatenate([st, tt])
    kind = np.concatenate([np.zeros(n_s, np.int8), np.ones(n_t, np.int8)])  # swap sorts before a transaction at the same time
    o = np.lexsort((kind, tim, code))
    pos = np.where(kind[o] == 0, np.arange(len(o)), -1)
    first = np.r_[True, code[o][1:] != code[o][:-1]]  # reset at each msisdn
    seg = np.maximum.accumulate(np.where(first, np.arange(len(o)), 0))
    last = np.maximum.accumulate(pos)
    last = np.where(last >= seg, last, -1)
    h = np.full(n_t, 1e5)
    it = o >= n_s; ti = o[it] - n_s; lt = last[it]
    okk = (lt >= 0) & (tc[ti] >= 0)
    unit = np.datetime_data(ts.to_numpy().dtype)[0]
    h[ti[okk]] = (tt[ti[okk]] - tim[o[lt[okk]]]).astype(f"timedelta64[{unit}]") / np.timedelta64(1, "h")
    return np.clip(h, None, 1e5)


def banking_features(b1: pd.DataFrame, b2: pd.DataFrame) -> pd.DataFrame:
    df = _entity_window(b1, "account_id", "timestamp", "amount")
    df["hour"] = df["timestamp"].dt.hour; df["weekday"] = df["timestamp"].dt.weekday
    df["log_amount"] = np.log1p(df["amount"])
    df["near_threshold"] = ((df["amount"] >= 9000) & (df["amount"] < 10000)).astype(int)
    df["declined"] = (df["response_code"] != "00").astype(int)
    df["is_debit"] = (df["direction"] == "debit").astype(int)
    df["foreign"] = (df["country"] != "GH").astype(int)
    df["country_change_fast"] = ((df.groupby("account_id")["country"].shift() != df["country"]) & (df["secs_since_prev"] < 3600)).astype(int)
    lead = np.zeros(len(df), dtype=int); a = df["amount"].to_numpy(); ok = a >= 1
    lead[ok] = (a[ok] / 10 ** np.floor(np.log10(a[ok]))).astype(int); df["lead_digit"] = lead
    df["merch_day_count"] = df.groupby(["merchant_id", "account_id", "day"])["amount"].transform("size")
    acc = b2.set_index("account_id")
    df["acct_dormant"] = df["account_id"].map(acc["status"].eq("dormant")).fillna(False).astype(int)
    df["amount_vs_expected"] = df["amount"] / df["account_id"].map(acc["expected_monthly_volume"]).fillna(1000)
    for c, v in {"channel": ["card", "mobile", "web", "branch", "atm"]}.items():
        for x in v:
            df[f"{c}_{x}"] = (df[c] == x).astype(int)
    return df


BANK_FEATURES = ["log_amount", "hour", "weekday", "secs_since_prev", "secs_to_next", "ent_day_count", "ent_day_sum",
                 "amount_z", "ent_count", "near_threshold", "declined", "is_debit", "foreign", "country_change_fast",
                 "lead_digit", "merch_day_count", "acct_dormant", "amount_vs_expected", "reversal_flag",
                 "channel_card", "channel_mobile", "channel_web", "channel_branch", "channel_atm"]


def telecom_features(t4: pd.DataFrame, t5: pd.DataFrame, last_swap: pd.Series, agent_day: pd.Series | None = None,
                     swaps: pd.DataFrame | None = None) -> pd.DataFrame:
    """last_swap: latest swap_time per msisdn from T3. agent_day: global row count per (agent_id, day),
    built incrementally across chunks, so a wallet bucket still sees each agent's whole day."""
    df = _entity_window(t4, "wallet_id", "timestamp", "amount")
    df["hour"] = df["timestamp"].dt.hour; df["weekday"] = df["timestamp"].dt.weekday
    df["log_amount"] = np.log1p(df["amount"])
    w = t5.set_index("wallet_id")
    df["wallet_limit"] = df["wallet_id"].map(w["wallet_limit"]).astype(float)
    df["over_tier"] = (df["amount"] > df["wallet_limit"]).astype(int)
    df["wallet_dormant"] = df["wallet_id"].map(w["status"].eq("dormant")).fillna(False).astype(int)
    df["round_amount"] = (df["amount"] % 100 == 0).astype(int)
    df["has_reversal"] = df["reversal_of"].fillna("").ne("").astype(int)
    if agent_day is None:
        df["agent_day_count"] = df.groupby(["agent_id", "day"])["amount"].transform("size")
    else:
        idx = pd.MultiIndex.from_arrays([df["agent_id"], df["day"]])
        df["agent_day_count"] = agent_day.reindex(idx).fillna(0).to_numpy()
    # hours since the latest SIM swap on the wallet's msisdn (within domain only)
    ms = df["wallet_id"].map(w["msisdn"])
    swap_t = ms.map(last_swap)
    hrs = (df["timestamp"] - swap_t).dt.total_seconds() / 3600
    df["hours_since_swap"] = hrs.where(hrs >= 0, 1e5).fillna(1e5).clip(upper=1e5)
    if swaps is not None:  # latest swap at or before each transaction (used by R_T01)
        df["hours_since_prior_swap"] = prior_swap_hours(ms, df["timestamp"], swaps)
    else:
        df["hours_since_prior_swap"] = df["hours_since_swap"]
    for x in ["p2p", "cash_in", "cash_out", "merchant", "airtime"]:
        df[f"type_{x}"] = (df["type"] == x).astype(int)
    return df


TEL_FEATURES = ["log_amount", "hour", "weekday", "secs_since_prev", "secs_to_next", "ent_day_count", "ent_day_sum",
                "amount_z", "ent_count", "wallet_limit", "over_tier", "wallet_dormant", "round_amount", "has_reversal",
                "agent_day_count", "hours_since_swap", "type_p2p", "type_cash_in", "type_cash_out", "type_merchant", "type_airtime"]
