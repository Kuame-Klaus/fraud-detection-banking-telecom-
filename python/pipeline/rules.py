"""Step 4: transparent scenario rules. Each returns a boolean flag per row of its table.
Thresholds are ASSUMPTION defaults, not client parameters."""
from __future__ import annotations
import numpy as np

import pandas as pd

# (scenario, rule_id, table, entity column, entity type, time column, amount column, function)
RULES = []


def rule(scenario, rule_id, table, ent, etype, tcol, acol):
    def deco(f):
        RULES.append((scenario, rule_id, table, ent, etype, tcol, acol, f))
        return f
    return deco


@rule("card_testing", "R_B01", "B1", "account_id", "account", "timestamp", "amount")
def card_testing(d):
    return (d["amount"] < 10) & (d["merch_day_count"] >= 10) & (d["channel"] == "card")


@rule("structuring", "R_B02", "B1", "account_id", "account", "timestamp", "amount")
def structuring(d):
    c = d.groupby("account_id")["near_threshold"].transform("sum")
    return (d["near_threshold"] == 1) & (c >= 3)


@rule("mule_network", "R_B03", "B1", "account_id", "account", "timestamp", "amount")
def mule(d):
    big_in = (d["direction"] == "credit") & (d["amount"] > 4000) & (d["secs_to_next"] < 3600)
    fast_out = (d["direction"] == "debit") & (d["secs_since_prev"] < 3600) & (d["ent_day_count"] >= 5)
    return big_in | fast_out


@rule("dormant_account_wake_up", "R_B04", "B1", "account_id", "account", "timestamp", "amount")
def dormant(d):
    return (d["acct_dormant"] == 1) & (d["amount"] > 5000)


@rule("kyc_mismatch_expected_volume", "R_B05", "B1", "account_id", "account", "timestamp", "amount")
def kyc(d):
    return d["amount_vs_expected"] > 20


@rule("impossible_travel", "R_B06", "B1", "account_id", "account", "timestamp", "amount")
def travel(d):
    return d["country_change_fast"] == 1


@rule("reversal_abuse", "R_B07", "B1", "account_id", "account", "timestamp", "amount")
def reversal(d):
    return (d["reversal_flag"] == 1) & (d.groupby("account_id")["reversal_flag"].transform("sum") >= 3)


@rule("account_takeover", "R_B08", "B1", "account_id", "account", "timestamp", "amount")
def ato_txn(d):
    return (d["channel"] == "web") & (d["amount"] > 2500) & (d["secs_since_prev"] < 1800)


@rule("account_takeover", "R_B09", "B4", "person_id", "person", "timestamp", None)
def ato_auth(d):
    d = d.sort_values(["person_id", "timestamp"])
    reset = d["event_type"].eq("password_reset")
    near = reset.groupby(d["person_id"]).transform(lambda s: s.rolling(5, center=True, min_periods=1).max())
    fails = d["event_type"].eq("login_failed").groupby(d["person_id"]).transform("sum")
    return (near > 0) & (fails >= 2) & d["geo"].ne("GH")


@rule("journal_abuse", "R_B10", "B7", "preparer_id", "user", "entry_timestamp", "debit")
def journal(d):
    amt = d["debit"] + d["credit"]
    return d["is_manual"] & (amt % 10000 == 0) & (amt > 0) & ((d["entry_timestamp"].dt.weekday >= 5) | (d["entry_timestamp"].dt.hour < 5))


@rule("segregation_of_duties", "R_B11", "B7", "preparer_id", "user", "entry_timestamp", "debit")
def sod(d):
    return d["preparer_id"] == d["approver_id"]


@rule("ghost_vendor_or_employee", "R_B13", "B10", "vendor_id", "vendor", "payment_date", "payment_amount")
def ghost(d):
    return d["vendor_bank_account"].str.startswith("BEBANK")


@rule("duplicate_vendor_payments", "R_B14", "B10", "vendor_id", "vendor", "payment_date", "payment_amount")
def dup(d):
    d = d.sort_values("payment_date")
    return d.duplicated(["vendor_id", "payment_amount"], keep="first")


@rule("payroll_after_exit", "R_B15", "B11", "employee_id", "employee", "pay_date", "pay_amount")
def payroll(d):
    return d["exit_date"].notna() & (d["pay_date"] > d["exit_date"]) & (d["pay_amount"] > 0)


@rule("sim_swap_fraud", "R_T01", "T4", "wallet_id", "wallet", "timestamp", "amount")
def simswap(d):
    return (d["hours_since_swap"] < 24) & (d["type"] == "cash_out")


@rule("wallet_tier_breach", "R_T02", "T4", "wallet_id", "wallet", "timestamp", "amount")
def tier(d):
    return d["over_tier"] == 1


@rule("dormant_wallet_drain", "R_T03", "T4", "wallet_id", "wallet", "timestamp", "amount")
def dwallet(d):
    return (d["wallet_dormant"] == 1) & (d["type"] == "cash_out") & (d["amount"] > 500)


