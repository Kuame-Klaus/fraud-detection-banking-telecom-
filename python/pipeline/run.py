"""Run the six pipeline steps end to end and write one shared results file (SYNTHETIC data).

    python -m python.pipeline.run --data data/synthetic/sample --out outputs/sample
"""
from __future__ import annotations

import argparse
import datetime as dt
import resource
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import dq, features, load, model, rules
from .output import write_results

ROOT = Path(__file__).resolve().parents[2]
BENFORD = {d: float(np.log10(1 + 1 / d)) for d in range(1, 10)}


def peak_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data/synthetic/sample"))
    ap.add_argument("--out", default=str(ROOT / "outputs/sample"))
    ap.add_argument("--run-id", default=None)
    a = ap.parse_args(argv)
    run_id = a.run_id or "python_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows, stage_t = [], {}
    found = load.discover(Path(a.data))
    T0 = time.time()

    # 1 load and control totals
    t = time.time(); D = {}
    for name, (domain, path) in found.items():
        D[name] = (domain, load.read(path))
    ctl = {n: load.control_totals(n, df) for n, (_, df) in D.items()}
    stage_t["load"] = time.time() - t

    # 2 data quality
    t = time.time()
    for n, (domain, df) in D.items():
        rows += dq.checks(n.split("_")[0], n, domain, df, ctl[n])
    stage_t["data_quality"] = time.time() - t

    # 3 features
    t = time.time()
    b1 = features.banking_features(D["B1_transactions"][1], D["B2_accounts"][1])
    t4 = features.telecom_features(D["T4_momo_wallet_txns"][1], D["T5_wallets"][1], D["T3_sims_and_sim_swap_events"][1])
    stage_t["features"] = time.time() - t

    # 4 rules
    t = time.time()
    t1 = D["T1_cdrs"][1]; t1.attrs["leaky_routes"] = rules.leaky_routes(t1, D["T8_interconnect_traffic"][1])
    b8 = D["B8_users_access"][1]; b7 = D["B7_gl_journal"][1]
    b7.attrs["privileged_users"] = list(b8.loc[b8["permission"] == "admin_gl", "user_id"])
    tables = {"B1": ("banking", b1), "B4": ("banking", D["B4_auth_events"][1]), "B7": ("banking", b7),
              "B10": ("banking", D["B10_vendors_and_payments"][1]), "B11": ("banking", D["B11_payroll_and_hr"][1]),
              "T1": ("telecom", t1), "T3": ("telecom", D["T3_sims_and_sim_swap_events"][1]), "T4": ("telecom", t4),
              "T6": ("telecom", D["T6_agents"][1]), "T7": ("telecom", D["T7_topups_billing"][1])}
    idcol = {"B1": "txn_id", "B4": "event_id", "B7": "line_id", "B10": "payment_id", "B11": None, "T1": "cdr_id",
             "T3": "swap_id", "T4": "txn_id", "T6": None, "T7": None}
    covered = set()
    for scen, rid, tb, ent, etype, tcol, acol, f in rules.RULES:
        domain, d = tables[tb]
        flag = f(d).reindex(d.index).fillna(False).astype(bool).to_numpy()
        lab = d["synthetic_scenario"].to_numpy()
        tp = int((flag & (lab == scen)).sum()); planted = int((lab == scen).sum()); alerts = int(flag.sum())
        covered.add(scen)
        base = {"domain": domain, "model": "rule", "rule_id": rid, "scenario": scen, "split": "all"}
        for m, v in [("planted_rows", planted), ("alerts", alerts), ("recall", tp / planted if planted else np.nan),
                     ("precision", tp / alerts if alerts else np.nan)]:
            rows.append({"record_type": "metric", **base, "metric": m, "value": float(v), "dataset_id": tb})
        for pct in (-20, -10, 0, 10, 20):
            pass  # threshold sweep is recorded for models below; rules use fixed ASSUMPTION thresholds
        hit = d.loc[flag]
        rid_col = hit[idcol[tb]].astype(str) if idcol[tb] else hit.index.astype(str).map(lambda i: f"{tb}_row_{i}")
        sc = pd.DataFrame({"record_type": "score", "domain": domain, "dataset_id": tb, "model": "rule", "rule_id": rid,
                           "scenario": scen, "split": "all", "record_id": rid_col.to_numpy(), "entity_id": hit[ent].astype(str).to_numpy(),
                           "entity_type": etype, "event_timestamp": hit[tcol].dt.strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy(),
                           "month": hit[tcol].dt.strftime("%Y-%m").to_numpy(), "score": 1.0, "threshold": 1.0,
                           "predicted_label": 1, "true_label": (hit["synthetic_scenario"] != "").astype(int).to_numpy(),
                           "true_scenario": hit["synthetic_scenario"].to_numpy(),
                           "amount": hit[acol].astype(float).to_numpy() if acol else np.nan})
        rows.append(sc)
    stage_t["rules"] = time.time() - t

    # 5 model
    t = time.time()
    for domain, d, feats, tcol, ent, etype, tb in [("banking", b1, features.BANK_FEATURES, "timestamp", "account_id", "account", "B1"),
                                                   ("telecom", t4, features.TEL_FEATURES, "timestamp", "wallet_id", "wallet", "T4")]:
        mt = time.time()
        score, y, sp, thr, ntr, clf = model.fit_score(d, feats, tcol)
        pred = (score >= thr).astype(int)
        lab = d["synthetic_scenario"].to_numpy()
        for s in ("train", "validation", "test"):
            m = model.metrics(y, score, pred, sp == s)
            for k, v in m.items():
                rows.append({"record_type": "metric", "domain": domain, "model": "xgboost", "scenario": "all", "split": s,
                             "metric": k, "value": float(v), "alert_rate": m["alert_rate"], "train_rows": ntr,
                             "sample_method": "none", "dataset_id": tb})
        test = sp == "test"
        for scen in sorted(set(lab[lab != ""])):
            mk = test & (lab == scen)
            if mk.sum():
                rows.append({"record_type": "metric", "domain": domain, "model": "xgboost", "scenario": scen, "split": "test",
                             "metric": "recall", "value": float(pred[mk].mean()), "dataset_id": tb})
        for pct in (-20, -10, 0, 10, 20):
            th = thr * (1 + pct / 100); p = score[test] >= th
            rows.append({"record_type": "threshold", "domain": domain, "model": "xgboost", "scenario": "all",
                         "threshold_change_pct": float(pct), "threshold": float(th), "alert_count": int(p.sum()),
                         "detected_count": int((p & (y[test] == 1)).sum())})
        dd = d.loc[test]
        rows.append(pd.DataFrame({"record_type": "score", "domain": domain, "dataset_id": tb, "model": "xgboost", "scenario": "all",
                                  "split": "test", "record_id": dd["txn_id"].to_numpy(), "entity_id": dd[ent].to_numpy(), "entity_type": etype,
                                  "event_timestamp": dd[tcol].dt.strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy(),
                                  "month": dd[tcol].dt.strftime("%Y-%m").to_numpy(), "score": score[test], "threshold": thr,
                                  "predicted_label": pred[test], "true_label": y[test], "true_scenario": lab[test],
                                  "amount": dd["amount"].to_numpy(), "currency": dd["currency"].to_numpy() if "currency" in dd else "GHS"}))
        # drift: score band share per month (all splits)
        bands = pd.cut(score, np.linspace(0, 1, 11), include_lowest=True, labels=[f"{i/10:.1f} to {(i+1)/10:.1f}" for i in range(10)])
        mon = d[tcol].dt.strftime("%Y-%m").to_numpy()
        tab = pd.crosstab(mon, bands, normalize="index")
        for mo, r in tab.iterrows():
            for b, v in r.items():
                rows.append({"record_type": "drift", "domain": domain, "model": "xgboost", "month": mo, "score_band": str(b), "band_share": float(v)})
        rows.append({"record_type": "metric", "domain": domain, "model": "xgboost", "metric": "train_seconds", "value": time.time() - mt,
                     "runtime_seconds": time.time() - mt, "train_rows": ntr, "dataset_id": tb})
    stage_t["model"] = time.time() - t

    # 6 extras for charts: coverage, benford, edges, geo
    t = time.time()
    for domain in ("banking", "telecom"):
        import yaml
        cfg = yaml.safe_load(open(ROOT / "python/synthetic/config.yaml"))
        for scen in cfg["scenarios"][domain]:
            rows.append({"record_type": "coverage", "domain": domain, "scenario": scen, "covered": scen in covered,
                         "note": "rule present" if scen in covered else "no rule yet"})
    for tb, domain, d, col in [("B1", "banking", b1, "amount"), ("B7", "banking", b7, "debit"), ("T4", "telecom", t4, "amount")]:
        fd = features.first_digit(d[col].to_numpy())
        cnt = np.bincount(fd, minlength=10)
        for k in range(1, 10):
            rows.append({"record_type": "benford", "domain": domain, "dataset_id": tb, "first_digit": k,
                         "observed_count": int(cnt[k]), "expected_share": BENFORD[k]})
    mule = b1[b1["synthetic_scenario"].eq("mule_network") | (b1["direction"].eq("debit") & (b1["amount"] > 5000))]
    e = mule[mule["direction"] == "debit"].groupby(["account_id", "counterparty_account"])["amount"].agg(["sum", "size"]).reset_index()
    rows.append(pd.DataFrame({"record_type": "edge", "domain": "banking", "entity_type": "account", "source_id": e["account_id"],
                              "target_id": e["counterparty_account"], "edge_weight": e["sum"], "edge_count": e["size"]}))
    ea = t4[t4["agent_day_count"] >= 8].groupby(["agent_id", "wallet_id"])["amount"].agg(["sum", "size"]).reset_index()
    rows.append(pd.DataFrame({"record_type": "edge", "domain": "telecom", "entity_type": "agent", "source_id": ea["agent_id"],
                              "target_id": ea["wallet_id"], "edge_weight": ea["sum"], "edge_count": ea["size"]}))
    t8 = D["T8_interconnect_traffic"][1]
    g1 = t1.assign(day=t1["start_time"].dt.strftime("%Y-%m-%d")).groupby(["route", "day"])["duration_sec"].sum().div(60)
    g8 = t8.assign(day=pd.to_datetime(t8["traffic_date"]).dt.strftime("%Y-%m-%d")).groupby(["route", "day"])["minutes"].sum()
    geo = pd.concat([g1.rename("geo_minutes"), g8.rename("geo_settled_minutes")], axis=1).reset_index()
    rows.append(pd.DataFrame({"record_type": "geo", "domain": "telecom", "dataset_id": "T1", "route": geo["route"],
                              "month": geo["day"], "geo_minutes": geo["geo_minutes"], "geo_settled_minutes": geo["geo_settled_minutes"],
                              "note": "latitude and longitude not available, see docs/open_questions.md"}))
    stage_t["output"] = time.time() - t
    for st, s in stage_t.items():
        rows.append({"record_type": "run", "stage": st, "runtime_seconds": s, "peak_memory_mb": peak_mb()})
    rows.append({"record_type": "run", "stage": "total", "runtime_seconds": time.time() - T0, "peak_memory_mb": peak_mb(),
                 "note": f"input rows {sum(c['rows'] for c in ctl.values())}"})
    path = write_results(rows, Path(a.out), run_id)
    print(f"results: {path}")
    for st, s in stage_t.items():
        print(f"{st}\t{s:.1f}s")
    print(f"total\t{time.time() - T0:.1f}s\tpeak_mb\t{peak_mb():.0f}")
    return path


if __name__ == "__main__":
    main()
