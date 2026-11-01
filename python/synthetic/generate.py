"""Seeded SYNTHETIC data generator for the Klaus Konsults fraud detection project.

Every row written here is synthetic. No real customer or client data is used.
Banking (B1 to B14) and telecom (T1 to T12) are generated as two separate
entities: they share no keys and no identifiers.

Column names follow docs/data_dictionary.md. Planted fraud rows carry the
scenario name in the label column (synthetic_scenario); other rows hold "".

Usage:
    python -m python.synthetic.generate --mode sample   # 1/1000 scale
    python -m python.synthetic.generate --mode full     # config row counts
"""
from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).resolve().parent / "config.yaml"
LABEL = "synthetic_scenario"
# ASSUMPTION values used only to shape synthetic data
PERIOD_START = np.datetime64("2025-01-01T00:00:00")
PERIOD_SECONDS = 365 * 86400
STRUCTURING_THRESHOLD = 10000.0  # ASSUMPTION reporting threshold
PLANT_SHARE = 0.0005  # ASSUMPTION share of event rows per planted scenario
CURRENCY_B = "GHS"
COUNTRIES = np.array(["GH", "GH", "GH", "GH", "NG", "CI", "TG", "GB", "US"])


def load_config() -> dict:
    with open(CONFIG) as f:
        return yaml.safe_load(f)


class Writer:
    """Writes one dataset as chunked Parquet parts under data/synthetic/<domain>/<id>/."""

    def __init__(self, out: Path, domain: str, name: str):
        self.dir = out / domain / name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.part = 0
        self.rows = 0

    def write(self, df: pd.DataFrame) -> None:
        if LABEL not in df:
            df[LABEL] = ""
        df["synthetic"] = True
        pq.write_table(pa.Table.from_pandas(df, preserve_index=False),
                       self.dir / f"synthetic_part_{self.part:05d}.parquet")
        self.part += 1
        self.rows += len(df)


def ts(rng, n, start=PERIOD_START, span=PERIOD_SECONDS):
    sec = rng.integers(0, span, n)
    return start + sec.astype("timedelta64[s]")


def ids(prefix, idx):
    return pd.Series(idx).map(lambda i: f"{prefix}{i:09d}").to_numpy(copy=True)


def ids_fast(prefix, idx):
    return np.char.add(prefix, np.char.zfill(np.asarray(idx).astype(str), 9))


