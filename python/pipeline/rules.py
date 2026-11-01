"""Step 4: transparent scenario rules. Each returns a boolean flag per row of its table.
Thresholds are ASSUMPTION defaults, not client parameters."""
from __future__ import annotations

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


@rule("interconnect_leakage", "R_T08", "T1", "route", "route", "start_time", "duration_sec")
def leak(d):
    return d["route"].isin(d.attrs.get("leaky_routes", []))


@rule("insider_sim_swap_or_access_abuse", "R_T09", "T3", "performed_by_user", "user", "swap_time", None)
def insider(d):
    night = d["swap_time"].dt.hour < 5
    c = night.groupby(d["performed_by_user"]).transform("sum")
    return night & (c >= c.quantile(0.999))


@rule("imei_churn", "R_T10", "T3", "msisdn", "msisdn", "swap_time", None)
def imei(d):
    return d.groupby("msisdn")["swap_id"].transform("size") >= 4


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