@rule("agent_fraud", "R_T04", "T4", "agent_id", "agent", "timestamp", "amount")
def agent(d):
    return (d["type"] == "cash_in") & (d["round_amount"] == 1) & (d["agent_day_count"] >= 8)


@rule("sim_box_and_bypass", "R_T05", "T1", "caller", "msisdn", "start_time", "duration_sec")
def simbox(d):
    day = d["start_time"].dt.floor("D")
    c = d.groupby(["caller", day])["cdr_id"].transform("size")
    return (d["call_type"] == "voice") & (c >= 20) & (d["duration_sec"] < 150)


@rule("wangiri", "R_T06", "T1", "caller", "msisdn", "start_time", "duration_sec")
def wangiri(d):
    short = d["duration_sec"] <= 3
    return short & (short.groupby(d["caller"]).transform("sum") >= 10)


@rule("subscription_and_bust_out", "R_T07", "T1", "caller", "msisdn", "start_time", "duration_sec")
def bust(d):
    return (d["duration_sec"] >= 1800) & d["roaming_flag"].astype(bool)


def leak(d):
    """Version 1 of R_T08 (every T1 call on a leaky route). Kept for reference; R_T08 now runs at route and day level."""
    return d["route"].isin(d.attrs.get("leaky_routes", []))


LEAK_MIN_UNSETTLED_SHARE = 0.35  # ASSUMPTION
LEAK_RATE_VS_MEDIAN = 0.6        # ASSUMPTION


def leak_route_day(t1_route_day_minutes: pd.Series, t8: pd.DataFrame) -> pd.DataFrame:
    """R_T08 at route and day level. One row per route day that has a T8 settlement row.
    unsettled_minutes = T1 minutes minus T8 settled minutes; settlement_rate = settlement amount per settled minute.
    Flag when the unsettled share is at least 0.35 and the rate is below 0.6 times the median rate.
    Route days with T1 traffic but no T8 row are counted separately (no_settlement_row), not flagged."""
    t8 = t8.assign(day=pd.to_datetime(t8["traffic_date"], utc=True).dt.strftime("%Y-%m-%d"))
    g = t8.groupby(["route", "day"]).agg(settled_minutes=("minutes", "sum"), settlement_amount=("settlement_amount", "sum"),
                                          synthetic_scenario=("synthetic_scenario", "max"))
    g = g.join(t1_route_day_minutes.rename("t1_minutes"), how="left").fillna({"t1_minutes": 0.0}).reset_index()
    g["synthetic_scenario"] = g["synthetic_scenario"].fillna("").astype(str)
    g["unsettled_minutes"] = g["t1_minutes"] - g["settled_minutes"]
    g["unsettled_share"] = np.where(g["t1_minutes"] > 0, g["unsettled_minutes"] / g["t1_minutes"].where(g["t1_minutes"] > 0, 1), 0.0)
    g["settlement_rate"] = g["settlement_amount"] / g["settled_minutes"].where(g["settled_minutes"] > 0, np.nan)
    med = g["settlement_rate"].median()
    g["flag"] = (g["unsettled_share"] >= LEAK_MIN_UNSETTLED_SHARE) & (g["settlement_rate"] < LEAK_RATE_VS_MEDIAN * med)
    g.attrs["no_settlement_row"] = int(len(set(t1_route_day_minutes.index) - set(zip(g["route"], g["day"]))))
    return g


@rule("insider_sim_swap_or_access_abuse", "R_T09", "T3", "performed_by_user", "user", "swap_time", None)
def insider(d):
    """5 or more night swaps (00:00 to 05:00 UTC) by one user on one night. ASSUMPTION threshold."""
    night = d["swap_time"].dt.hour < 5
    c = night.groupby([d["performed_by_user"], d["swap_time"].dt.floor("D")]).transform("sum")
    return night & (c >= 5)


@rule("imei_churn", "R_T10", "T3", "msisdn", "msisdn", "swap_time", None)
def imei(d):
    """4 or more swaps on one number within 30 days. ASSUMPTION threshold."""
    x = d.sort_values(["msisdn", "swap_time"])
    g = x.groupby("msisdn")["swap_time"]
    start = (g.shift(-3) - x["swap_time"]) <= pd.Timedelta(days=30)
    flag = start.copy()
    for k in (1, 2, 3):
        flag |= start.groupby(x["msisdn"]).shift(k).fillna(False).astype(bool)
    return flag.reindex(d.index)


@rule("recharge_fraud", "R_T11", "T7", "msisdn", "msisdn", "event_time", "amount")
def recharge(d):
    day = d["event_time"].dt.floor("D")
    c = d.groupby(["msisdn", day])["amount"].transform("size")
    return (d["event_type"] == "topup") & (c >= 8)


@rule("subscription_and_bust_out", "R_T12", "T7", "msisdn", "msisdn", "event_time", "amount")
def baddebt(d):
    return d["bad_debt_amount"] > 1000