def plant_blocks(rng, n, share, block):
    """Return start indices of contiguous blocks covering about share*n rows."""
    k = max(1, int(n * share / block))
    if n <= block:
        return np.array([0])
    return rng.choice(np.arange(0, n - block, block), size=min(k, (n - block) // block), replace=False)


# ---------------------------------------------------------------- banking
def gen_banking(cfg, scale, out, rng, chunk):
    R = {k: max(1, int(v * scale)) for k, v in cfg["rows"]["banking"].items()}
    counts = {}
    n_acc, n_per = R["B2_accounts"], R["B3_persons"]

    # B3 persons
    w = Writer(out, "banking", "B3_persons")
    p = np.arange(n_per)
    income = rng.choice(["low", "middle", "high"], n_per, p=[0.5, 0.4, 0.1])
    w.write(pd.DataFrame({
        "person_id": ids_fast("BP", p),
        "name_hash": ids_fast("SYNNAME", p), "national_id_hash": ids_fast("SYNNID", p),
        "dob": (np.datetime64("1950-01-01") + rng.integers(0, 365 * 55, n_per).astype("timedelta64[D]")),
        "region": rng.choice(["R01", "R02", "R03", "R04", "R05"], n_per),
        "occupation": rng.choice(["trader", "salaried", "student", "farmer", "self_employed"], n_per),
        "income_band": income,
        "phone": ids_fast("SYNPHONE", p), "email_hash": ids_fast("SYNMAIL", p),
        "address_hash": ids_fast("SYNADDR", p),
        "address_change_date": ts(rng, n_per),
    }))
    counts["B3_persons"] = w.rows

    # B2 accounts; some dormant, some low expected volume
    a = np.arange(n_acc)
    acc_person = rng.integers(0, n_per, n_acc)
    status = rng.choice(["active", "dormant", "closed"], n_acc, p=[0.88, 0.08, 0.04])
    w = Writer(out, "banking", "B2_accounts")
    w.write(pd.DataFrame({
        "account_id": ids_fast("BA", a), "person_id": ids_fast("BP", acc_person),
        "open_date": PERIOD_START - rng.integers(30, 3650, n_acc).astype("timedelta64[D]"),
        "status": status,
        "type": rng.choice(["savings", "current", "business"], n_acc, p=[0.6, 0.3, 0.1]),
        "kyc_level": rng.choice(["tier1", "tier2", "tier3"], n_acc, p=[0.4, 0.4, 0.2]),
        "expected_monthly_volume": np.round(rng.lognormal(7.5, 1.0, n_acc), 2),
        "branch": rng.choice([f"BR{i:03d}" for i in range(60)], n_acc),
        "status_change_date": ts(rng, n_acc),
        "kyc_change_date": ts(rng, n_acc),
    }))
    counts["B2_accounts"] = w.rows
    dormant = a[status == "dormant"]
    expected_vol = None  # not needed further

    # B1 transactions in chunks
    w = Writer(out, "banking", "B1_transactions")
    total, off = R["B1_transactions"], 0
    while off < total:
        n = min(chunk, total - off)
        idx = np.arange(off, off + n)
        acc = rng.integers(0, n_acc, n)
        amt = np.round(rng.lognormal(4.5, 1.3, n), 2)
        t = ts(rng, n)
        bal = np.round(rng.lognormal(8, 1.2, n), 2)
        direction = rng.choice(["debit", "credit"], n, p=[0.6, 0.4])
        df = pd.DataFrame({
            "txn_id": ids_fast("BT", idx), "account_id": acc, "timestamp": t,
            "amount": amt, "currency": CURRENCY_B,
            "channel": rng.choice(["card", "mobile", "web", "branch", "atm"], n, p=[0.4, 0.3, 0.15, 0.05, 0.1]),
            "merchant_id": rng.integers(0, 50000, n), "mcc": rng.choice([5411, 5812, 5999, 4814, 6011, 5732], n),
            "counterparty_account": rng.integers(0, n_acc, n), "terminal_id": rng.integers(0, 20000, n),
            "country": rng.choice(COUNTRIES, n), "response_code": rng.choice(["00", "05", "51"], n, p=[0.95, 0.03, 0.02]),
            "direction": direction, "balance_before": bal, "reversal_flag": 0, "original_txn_id": "",
            LABEL: "",
        })
        lab = df[LABEL].to_numpy(dtype=object, copy=True)
        A = df["amount"].to_numpy(copy=True); ACC = df["account_id"].to_numpy(copy=True); T = df["timestamp"].to_numpy(copy=True)
        RC = df["response_code"].to_numpy(dtype=object, copy=True); M = df["merchant_id"].to_numpy(copy=True)
        CH = df["channel"].to_numpy(dtype=object, copy=True); CTY = df["country"].to_numpy(dtype=object, copy=True)
        DIR = df["direction"].to_numpy(dtype=object, copy=True); CP = df["counterparty_account"].to_numpy(copy=True)
        REV = df["reversal_flag"].to_numpy(copy=True); ORIG = df["original_txn_id"].to_numpy(dtype=object, copy=True)
        # card_testing: bursts of 20 tiny card attempts on one merchant within minutes, mostly declined
        for s in plant_blocks(rng, n, PLANT_SHARE, 20):
            sl = slice(s, s + 20)
            ACC[sl] = rng.integers(0, n_acc); M[sl] = rng.integers(0, 50000)
            T[sl] = T[s] + np.sort(rng.integers(0, 600, 20)).astype("timedelta64[s]")
            A[sl] = np.round(rng.uniform(0.5, 5, 20), 2); CH[sl] = "card"; DIR[sl] = "debit"
            RC[sl] = rng.choice(["05", "51", "00"], 20, p=[0.6, 0.3, 0.1]); lab[sl] = "card_testing"
        # structuring: 6 deposits just under the threshold within 3 days
        for s in plant_blocks(rng, n, PLANT_SHARE, 6):
            sl = slice(s, s + 6)
            ACC[sl] = rng.integers(0, n_acc); DIR[sl] = "credit"; CH[sl] = "branch"
            A[sl] = np.round(rng.uniform(0.90, 0.995, 6) * STRUCTURING_THRESHOLD, 2)
            T[sl] = T[s] + rng.integers(0, 3 * 86400, 6).astype("timedelta64[s]"); RC[sl] = "00"; lab[sl] = "structuring"
        # mule_network: one inbound then fast fan out to 5 other accounts
        for s in plant_blocks(rng, n, PLANT_SHARE, 6):
            mule = rng.integers(0, n_acc); big = np.round(rng.uniform(5000, 40000), 2)
            ACC[s:s + 6] = mule; DIR[s] = "credit"; A[s] = big; CH[s:s + 6] = "mobile"
            DIR[s + 1:s + 6] = "debit"; A[s + 1:s + 6] = np.round(big / 5 * rng.uniform(0.9, 1.0, 5), 2)
            CP[s + 1:s + 6] = rng.integers(0, n_acc, 5)
            T[s + 1:s + 6] = T[s] + rng.integers(60, 3600, 5).astype("timedelta64[s]"); RC[s:s + 6] = "00"
            lab[s:s + 6] = "mule_network"
        # dormant_account_wake_up: dormant account suddenly moves large sums
        if len(dormant):
            for s in plant_blocks(rng, n, PLANT_SHARE, 3):
                ACC[s:s + 3] = rng.choice(dormant); A[s:s + 3] = np.round(rng.uniform(8000, 50000, 3), 2)
                DIR[s:s + 3] = "debit"; RC[s:s + 3] = "00"; lab[s:s + 3] = "dormant_account_wake_up"
        # kyc_mismatch_expected_volume: very large credits far above any normal amount
        for s in plant_blocks(rng, n, PLANT_SHARE, 2):
            A[s:s + 2] = np.round(rng.uniform(80000, 300000, 2), 2); DIR[s:s + 2] = "credit"
            RC[s:s + 2] = "00"; lab[s:s + 2] = "kyc_mismatch_expected_volume"
        # impossible_travel: same card in two far countries within 30 minutes
        for s in plant_blocks(rng, n, PLANT_SHARE, 2):
            ACC[s:s + 2] = rng.integers(0, n_acc); CH[s:s + 2] = "card"; CTY[s] = "GH"; CTY[s + 1] = rng.choice(["US", "GB"])
            T[s + 1] = T[s] + np.timedelta64(int(rng.integers(300, 1800)), "s"); RC[s:s + 2] = "00"
            lab[s:s + 2] = "impossible_travel"
        # benford_anomaly: amounts forced to start with 7 or 8 in a cluster
        for s in plant_blocks(rng, n, PLANT_SHARE, 10):
            sl = slice(s, s + 10)
            A[sl] = np.round(rng.choice([7, 8], 10) * 10 ** rng.integers(2, 4, 10) * rng.uniform(1.0, 1.12, 10), 2)
            lab[sl] = "benford_anomaly"
        # reversal_abuse: repeated reversals by one account
        for s in plant_blocks(rng, n, PLANT_SHARE, 4):
            ACC[s:s + 4] = rng.integers(0, n_acc); REV[s:s + 4] = 1
            ORIG[s:s + 4] = ids_fast("BT", rng.integers(0, max(off + n, 1), 4)); RC[s:s + 4] = "00"
            lab[s:s + 4] = "reversal_abuse"
        # account_takeover: large outbound web transfers to new counterparties (matching B4 plants)
        for s in plant_blocks(rng, n, PLANT_SHARE, 3):
            ACC[s:s + 3] = rng.integers(0, n_acc); CH[s:s + 3] = "web"; DIR[s:s + 3] = "debit"
            A[s:s + 3] = np.round(rng.uniform(3000, 20000, 3), 2); RC[s:s + 3] = "00"
            T[s:s + 3] = T[s] + rng.integers(0, 1800, 3).astype("timedelta64[s]"); lab[s:s + 3] = "account_takeover"
        REV[(lab == "") & (rng.random(n) < 0.002)] = 1
        df["amount"] = A; df["timestamp"] = T; df["account_id"] = ids_fast("BA", ACC)
        df["counterparty_account"] = ids_fast("BA", CP); df["merchant_id"] = ids_fast("BM", M)
        df["terminal_id"] = ids_fast("BTM", df["terminal_id"].to_numpy(copy=True))
        df["response_code"] = RC; df["channel"] = CH; df["country"] = CTY; df["direction"] = DIR
        df["reversal_flag"] = REV; df["original_txn_id"] = ORIG; df[LABEL] = lab
        sign = np.where(DIR == "debit", -1, 1)
        df["balance_after"] = np.round(df["balance_before"].to_numpy(copy=True) + sign * A, 2)
        df = df[["txn_id", "account_id", "timestamp", "amount", "currency", "channel", "merchant_id", "mcc",
                 "counterparty_account", "terminal_id", "country", "response_code", "direction",
                 "balance_before", "balance_after", "reversal_flag", "original_txn_id", LABEL]]
        w.write(df); off += n
    counts["B1_transactions"] = w.rows

    # B4 auth events; account takeover = password reset, new device, new ip, login burst
    w = Writer(out, "banking", "B4_auth_events")
    total, off = R["B4_auth_events"], 0
    while off < total:
        n = min(chunk, total - off)
        per = rng.integers(0, n_per, n); dev = rng.integers(0, R["B5_devices"], n)
        et = rng.choice(["login", "login_failed", "password_reset", "otp_sent", "logout"], n, p=[0.6, 0.08, 0.02, 0.15, 0.15])
        T = ts(rng, n); geo = rng.choice(COUNTRIES, n).astype(object); ip = rng.integers(0, 2**24, n)
        lab = np.full(n, "", dtype=object)
        for s in plant_blocks(rng, n, PLANT_SHARE, 5):
            per[s:s + 5] = rng.integers(0, n_per); dev[s:s + 5] = rng.integers(0, R["B5_devices"])
            ip[s:s + 5] = rng.integers(0, 2**24); geo[s:s + 5] = rng.choice(["NG", "US", "GB"])
            et[s:s + 5] = ["login_failed", "login_failed", "password_reset", "otp_sent", "login"]
            T[s:s + 5] = T[s] + np.sort(rng.integers(0, 900, 5)).astype("timedelta64[s]"); lab[s:s + 5] = "account_takeover"
        w.write(pd.DataFrame({"event_id": ids_fast("BE", np.arange(off, off + n)), "person_id": ids_fast("BP", per),
                              "device_id": ids_fast("BD", dev), "ip": ids_fast("SYNIP", ip), "geo": geo,
                              "event_type": et, "timestamp": T, LABEL: lab}))
        off += n
    counts["B4_auth_events"] = w.rows

    # B5 devices
    n = R["B5_devices"]; w = Writer(out, "banking", "B5_devices")
    w.write(pd.DataFrame({"device_id": ids_fast("BD", np.arange(n)), "imei_or_fingerprint": ids_fast("SYNFP", np.arange(n)),
                          "first_seen": ts(rng, n), "last_seen": ts(rng, n), "person_id": ids_fast("BP", rng.integers(0, n_per, n))}))
    counts["B5_devices"] = w.rows

    # B6 beneficiaries; mule beneficiaries shared by many accounts
    n = R["B6_beneficiaries"]; w = Writer(out, "banking", "B6_beneficiaries")
    ben = rng.integers(0, n_acc, n); lab = np.full(n, "", dtype=object)
    k = max(1, int(n * PLANT_SHARE)); hub = rng.integers(0, n_acc, max(1, k // 10))
    pi = rng.choice(n, k, replace=False); ben[pi] = rng.choice(hub, k); lab[pi] = "mule_network"
    w.write(pd.DataFrame({"account_id": ids_fast("BA", rng.integers(0, n_acc, n)), "payee_account": ids_fast("BA", ben),
                          "added_at": ts(rng, n), "added_via_device": ids_fast("BD", rng.integers(0, R["B5_devices"], n)), LABEL: lab}))
    counts["B6_beneficiaries"] = w.rows

    # B8 users and access; SoD = same user is preparer and approver role; privileged grants before journals
    n_users = R["B8_users_access"]; users = np.arange(n_users)
    role = rng.choice(["teller", "accountant", "approver", "it_admin", "auditor"], n_users, p=[0.4, 0.25, 0.15, 0.1, 0.1])
    change = ts(rng, n_users); lab = np.full(n_users, "", dtype=object)
    perm = np.where(role == "approver", "approve_journal", np.where(role == "accountant", "post_journal", "read")).astype(object)
    priv = rng.choice(np.where(role == "accountant")[0], max(1, int(n_users * 0.002)), replace=False)
    perm[priv] = "admin_gl"; lab[priv] = "privileged_access_before_journals"
    w = Writer(out, "banking", "B8_users_access")
    w.write(pd.DataFrame({"user_id": ids_fast("BU", users), "is_active": rng.random(n_users) < 0.92, "role": role,
                          "permission": perm, "last_login": ts(rng, n_users), "change_time": change,
                          "changed_by": ids_fast("BU", rng.integers(0, n_users, n_users)),
                          "change_type": rng.choice(["grant", "revoke", "modify"], n_users), LABEL: lab}))
    counts["B8_users_access"] = w.rows
    preparers = np.where(role == "accountant")[0]; approvers = np.where(role == "approver")[0]

    # B7 GL journal
    w = Writer(out, "banking", "B7_gl_journal")
    total, off = R["B7_gl_journal"], 0
    while off < total:
        n = min(chunk, total - off)
        T = ts(rng, n); pr = rng.choice(preparers, n); ap = rng.choice(approvers, n)
        man = rng.random(n) < 0.1; amt = np.round(rng.lognormal(7, 1.5, n), 2)
        hour_shift = np.zeros(n, dtype="timedelta64[s]"); lab = np.full(n, "", dtype=object)
        desc = rng.choice(["accrual", "fee income", "interest", "reclass", "settlement"], n).astype(object)
        for s in plant_blocks(rng, n, PLANT_SHARE, 3):  # journal_abuse: manual, round, weekend night, vague text
            man[s:s + 3] = True; amt[s:s + 3] = rng.choice([50000, 100000, 250000], 3).astype(float)
            d = T[s].astype("datetime64[D]"); wd = (d.astype(int) - 4) % 7  # 0 = Monday
            T[s:s + 3] = d + np.timedelta64(int((5 - wd) % 7), "D") + np.timedelta64(2 * 3600 + 7, "s")
            desc[s:s + 3] = "adj"; lab[s:s + 3] = "journal_abuse"
        for s in plant_blocks(rng, n, PLANT_SHARE, 2):  # segregation_of_duties: preparer equals approver
            ap[s:s + 2] = pr[s:s + 2]; man[s:s + 2] = True; lab[s:s + 2] = "segregation_of_duties"
        for s in plant_blocks(rng, n, PLANT_SHARE, 2):  # privileged access holder posts manual journals
            pr[s:s + 2] = rng.choice(priv); man[s:s + 2] = True; lab[s:s + 2] = "privileged_access_before_journals"
        je = (off + np.arange(n)) // 2
        deb = np.where(np.arange(n) % 2 == 0, amt, 0.0); cre = np.where(np.arange(n) % 2 == 1, amt, 0.0)
        w.write(pd.DataFrame({"line_id": ids_fast("BL", np.arange(off, off + n)), "je_id": ids_fast("BJ", je),
                              "posting_date": T.astype("datetime64[D]"), "entry_timestamp": T,
                              "account_code": rng.choice([f"GL{i:05d}" for i in range(400)], n), "debit": deb, "credit": cre,
                              "preparer_id": ids_fast("BU", pr), "approver_id": ids_fast("BU", ap), "is_manual": man,
                              "description": desc, "document_type": rng.choice(["JE", "AP", "AR", "FA"], n),
                              "reversal_ind": rng.random(n) < 0.01, LABEL: lab}))
        off += n
    counts["B7_gl_journal"] = w.rows

    # B9 cards and authorisations
    w = Writer(out, "banking", "B9_cards_and_authorisations")
    total, off = R["B9_cards_and_authorisations"], 0
    while off < total:
        n = min(chunk, total - off)
        card = rng.integers(0, max(1, n_acc), n); T = ts(rng, n); amt = np.round(rng.lognormal(4, 1.2, n), 2)
        rc = rng.choice(["00", "05", "51"], n, p=[0.95, 0.03, 0.02]).astype(object); lab = np.full(n, "", dtype=object)
        term = rng.integers(0, 20000, n)
        for s in plant_blocks(rng, n, PLANT_SHARE, 20):
            card[s:s + 20] = rng.integers(0, n_acc); term[s:s + 20] = rng.integers(0, 20000)
            T[s:s + 20] = T[s] + np.sort(rng.integers(0, 600, 20)).astype("timedelta64[s]")
            amt[s:s + 20] = np.round(rng.uniform(0.5, 5, 20), 2); rc[s:s + 20] = "05"; lab[s:s + 20] = "card_testing"
        w.write(pd.DataFrame({"card_id": ids_fast("BC", card), "account_id": ids_fast("BA", card),
                              "card_status": rng.choice(["active", "blocked", "expired"], n, p=[0.95, 0.03, 0.02]),
                              "issue_date": PERIOD_START - rng.integers(30, 1500, n).astype("timedelta64[D]"),
                              "auth_id": ids_fast("BZ", np.arange(off, off + n)), "auth_time": T, "amount": amt,
                              "response_code": rc, "terminal_id": ids_fast("BTM", term),
                              "terminal_type": rng.choice(["pos", "atm", "ecom"], n), LABEL: lab}))
        off += n
    counts["B9_cards_and_authorisations"] = w.rows

    # B10 vendors and payments; ghost vendor shares an employee bank account; duplicate payments
    n = R["B10_vendors_and_payments"]; n_emp = max(10, R["B11_payroll_and_hr"] // 12)
    n_vend = max(5, n // 20); vend = rng.integers(0, n_vend, n)
    vacct = ids_fast("BVBANK", np.arange(n_vend)).astype(object)
    ghost = rng.choice(n_vend, max(1, int(n_vend * 0.005)), replace=False)
    emp_acct = ids_fast("BEBANK", np.arange(n_emp))
    vacct[ghost] = rng.choice(emp_acct, len(ghost))
    pdate = ts(rng, n); pamt = np.round(rng.lognormal(8, 1.0, n), 2); lab = np.full(n, "", dtype=object)
    lab[np.isin(vend, ghost)] = "ghost_vendor_or_employee"
    dup = rng.choice(n - 1, max(1, int(n * PLANT_SHARE * 4)), replace=False)
    vend[dup + 1] = vend[dup]; pamt[dup + 1] = pamt[dup]
    pdate[dup + 1] = pdate[dup] + rng.integers(0, 3 * 86400, len(dup)).astype("timedelta64[s]")
    lab[dup + 1] = "duplicate_vendor_payments"
    w = Writer(out, "banking", "B10_vendors_and_payments")
    w.write(pd.DataFrame({"vendor_id": ids_fast("BV", vend), "vendor_name": ids_fast("SYNVENDOR", vend),
                          "vendor_bank_account": vacct[vend], "vendor_address": ids_fast("SYNADDR", vend),
                          "created_by": ids_fast("BU", rng.choice(preparers, n)), "created_at": PERIOD_START - rng.integers(1, 900, n).astype("timedelta64[D]"),
                          "payment_id": ids_fast("BPAY", np.arange(n)), "payment_date": pdate, "payment_amount": pamt,
                          "payment_approver_id": ids_fast("BU", rng.choice(approvers, n)), LABEL: lab}))
    counts["B10_vendors_and_payments"] = w.rows

    # B11 payroll and HR; paid after exit
    n = R["B11_payroll_and_hr"]; emp = np.arange(n) % n_emp; month = np.arange(n) // n_emp
    hire = PERIOD_START - rng.integers(100, 4000, n_emp).astype("timedelta64[D]")
    exit_d = np.full(n_emp, np.datetime64("NaT", "D"))
    leavers = rng.choice(n_emp, max(1, n_emp // 20), replace=False)
    exit_d[leavers] = PERIOD_START.astype("datetime64[D]") + rng.integers(0, 200, len(leavers)).astype("timedelta64[D]")
    paydate = PERIOD_START.astype("datetime64[D]") + (np.minimum(month, 11) * 30 + 25).astype("timedelta64[D]")
    after = ~np.isnat(exit_d[emp]) & (paydate > exit_d[emp])
    keep_paying = np.isin(emp, leavers[: max(1, len(leavers) // 5)])
    lab = np.where(after & keep_paying, "payroll_after_exit", "").astype(object)
    att = np.where(after & ~keep_paying, 0, rng.integers(18, 23, n)); att[lab != ""] = 0
    pay = np.where(after & ~keep_paying, 0.0, np.round(rng.lognormal(8, 0.4, n), 2))
    w = Writer(out, "banking", "B11_payroll_and_hr")
    w.write(pd.DataFrame({"employee_id": ids_fast("BEMP", emp), "employee_bank_account": emp_acct[emp],
                          "hire_date": hire[emp].astype("datetime64[D]"), "exit_date": exit_d[emp],
                          "department": rng.choice(["ops", "finance", "it", "sales"], n_emp)[emp],
                          "pay_run_id": ids_fast("BRUN", month), "pay_date": paydate, "pay_amount": pay,
                          "attendance_days": att, LABEL: lab}))
    counts["B11_payroll_and_hr"] = w.rows

    bscen = cfg["scenarios"]["banking"]
    # B12 fraud cases (synthetic history)
    n = R["B12_fraud_cases"]; w = Writer(out, "banking", "B12_fraud_cases")
    rep = ts(rng, n)
    w.write(pd.DataFrame({"case_id": ids_fast("BCASE", np.arange(n)), "entity_id": ids_fast("BA", rng.integers(0, n_acc, n)),
                          "entity_type": "account", "scenario": rng.choice(bscen, n),
                          "loss_amount": np.round(rng.lognormal(7, 1.3, n), 2), "reported_date": rep,
                          "confirmed_date": rep + rng.integers(1, 60 * 86400, n).astype("timedelta64[s]"),
                          "outcome": rng.choice(["confirmed", "not_fraud", "open"], n, p=[0.5, 0.35, 0.15])}))
    counts["B12_fraud_cases"] = w.rows
    # B13 existing alerts (synthetic, used for rule coverage gap only)
    n = R["B13_existing_alerts"]; w = Writer(out, "banking", "B13_existing_alerts")
    w.write(pd.DataFrame({"alert_id": ids_fast("BAL", np.arange(n)),
                          "rule_or_model": rng.choice(["legacy_velocity", "legacy_amount", "legacy_country"], n),
                          "score": np.round(rng.random(n), 4), "entity_id": ids_fast("BA", rng.integers(0, n_acc, n)),
                          "alert_date": ts(rng, n), "analyst_id": ids_fast("BU", rng.integers(0, n_users, n)),
                          "disposition": rng.choice(["false_positive", "escalated", "closed"], n, p=[0.8, 0.1, 0.1])}))
    counts["B13_existing_alerts"] = w.rows
    # B14 reference parameters
    n = R["B14_reference_parameters"]; w = Writer(out, "banking", "B14_reference_parameters")
    rt = np.array(["mcc", "country", "threshold", "channel"])[np.arange(n) % 4]
    lim = np.where(rt == "threshold", STRUCTURING_THRESHOLD, np.nan)
    w.write(pd.DataFrame({"reference_type": rt, "code": ids_fast("REF", np.arange(n)), "description": "synthetic reference row",
                          "limit_value": lim, "threshold_value": lim}))
    counts["B14_reference_parameters"] = w.rows
    return counts


# ---------------------------------------------------------------- telecom
def gen_telecom(cfg, scale, out, rng, chunk):
    R = {k: max(1, int(v * scale)) for k, v in cfg["rows"]["telecom"].items()}
    counts = {}
    n_sub, n_wal = R["T2_subscribers"], R["T5_wallets"]
    n_agents = max(10, R["T6_agents"] // 100); n_cells = max(20, R["T9_cell_sites_and_roaming"] // 20)
    n_routes = 40

    # T2 subscribers; bust out = new postpaid with high credit, many from one shop
    s = np.arange(n_sub); act = ts(rng, n_sub, PERIOD_START - np.timedelta64(400, "D"), 400 * 86400 + PERIOD_SECONDS)
    plan = rng.choice(["prepaid", "postpaid"], n_sub, p=[0.85, 0.15]).astype(object)
    credit = np.where(plan == "postpaid", np.round(rng.uniform(50, 500, n_sub), 2), 0.0)
    shop = rng.integers(0, 300, n_sub); lab = np.full(n_sub, "", dtype=object)
    bust = rng.choice(n_sub, max(1, int(n_sub * PLANT_SHARE * 2)), replace=False)
    plan[bust] = "postpaid"; credit[bust] = np.round(rng.uniform(1500, 3000, len(bust)), 2)
    shop[bust] = rng.integers(0, 3, len(bust)); lab[bust] = "subscription_and_bust_out"
    w = Writer(out, "telecom", "T2_subscribers")
    w.write(pd.DataFrame({"msisdn": ids_fast("TM", s), "person_id": ids_fast("TP", s), "activation_date": act, "plan": plan,
                          "kyc_status": rng.choice(["verified", "pending", "failed"], n_sub, p=[0.9, 0.08, 0.02]),
                          "id_number_hash": ids_fast("SYNTID", rng.integers(0, n_sub, n_sub)), "credit_limit": credit,
                          "registration_channel": rng.choice(["shop", "agent", "online"], n_sub),
                          "registration_shop_id": ids_fast("TSHOP", shop), LABEL: lab}))
    counts["T2_subscribers"] = w.rows
    bust_ms = bust

    # T3 SIM swaps; sim_swap_fraud swapped msisdns later drain wallets in T4; insider = one user many swaps at night
    n = R["T3_sims_and_sim_swap_events"]; ms = rng.integers(0, n_sub, n); T = ts(rng, n)
    user = rng.integers(0, 2000, n); ch = rng.choice(["shop", "call_centre", "online"], n).astype(object)
    lab = np.full(n, "", dtype=object); k = max(1, int(n * PLANT_SHARE * 2))
    ssw = rng.choice(n, k, replace=False); lab[ssw] = "sim_swap_fraud"
    # The draws below are kept only so the random stream (and so T4, T1 and later tables) stays identical
    # to earlier versions; their effect is undone straight after. Version 1 spread insider swaps over the
    # whole year across 3 users and spread IMEI churn swaps over a year per number, so neither pattern
    # stood out from normal traffic and both rules missed them (recall 0 at sample size).
    keep = (ms.copy(), user.copy(), ch.copy(), T.copy())
    ins = rng.choice(np.setdiff1d(np.arange(n), ssw), k, replace=False)
    user[ins] = rng.integers(0, 3, k)
    T[ins] = T[ins].astype("datetime64[D]") + rng.integers(0, 4 * 3600, k).astype("timedelta64[s]")
    imc = rng.choice(np.setdiff1d(np.arange(n), np.concatenate([ssw, ins])), k, replace=False)
    ms[imc] = rng.choice(rng.integers(0, n_sub, max(1, k // 8)), k)
    ms, user, ch, T = keep
    sim = rng.integers(0, n_sub * 2, n)
    old_imei = rng.integers(0, 10**8, n); new_imei = rng.integers(0, 10**8, n)
    # Version 2 planting on a separate seeded stream, on rows that are not sim_swap_fraud plants.
    prng = np.random.default_rng(cfg["seed"] + 100)
    pool = prng.permutation(np.setdiff1d(np.arange(n), ssw))
    n_ins = max(1, k // 8); n_imc = max(1, k // 6); pos = 0
    for _ in range(n_ins):  # insider: one call centre user, 8 swaps on different numbers in one night (00:00 to 04:00)
        rows = pool[pos:pos + 8]; pos += 8
        day = T[rows[0]].astype("datetime64[D]")
        user[rows] = prng.integers(0, 2000); ch[rows] = "call_centre"
        T[rows] = day + np.sort(prng.integers(0, 4 * 3600, 8)).astype("timedelta64[s]")
        lab[rows] = "insider_sim_swap_or_access_abuse"
    for _ in range(n_imc):  # imei_churn: one number, 6 swaps within 30 days, each new IMEI becomes the next old IMEI
        rows = pool[pos:pos + 6]; pos += 6
        ms[rows] = prng.integers(0, n_sub)
        T[rows] = T[rows[0]] + np.sort(prng.integers(0, 30 * 86400, 6)).astype("timedelta64[s]")
        chain = prng.integers(0, 10**8, 7); old_imei[rows] = chain[:6]; new_imei[rows] = chain[1:]
        lab[rows] = "imei_churn"
    w = Writer(out, "telecom", "T3_sims_and_sim_swap_events")
    w.write(pd.DataFrame({"swap_id": ids_fast("TSW", np.arange(n)), "sim_id": ids_fast("TSIM", sim),
                          "msisdn": ids_fast("TM", ms), "swap_time": T, "old_imei": ids_fast("TIMEI", old_imei),
                          "new_imei": ids_fast("TIMEI", new_imei), "channel": ch,
                          "performed_by_user": ids_fast("TU", user), "shop_id": ids_fast("TSHOP", rng.integers(0, 300, n)), LABEL: lab}))
    counts["T3_sims_and_sim_swap_events"] = w.rows
    swapped_ms, swapped_t = ms[ssw], T[ssw]

    # T5 wallets
    wl = np.arange(n_wal); tier = rng.choice(["tier1", "tier2", "tier3"], n_wal, p=[0.6, 0.3, 0.1])
    limit = np.select([tier == "tier1", tier == "tier2"], [2000.0, 10000.0], 50000.0)
    wstat = rng.choice(["active", "dormant", "suspended"], n_wal, p=[0.88, 0.1, 0.02])
    wal_ms = rng.integers(0, n_sub, n_wal); wal_ms[: len(swapped_ms)] = swapped_ms[: n_wal]
    w = Writer(out, "telecom", "T5_wallets")
    w.write(pd.DataFrame({"wallet_id": ids_fast("TW", wl), "msisdn": ids_fast("TM", wal_ms), "person_id": ids_fast("TP", wal_ms),
                          "opened_at": PERIOD_START - rng.integers(10, 1500, n_wal).astype("timedelta64[D]"), "status": wstat,
                          "kyc_tier": tier, "wallet_limit": limit}))
    counts["T5_wallets"] = w.rows
    tier1 = wl[tier == "tier1"]; dormant_w = wl[wstat == "dormant"]
    n_swap_w = min(len(swapped_ms), n_wal)

    # T4 wallet transactions
    w = Writer(out, "telecom", "T4_momo_wallet_txns")
    total, off = R["T4_momo_wallet_txns"], 0
    while off < total:
        n = min(chunk, total - off)
        W = rng.integers(0, n_wal, n); T = ts(rng, n); amt = np.round(rng.lognormal(3.8, 1.2, n), 2)
        typ = rng.choice(["p2p", "cash_in", "cash_out", "merchant", "airtime"], n, p=[0.35, 0.2, 0.2, 0.15, 0.1]).astype(object)
        ag = rng.integers(0, n_agents, n); cp = rng.integers(0, n_wal, n); lab = np.full(n, "", dtype=object)
        stt = rng.choice(["success", "failed"], n, p=[0.97, 0.03]).astype(object); rev = np.full(n, "", dtype=object)
        if n_swap_w:  # sim_swap_fraud: within hours of swap, wallet drained by cash out
            for s in plant_blocks(rng, n, PLANT_SHARE, 3):
                j = rng.integers(0, n_swap_w); W[s:s + 3] = j
                T[s:s + 3] = swapped_t[j] + rng.integers(600, 6 * 3600, 3).astype("timedelta64[s]")
                typ[s:s + 3] = "cash_out"; amt[s:s + 3] = np.round(rng.uniform(1000, 8000, 3), 2); stt[s:s + 3] = "success"
                lab[s:s + 3] = "sim_swap_fraud"
        for s in plant_blocks(rng, n, PLANT_SHARE, 4):  # wallet_tier_breach
            W[s:s + 4] = rng.choice(tier1); amt[s:s + 4] = np.round(rng.uniform(2500, 6000, 4), 2); typ[s:s + 4] = "p2p"
            stt[s:s + 4] = "success"; lab[s:s + 4] = "wallet_tier_breach"
        if len(dormant_w):
            for s in plant_blocks(rng, n, PLANT_SHARE, 3):  # dormant_wallet_drain
                W[s:s + 3] = rng.choice(dormant_w); typ[s:s + 3] = "cash_out"; amt[s:s + 3] = np.round(rng.uniform(800, 5000, 3), 2)
                stt[s:s + 3] = "success"; lab[s:s + 3] = "dormant_wallet_drain"
        for s in plant_blocks(rng, n, PLANT_SHARE, 10):  # agent_fraud: one agent split cash in with round amounts and reversals
            ag[s:s + 10] = rng.integers(0, max(1, n_agents // 50)); typ[s:s + 10] = "cash_in"
            amt[s:s + 10] = rng.choice([100.0, 200.0, 500.0], 10); T[s:s + 10] = T[s] + np.sort(rng.integers(0, 1800, 10)).astype("timedelta64[s]")
            rev[s + 5:s + 10] = ids_fast("TT", np.arange(off + s, off + s + 5)); stt[s:s + 10] = "success"; lab[s:s + 10] = "agent_fraud"
        bal = np.round(rng.lognormal(6, 1.2, n), 2)
        sign = np.where(np.isin(typ, ["cash_in"]), 1, -1)
        w.write(pd.DataFrame({"txn_id": ids_fast("TT", np.arange(off, off + n)), "wallet_id": ids_fast("TW", W), "timestamp": T,
                              "type": typ, "amount": amt, "counterparty": ids_fast("TW", cp), "agent_id": ids_fast("TAG", ag),
                              "balance_before": bal, "balance_after": np.round(bal + sign * amt, 2), "status": stt,
                              "reversal_of": rev, LABEL: lab}))
        off += n
    counts["T4_momo_wallet_txns"] = w.rows

    # T1 CDRs
    w = Writer(out, "telecom", "T1_cdrs")
    total, off = R["T1_cdrs"], 0
    route_min = np.zeros(n_routes)  # T1 minutes per route, so T8 can settle against them
    route_day_min = np.zeros(n_routes * 365)  # T1 minutes per route and day
    while off < total:
        n = min(chunk, total - off)
        caller = rng.integers(0, n_sub, n); callee = rng.integers(0, n_sub, n); T = ts(rng, n)
        dur = rng.gamma(1.5, 80, n).astype(int); ct = rng.choice(["voice", "sms", "data"], n, p=[0.5, 0.3, 0.2]).astype(object)
        cell = rng.integers(0, n_cells, n); route = rng.integers(0, n_routes, n); imei = rng.integers(0, 10**8, n)
        roam = rng.random(n) < 0.01; lab = np.full(n, "", dtype=object); chg = np.round(dur * 0.002, 4)
        for s in plant_blocks(rng, n, PLANT_SHARE, 50):  # sim_box_and_bypass: one SIM, many short calls, one cell, many callees
            caller[s:s + 50] = rng.integers(0, n_sub); cell[s:s + 50] = rng.integers(0, n_cells); imei[s:s + 50] = rng.integers(0, 10**8)
            ct[s:s + 50] = "voice"; dur[s:s + 50] = rng.integers(20, 120, 50); route[s:s + 50] = rng.integers(0, 3)
            T[s:s + 50] = T[s] + np.sort(rng.integers(0, 4 * 3600, 50)).astype("timedelta64[s]"); lab[s:s + 50] = "sim_box_and_bypass"
        for s in plant_blocks(rng, n, PLANT_SHARE, 30):  # wangiri: one number, many 0 to 3 second calls
            caller[s:s + 30] = rng.integers(0, n_sub); ct[s:s + 30] = "voice"; dur[s:s + 30] = rng.integers(0, 4, 30)
            roam[s:s + 30] = True; T[s:s + 30] = T[s] + np.sort(rng.integers(0, 1800, 30)).astype("timedelta64[s]"); lab[s:s + 30] = "wangiri"
        for s in plant_blocks(rng, n, PLANT_SHARE, 20):  # subscription_and_bust_out: heavy premium usage by bust out subs
            caller[s:s + 20] = rng.choice(bust_ms); ct[s:s + 20] = "voice"; dur[s:s + 20] = rng.integers(1800, 3600, 20); roam[s:s + 20] = True
            lab[s:s + 20] = "subscription_and_bust_out"
        for s in plant_blocks(rng, n, PLANT_SHARE, 20):  # interconnect_leakage: traffic on routes 37 to 39 (unsettled in T8)
            route[s:s + 20] = rng.integers(37, 40, 20); lab[s:s + 20] = "interconnect_leakage"
        chg = np.round(dur * 0.002, 4); route_min += np.bincount(route, weights=dur, minlength=n_routes) / 60
        dix = np.clip(((T - PERIOD_START) // np.timedelta64(1, 'D')).astype(np.int64), 0, 364)
        route_day_min += np.bincount(route * 365 + dix, weights=dur, minlength=n_routes * 365) / 60
        w.write(pd.DataFrame({"cdr_id": ids_fast("TC", np.arange(off, off + n)), "caller": ids_fast("TM", caller),
                              "callee": ids_fast("TM", callee), "start_time": T, "duration_sec": dur, "call_type": ct,
                              "cell_id": ids_fast("TCELL", cell), "route": ids_fast("TR", route), "imsi": ids_fast("TIMSI", caller),
                              "imei": ids_fast("TIMEI", imei), "charge": chg, "roaming_flag": roam, LABEL: lab}))
        off += n
    counts["T1_cdrs"] = w.rows

    # T6 agents joined to float movements
    w = Writer(out, "telecom", "T6_agents")
    total, off = R["T6_agents"], 0
    reg = rng.choice(["R01", "R02", "R03", "R04", "R05"], n_agents); onb = PERIOD_START - rng.integers(10, 2000, n_agents).astype("timedelta64[D]")
    while off < total:
        n = min(chunk, total - off)
        ag = rng.integers(0, n_agents, n); T = ts(rng, n); fl = np.round(rng.lognormal(7, 1, n), 2)
        mt = rng.choice(["top_up", "rebalance", "withdraw"], n).astype(object); lab = np.full(n, "", dtype=object)
        com = np.round(fl * 0.01, 2)
        for s in plant_blocks(rng, n, PLANT_SHARE, 8):  # agent_float_anomalies: night rebalances, large float, high commission
            ag[s:s + 8] = rng.integers(0, n_agents); mt[s:s + 8] = "rebalance"; fl[s:s + 8] = np.round(rng.uniform(40000, 90000, 8), 2)
            T[s:s + 8] = T[s].astype("datetime64[D]") + rng.integers(0, 4 * 3600, 8).astype("timedelta64[s]")
            com[s:s + 8] = np.round(fl[s:s + 8] * 0.05, 2); lab[s:s + 8] = "agent_float_anomalies"
        w.write(pd.DataFrame({"agent_id": ids_fast("TAG", ag), "region": reg[ag], "onboarded_at": onb[ag],
                              "commission_rate": 0.01, "status": "active", "movement_time": T, "movement_type": mt,
                              "float_amount": fl, "payout_date": (T + np.timedelta64(30, "D")).astype("datetime64[D]"),
                              "commission_amount": com, LABEL: lab}))
        off += n
    counts["T6_agents"] = w.rows

    # T7 top ups and billing; recharge_fraud = many top ups same msisdn minutes apart
    w = Writer(out, "telecom", "T7_topups_billing")
    total, off = R["T7_topups_billing"], 0
    while off < total:
        n = min(chunk, total - off)
        ms = rng.integers(0, n_sub, n); T = ts(rng, n); amt = np.round(rng.choice([1, 2, 5, 10, 20, 50], n) * 1.0, 2)
        et = rng.choice(["topup", "invoice", "payment"], n, p=[0.8, 0.1, 0.1]).astype(object); lab = np.full(n, "", dtype=object)
        bad = np.zeros(n)
        for s in plant_blocks(rng, n, PLANT_SHARE, 15):
            ms[s:s + 15] = rng.integers(0, n_sub); et[s:s + 15] = "topup"; amt[s:s + 15] = 50.0
            T[s:s + 15] = T[s] + np.sort(rng.integers(0, 900, 15)).astype("timedelta64[s]"); lab[s:s + 15] = "recharge_fraud"
        for s in plant_blocks(rng, n, PLANT_SHARE, 2):
            ms[s:s + 2] = rng.choice(bust_ms); et[s:s + 2] = "invoice"; amt[s:s + 2] = np.round(rng.uniform(1500, 3000, 2), 2)
            bad[s:s + 2] = amt[s:s + 2]; lab[s:s + 2] = "subscription_and_bust_out"
        w.write(pd.DataFrame({"msisdn": ids_fast("TM", ms), "event_time": T, "event_type": et, "amount": amt,
                              "channel": rng.choice(["ussd", "app", "voucher", "agent"], n),
                              "invoice_status": np.where(et == "invoice", np.where(bad > 0, "unpaid", "paid"), ""),
                              "collections_amount": np.where(bad > 0, 0.0, np.where(et == "invoice", amt, 0.0)),
                              "bad_debt_amount": bad, LABEL: lab}))
        off += n
    counts["T7_topups_billing"] = w.rows

    # T8 interconnect traffic per route and day; routes 37 to 39 under settled
    n = R["T8_interconnect_traffic"]; d = PERIOD_START.astype("datetime64[D]") + rng.integers(0, 365, n).astype("timedelta64[D]")
    rt = rng.integers(0, n_routes, n); mins = np.round(rng.uniform(1000, 20000, n), 1)
    # Settled minutes follow T1 per route and day. The original draws are kept (RNG order), then a separate RNG
    # places the rows on route days: every route gets at least one row (version 1 left some routes, e.g. TR000000012
    # and TR000000030 in the sample, with no T8 row at all), and when there are more rows than route days every route
    # day is covered. Each route day's T1 minutes are split over its rows in proportion to the drawn values, times a
    # settled share of 0.97 to 1.0 for normal routes and 0.6 for leakage routes 37 to 39.
    prng8 = np.random.default_rng(cfg["seed"] + 200)
    share = prng8.uniform(0.97, 1.0, n_routes); share[37:] = 0.6
    ncell = n_routes * 365
    if n >= ncell:
        cell = np.concatenate([np.arange(ncell), prng8.integers(0, ncell, n - ncell)])
    else:
        first = np.arange(n_routes) * 365 + prng8.integers(0, 365, n_routes)
        rest = prng8.choice(np.setdiff1d(np.arange(ncell), first), max(0, n - n_routes), replace=False)
        cell = np.concatenate([first, rest])[:n]
    cell = prng8.permutation(cell); rt = cell // 365
    d = PERIOD_START.astype("datetime64[D]") + (cell % 365).astype("timedelta64[D]")
    tot = np.bincount(cell, weights=mins, minlength=ncell)
    mins = np.floor(mins / tot[cell] * route_day_min[cell] * share[rt] * 10) / 10
    settle = np.round(mins * 0.01, 2); lab = np.where(rt >= 37, "interconnect_leakage", "").astype(object)
    settle[rt >= 37] = np.round(settle[rt >= 37] * 0.4, 2)
    w = Writer(out, "telecom", "T8_interconnect_traffic")
    w.write(pd.DataFrame({"traffic_date": d, "route": ids_fast("TR", rt), "carrier": ids_fast("TCARRIER", rt % 8),
                          "minutes": mins, "settlement_amount": settle, LABEL: lab}))
    counts["T8_interconnect_traffic"] = w.rows

    # T9 cell sites and roaming
    n = R["T9_cell_sites_and_roaming"]; w = Writer(out, "telecom", "T9_cell_sites_and_roaming")
    w.write(pd.DataFrame({"cell_id": ids_fast("TCELL", np.arange(n) % n_cells), "location": ids_fast("TLOC", (np.arange(n) % n_cells) // 5),
                          "roaming_record_id": ids_fast("TRR", np.arange(n)), "msisdn": ids_fast("TM", rng.integers(0, n_sub, n)),
                          "roaming_country": rng.choice(["NG", "CI", "TG", "GB", "US"], n), "roaming_start_time": ts(rng, n)}))
    counts["T9_cell_sites_and_roaming"] = w.rows

    tscen = cfg["scenarios"]["telecom"]
    n = R["T10_complaints_and_cases"]; w = Writer(out, "telecom", "T10_complaints_and_cases")
    w.write(pd.DataFrame({"case_id": ids_fast("TCASE", np.arange(n)), "msisdn": ids_fast("TM", rng.integers(0, n_sub, n)),
                          "scenario": rng.choice(tscen, n), "case_date": ts(rng, n),
                          "outcome": rng.choice(["confirmed", "not_fraud", "open"], n, p=[0.5, 0.35, 0.15])}))
    counts["T10_complaints_and_cases"] = w.rows
    n = R["T11_alerts_and_rules"]; w = Writer(out, "telecom", "T11_alerts_and_rules")
    rid = rng.integers(0, 5, n)
    w.write(pd.DataFrame({"alert_id": ids_fast("TAL", np.arange(n)), "rule_or_model": "legacy_rule", "score": np.round(rng.random(n), 4),
                          "entity_id": ids_fast("TM", rng.integers(0, n_sub, n)), "alert_date": ts(rng, n),
                          "analyst_id": ids_fast("TU", rng.integers(0, 2000, n)),
                          "disposition": rng.choice(["false_positive", "escalated", "closed"], n, p=[0.8, 0.1, 0.1]),
                          "rule_id": ids_fast("TRULE", rid), "rule_definition": "synthetic legacy rule", "rule_threshold": (rid + 1) * 10.0}))
    counts["T11_alerts_and_rules"] = w.rows
    n = R["T12_reference_parameters"]; w = Writer(out, "telecom", "T12_reference_parameters")
    w.write(pd.DataFrame({"reference_type": np.array(["route", "tier_limit", "tariff"])[np.arange(n) % 3],
                          "code": ids_fast("TREF", np.arange(n)), "description": "synthetic reference row", "value": rng.random(n)}))
    counts["T12_reference_parameters"] = w.rows
    return counts


def export_csv(src: Path, dst: Path) -> None:
    """One CSV per dataset, all planted rows included (the sample is generated, not subsampled)."""
    for domain in ("banking", "telecom"):
        (dst / domain).mkdir(parents=True, exist_ok=True)
        for d in sorted((src / domain).iterdir()):
            pd.read_parquet(d).to_csv(dst / domain / f"{d.name}.csv", index=False, date_format="%Y-%m-%dT%H:%M:%SZ")


MAX_PART_BYTES = 90 * 1024**2  # stay well under GitHub's 100 MB per file limit


def export_full(src: Path, dst: Path, zstd_level: int = 9) -> Path:
    """Rewrite generated data as numbered zstd Parquet parts (each 90 MB or less) plus data/full/manifest.json
    with row counts and SHA256 checksums, so the full SYNTHETIC dataset can be committed to git."""
    import hashlib
    import json
    if dst.exists():
        shutil.rmtree(dst)
    manifest = {"label": "SYNTHETIC data, Klaus Konsults", "format": "parquet", "compression": f"zstd level {zstd_level}",
                "max_part_bytes": MAX_PART_BYTES, "datasets": {}}
    for domain in ("banking", "telecom"):
        for d in sorted((src / domain).iterdir()):
            out = dst / domain / d.name; out.mkdir(parents=True)
            parts, i = [], 0
            for f in sorted(d.glob("*.parquet")):
                tbl = pq.read_table(f)
                pieces = [tbl]
                while pieces:
                    t = pieces.pop(0)
                    name = out / f"part_{i:05d}.parquet"
                    pq.write_table(t, name, compression="zstd", compression_level=zstd_level)
                    if name.stat().st_size > MAX_PART_BYTES and t.num_rows > 1:
                        name.unlink(); h = t.num_rows // 2
                        pieces[:0] = [t.slice(0, h), t.slice(h)]
                        continue
                    sha = hashlib.sha256(name.read_bytes()).hexdigest()
                    parts.append({"path": f"{domain}/{d.name}/{name.name}", "rows": t.num_rows,
                                  "bytes": name.stat().st_size, "sha256": sha}); i += 1
            manifest["datasets"][d.name] = {"domain": domain, "rows": sum(p["rows"] for p in parts), "parts": parts}
    (dst / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return dst


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description="SYNTHETIC data generator (Klaus Konsults)")
    ap.add_argument("--mode", choices=["sample", "full"], default="sample")
    ap.add_argument("--scale", type=float, default=None, help="override scale, sample default is 0.001")
    ap.add_argument("--out", default=None)
    ap.add_argument("--export-csv", default=None, help="also write one CSV per dataset to this folder (e.g. data/sample)")
    ap.add_argument("--export-full", default=None, help="write committed full parts and manifest to this folder (e.g. data/full)")
    ap.add_argument("--reuse", action="store_true", help="skip generation and reuse data already in the output folder")
    args = ap.parse_args(argv)
    cfg = load_config()
    scale = args.scale if args.scale is not None else (1.0 if args.mode == "full" else 0.0025)
    out = Path(args.out) if args.out else ROOT / cfg["output_dir"] / args.mode
    if args.reuse and (out / "row_counts.json").exists():
        import json
        counts = json.loads((out / "row_counts.json").read_text())
        if args.export_csv:
            export_csv(out, Path(args.export_csv))
        if args.export_full:
            export_full(out, Path(args.export_full))
        return counts
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    chunk = int(cfg["chunk_rows"])
    t0 = time.time()
    counts = {}
    # separate seeded streams so banking and telecom stay independent
    counts.update(gen_banking(cfg, scale, out, np.random.default_rng(cfg["seed"]), chunk))
    counts.update(gen_telecom(cfg, scale, out, np.random.default_rng(cfg["seed"] + 1), chunk))
    secs = time.time() - t0
    pd.Series(counts, name="rows").to_json(out / "row_counts.json")
    if args.export_csv:
        export_csv(out, Path(args.export_csv))
    if args.export_full:
        export_full(out, Path(args.export_full))
    for k, v in counts.items():
        print(f"{k}\t{v}")
    print(f"generate_seconds\t{secs:.1f}")
    return counts


if __name__ == "__main__":
    main()