@rule("agent_float_anomalies", "R_T13", "T6", "agent_id", "agent", "movement_time", "float_amount")
def flt(d):
    return (d["movement_time"].dt.hour < 5) & (d["float_amount"] > 30000)


def leaky_routes(t1: pd.DataFrame, t8: pd.DataFrame) -> list[str]:
    """Routes whose settled share of T1 minutes is far below the median (join by route only; no carrier in T1)."""
    m = t1.groupby("route")["duration_sec"].sum() / 60
    s = t8.groupby("route")["settlement_amount"].sum() / t8.groupby("route")["minutes"].sum()
    ratio = s.reindex(m.index)
    return list(ratio[ratio < 0.6 * ratio.median()].index)


@rule("benford_anomaly", "R_B16", "B1", "account_id", "account", "timestamp", "amount")
def benford(d):
    return d["lead_digit"].isin([7, 8]) & (d["amount"] >= 700) & (d["amount"] < 9000)


@rule("privileged_access_before_journals", "R_B12", "B7", "preparer_id", "user", "entry_timestamp", "debit")
def privileged(d):
    return d["preparer_id"].isin(d.attrs.get("privileged_users", [])) & d["is_manual"]


def leaky_routes_from(t1_minutes_by_route: pd.Series, t8: pd.DataFrame) -> list[str]:
    """Same test as leaky_routes, from T1 minutes per route summed incrementally across chunks."""
    s = t8.groupby("route")["settlement_amount"].sum() / t8.groupby("route")["minutes"].sum()
    ratio = s.reindex(t1_minutes_by_route.index)
    return list(ratio[ratio < 0.6 * ratio.median()].index)


# ---------------------------------------------------------------------------
# PROPOSED versions (docs/threshold_proposals.md). Not the default: used only with run.py --rules proposed,
# until Klaus Konsults approves them.
FAR = {"GB", "US"}  # ASSUMPTION: countries not reachable from GH within 30 minutes


def travel_proposed(d):
    d2 = d.sort_values(["account_id", "timestamp"])
    g = d2.groupby("account_id", sort=False)
    prev_c = g["country"].shift(); prev_ch = g["channel"].shift(); prev_rc = g["response_code"].shift()
    gap = g["timestamp"].diff().dt.total_seconds()
    pair = ((d2["country"] != prev_c) & (gap <= 1800) & (d2["channel"] == "card") & (prev_ch == "card")
            & (d2["response_code"] == "00") & (prev_rc == "00")
            & (d2["country"].isin(FAR) | prev_c.isin(FAR)) & (d2["country"].eq("GH") | prev_c.eq("GH")))
    flag = pair | pair.groupby(d2["account_id"], sort=False).shift(-1, fill_value=False)  # also the first row of the pair
    return flag.reindex(d.index)


def ato_auth_proposed(d):
    """2 or more failed logins, then a password reset, within 15 minutes, from abroad; flag every event in that window."""
    d2 = d.sort_values(["person_id", "timestamp"])
    t = d2["timestamp"].astype("int64") // 10**9; p = d2["person_id"]
    fail = d2["event_type"].eq("login_failed").astype(int); reset = d2["event_type"].eq("password_reset")
    def win(s, w):  # count in the 900 s before each row, per person
        x = pd.Series(s.to_numpy(), index=pd.to_datetime(t.to_numpy(), unit="s"))
        return x.groupby(p.to_numpy()).rolling(f"{w}s").sum().reset_index(level=0, drop=True).to_numpy()
    fails_before = win(fail, 900)
    anchor = pd.Series(reset.to_numpy() & (fails_before >= 2) & d2["geo"].ne("GH").to_numpy(), index=d2.index)
    # mark rows within 15 minutes before and after an anchor on the same person
    at = pd.Series(np.where(anchor, t, np.nan), index=d2.index)
    nxt = at.groupby(p).bfill(); prv = at.groupby(p).ffill()
    flag = ((nxt - t).between(0, 900) | (t - prv).between(0, 900)) & d2["geo"].ne("GH")
    return flag.reindex(d.index)


def benford_proposed(d):
    """First two digits 70, 71, 80 or 81 in 700 to 899 or 7,000 to 8,999. ASSUMPTION, see risks in the proposal doc."""
    a = d["amount"].to_numpy(dtype=float); ok = a >= 10
    two = np.zeros(len(a), dtype=int)
    two[ok] = (a[ok] / 10 ** (np.floor(np.log10(a[ok])) - 1)).astype(int)
    band = ((a >= 700) & (a < 900)) | ((a >= 7000) & (a < 9000))
    return pd.Series(np.isin(two, [70, 71, 80, 81]) & band, index=d.index)


def simswap_proposed(d):
    """Cash out within 24 hours after the latest swap at or before the transaction (not the latest swap overall)."""
    return (d["hours_since_prior_swap"] < 24) & (d["type"] == "cash_out")


PROPOSED = {"R_B06": travel_proposed, "R_B09": ato_auth_proposed, "R_T01": simswap_proposed}
# benford_proposed was measured and rejected (sample recall 0.1); see docs/threshold_proposals.md
