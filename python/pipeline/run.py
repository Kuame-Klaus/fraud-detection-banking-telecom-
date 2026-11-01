"""Run the six pipeline steps end to end, one table and one chunk at a time (SYNTHETIC data).

    python -m python.pipeline.run --data data/sample --out outputs/sample
    python -m python.pipeline.run --data data/full   --out outputs/full

Memory stays bounded: every large table is streamed chunk by chunk (one manifest part at a time). Tables that
need per entity history (B1, B4, T1, T4, T7) are first split by a hash of their entity key into buckets on
disk, so each bucket holds every row of the entities in it and per entity features stay exact. Global
aggregates (DQ counters, Benford counts, agent day counts, route minutes) are summed chunk by chunk.
XGBoost trains on a recorded stratified sample when the training split is large, then scores every row."""
from __future__ import annotations

import argparse
import datetime as dt
import math
import resource
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import dq, features, load, model, rules
from .output import ResultsWriter

ROOT = Path(__file__).resolve().parents[2]
BENFORD = {d: float(np.log10(1 + 1 / d)) for d in range(1, 10)}
BUCKET_KEY = {"B1_transactions": "account_id", "B4_auth_events": "person_id", "B7_gl_journal": "preparer_id",
              "B10_vendors_and_payments": "vendor_id", "B11_payroll_and_hr": "employee_id", "T1_cdrs": "caller",
              "T3_sims_and_sim_swap_events": None, "T4_momo_wallet_txns": "wallet_id", "T6_agents": "agent_id",
              "T7_topups_billing": "msisdn"}
SHORT = {k: k.split("_")[0] for k in BUCKET_KEY}
IDCOL = {"B1": "txn_id", "B4": "event_id", "B7": "line_id", "B10": "payment_id", "T1": "cdr_id", "T3": "swap_id", "T4": "txn_id"}
BANDS = np.linspace(0, 1, 11)
BAND_LABELS = [f"{i/10:.1f} to {(i+1)/10:.1f}" for i in range(10)]


def peak_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


class Buckets:
    """Hash partition of one table on disk. With one bucket, chunks are read straight from the source."""

    def __init__(self, src: load.Source, name: str, key, nb: int, tmp: Path):
        self.src, self.name, self.key, self.nb = src, name, key, nb
        self.dir = tmp / name; self.i = 0
        if nb > 1:
            for b in range(nb):
                (self.dir / f"b{b:04d}").mkdir(parents=True, exist_ok=True)

    def add(self, chunk: pd.DataFrame) -> None:
        if self.nb == 1:
            return
        b = pd.util.hash_pandas_object(chunk[self.key], index=False).to_numpy() % self.nb
        for k in np.unique(b):
            chunk[b == k].to_parquet(self.dir / f"b{k:04d}" / f"c{self.i:05d}.parquet", index=False)
        self.i += 1

    def __iter__(self):
        if self.nb == 1:
            yield self.src.read_all(self.name)
        else:
            for b in range(self.nb):
                files = sorted((self.dir / f"b{b:04d}").glob("*.parquet"))
                if files:
                    yield pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def score_frame(d, tb, domain, ent, etype, tcol, acol, rid, scen, flag):
    hit = d.loc[flag]
    rid_col = hit[IDCOL[tb]].astype(str).to_numpy() if tb in IDCOL else np.array([f"{tb}_row_{i}" for i in hit.index])
    return pd.DataFrame({"record_type": "score", "domain": domain, "dataset_id": tb, "model": "rule", "rule_id": rid,
                         "scenario": scen, "split": "all", "record_id": rid_col, "entity_id": hit[ent].astype(str).to_numpy(),
                         "entity_type": etype, "event_timestamp": hit[tcol].dt.strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy(),
                         "month": hit[tcol].dt.strftime("%Y-%m").to_numpy(), "score": 1.0, "threshold": 1.0,
                         "predicted_label": 1, "true_label": (hit["synthetic_scenario"] != "").astype(int).to_numpy(),
                         "true_scenario": hit["synthetic_scenario"].to_numpy(),
                         "amount": hit[acol].astype(float).to_numpy() if acol else np.nan})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data/sample"))
    ap.add_argument("--out", default=str(ROOT / "outputs/sample"))
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--bucket-rows", type=int, default=1_500_000, help="target rows per entity bucket")
    ap.add_argument("--max-train-rows", type=int, default=2_000_000, help="stratified sample cap for XGBoost training")
    ap.add_argument("--csv-scores", choices=["auto", "yes", "no"], default="auto",
                    help="write score rows to the CSV too (auto: only when the run is small)")
    ap.add_argument("--rules", choices=["default", "proposed"], default="default",
                    help="proposed swaps in the candidate R_B06, R_B09, R_B16 and R_T01 from docs/threshold_proposals.md")
    a = ap.parse_args(argv)
    run_id = a.run_id or "python_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(a.out); tmp = out / f"_tmp_{run_id}"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    src = load.Source(Path(a.data))
    W = ResultsWriter(out, run_id)
    st, T0 = {}, time.time()
    cfg = yaml.safe_load(open(ROOT / "python/synthetic/config.yaml"))

    # Steps 1 and 2: stream every table once: control totals, DQ, global aggregates and bucket split
    t = time.time()
    small = {}
    buckets = {}
    benford = {k: np.zeros(10, dtype=np.int64) for k in ("B1", "B7", "T4")}
    agent_day, route_min, geo1 = [], [], []
    total_rows = 0
    for name, (domain, _) in src.datasets.items():
        q = dq.DQ(name.split("_")[0], name, domain, load.AMOUNT_COLS.get(name), src.expected_rows(name))
        if name in BUCKET_KEY:
            key = BUCKET_KEY[name]
            nb = 1 if key is None else max(1, math.ceil(src.rows(name) / a.bucket_rows))
            buckets[name] = Buckets(src, name, key, nb, tmp)
        for chunk in src.chunks(name):
            q.update(chunk); total_rows += len(chunk)
            if name in buckets:
                buckets[name].add(chunk)
            if name == "B1_transactions":
                benford["B1"] += np.bincount(features.first_digit(chunk["amount"].to_numpy()), minlength=10)
            elif name == "B7_gl_journal":
                benford["B7"] += np.bincount(features.first_digit(chunk["debit"].to_numpy()), minlength=10)
            elif name == "T4_momo_wallet_txns":
                benford["T4"] += np.bincount(features.first_digit(chunk["amount"].to_numpy()), minlength=10)
                agent_day.append(chunk.groupby([chunk["agent_id"], chunk["timestamp"].dt.floor("D").rename("day")]).size())
            elif name == "T1_cdrs":
                route_min.append(chunk.groupby("route")["duration_sec"].sum() / 60)
                geo1.append(chunk.groupby([chunk["route"], chunk["start_time"].dt.strftime("%Y-%m-%d").rename("day")])["duration_sec"].sum() / 60)
            del chunk
        for r in q.finish():
            W.add(r)
    for n in ("B2_accounts", "B8_users_access", "T3_sims_and_sim_swap_events", "T5_wallets", "T8_interconnect_traffic"):
        small[n] = src.read_all(n)
    agent_day_s = pd.concat(agent_day).groupby(level=[0, 1]).sum()
    route_min_s = pd.concat(route_min).groupby(level=0).sum()
    geo1_s = pd.concat(geo1).groupby(level=[0, 1]).sum()
    del agent_day, route_min, geo1
    st["load"] = time.time() - t  # load, control totals and DQ share one streaming pass
    st["data_quality"] = 0.0

    # Steps 3 and 4: per table, per bucket: features (B1, T4) and rules
    t_feat = 0.0; t = time.time()
    leaky = rules.leaky_routes_from(route_min_s, small["T8_interconnect_traffic"])
    b8 = small["B8_users_access"]; priv = list(b8.loc[b8["permission"] == "admin_gl", "user_id"])
    last_swap = small["T3_sims_and_sim_swap_events"].groupby("msisdn")["swap_time"].max()
    domain_of = {n: src.datasets[n][0] for n in BUCKET_KEY}
    stats, covered = {}, set()
    srng = np.random.default_rng(cfg["seed"])
    model_in = {"B1": {"train": [], "validation": [], "files": []}, "T4": {"train": [], "validation": [], "files": []}}
    frac = {}
    for tb, n in (("B1", "B1_transactions"), ("T4", "T4_momo_wallet_txns")):
        est_neg_train = src.rows(n) * 0.75
        frac[tb] = min(1.0, a.max_train_rows / max(est_neg_train, 1))
    edges = {"B1": [], "T4": []}
    by_table = {}
    for r in rules.RULES:
        by_table.setdefault(r[2], []).append(r)
    for name, bk in buckets.items():
        tb = SHORT[name]; domain = domain_of[name]
        for bi, d in enumerate(bk):
            if tb == "B1":
                tf = time.time(); d = features.banking_features(d, small["B2_accounts"]); t_feat += time.time() - tf
                feats = features.BANK_FEATURES
            elif tb == "T4":
                tf = time.time(); d = features.telecom_features(d, small["T5_wallets"], last_swap, agent_day_s,
                                                swaps=small["T3_sims_and_sim_swap_events"] if a.rules == "proposed" else None); t_feat += time.time() - tf
                feats = features.TEL_FEATURES
            d.attrs["leaky_routes"] = leaky; d.attrs["privileged_users"] = priv
            lab = d["synthetic_scenario"].to_numpy()
            for scen, rid, _, ent, etype, tcol, acol, f in by_table.get(tb, []):
                if a.rules == "proposed": f = rules.PROPOSED.get(rid, f)
                flag = f(d).reindex(d.index).fillna(False).astype(bool).to_numpy()
                s = stats.setdefault((rid, scen, tb, domain), [0, 0, 0])
                s[0] += int((flag & (lab == scen)).sum()); s[1] += int((lab == scen).sum()); s[2] += int(flag.sum())
                covered.add(scen)
                W.write(score_frame(d, tb, domain, ent, etype, tcol, acol, rid, scen, flag))
            if tb in model_in:
                tcol = "timestamp"
                sp = model.split(d[tcol]); y = (lab != "").astype(np.int8)
                keep = (y == 1) | (srng.random(len(d)) < frac[tb])
                for s_name in ("train", "validation"):
                    m = (sp == s_name) & keep
                    model_in[tb][s_name].append((d.loc[m, feats].astype(np.float32), y[m]))
                cols = feats + ["txn_id", "timestamp", "amount", "synthetic_scenario"] + (["account_id", "currency"] if tb == "B1" else ["wallet_id"])
                fp = tmp / f"feat_{tb}_{bi:04d}.parquet"; d[cols].to_parquet(fp, index=False); model_in[tb]["files"].append(fp)
                if tb == "B1":
                    mule = d[d["synthetic_scenario"].eq("mule_network") | (d["direction"].eq("debit") & (d["amount"] > 5000))]
                    edges["B1"].append(mule[mule["direction"] == "debit"].groupby(["account_id", "counterparty_account"])["amount"].agg(["sum", "size"]).reset_index())
                else:
                    edges["T4"].append(d[d["agent_day_count"] >= 8].groupby(["agent_id", "wallet_id"])["amount"].agg(["sum", "size"]).reset_index())
            del d
    # R_T08 interconnect leakage at route and day level (T1 minutes versus T8 settlement)
    g = rules.leak_route_day(geo1_s, small["T8_interconnect_traffic"]); covered.add("interconnect_leakage")
    lab8 = (g["synthetic_scenario"] == "interconnect_leakage").to_numpy(); f8 = g["flag"].to_numpy()
    stats[("R_T08", "interconnect_leakage", "T8", "telecom")] = [int((f8 & lab8).sum()), int(lab8.sum()), int(f8.sum())]
    h = g[f8]
    W.write(pd.DataFrame({"record_type": "score", "domain": "telecom", "dataset_id": "T8", "model": "rule", "rule_id": "R_T08",
                          "scenario": "interconnect_leakage", "split": "all", "record_id": (h["route"] + "_" + h["day"]).to_numpy(),
                          "entity_id": h["route"].to_numpy(), "entity_type": "route",
                          "event_timestamp": (h["day"] + "T00:00:00Z").to_numpy(), "month": h["day"].str[:7].to_numpy(),
                          "score": 1.0, "threshold": 1.0, "predicted_label": 1,
                          "true_label": (h["synthetic_scenario"] != "").astype(int).to_numpy(),
                          "true_scenario": h["synthetic_scenario"].to_numpy(), "amount": h["unsettled_minutes"].to_numpy(),
                          "note": "amount is unsettled minutes for the route day"}))
    W.add({"record_type": "metric", "domain": "telecom", "model": "rule", "rule_id": "R_T08", "scenario": "interconnect_leakage",
           "split": "all", "dataset_id": "T8", "metric": "route_days_without_settlement_row", "value": float(g.attrs["no_settlement_row"])})
    for (rid, scen, tb, domain), (tp, planted, alerts) in stats.items():
        base = {"record_type": "metric", "domain": domain, "model": "rule", "rule_id": rid, "scenario": scen, "split": "all", "dataset_id": tb}
        for m, v in [("planted_rows", planted), ("alerts", alerts), ("detected", tp), ("recall", tp / planted if planted else np.nan),
                     ("precision", tp / alerts if alerts else np.nan)]:
            W.add({**base, "metric": m, "value": float(v)})
    st["features"] = t_feat
    st["rules"] = time.time() - t - t_feat

    # Step 5: XGBoost per domain: train on a recorded stratified sample, score every row
    t = time.time()
    summary_model = []
    for domain, tb, feats, ent, etype in (("banking", "B1", features.BANK_FEATURES, "account_id", "account"),
                                          ("telecom", "T4", features.TEL_FEATURES, "wallet_id", "wallet")):
        mt = time.time(); mi = model_in[tb]
        Xtr = pd.concat([x for x, _ in mi["train"]], ignore_index=True); ytr = np.concatenate([y for _, y in mi["train"]])
        Xva = pd.concat([x for x, _ in mi["validation"]], ignore_index=True); yva = np.concatenate([y for _, y in mi["validation"]])
        mi["train"] = mi["validation"] = None
        clf = model.fit(Xtr, ytr, Xva, yva, seed=cfg["seed"])
        ntr = len(ytr); method = "none" if frac[tb] >= 1 else "stratified"
        del Xtr, Xva
        scores, ys, sps, labs = [], [], [], []
        for fp in mi["files"]:
            d = pd.read_parquet(fp)
            scores.append(clf.predict_proba(d[feats].astype(np.float32))[:, 1].astype(np.float64))
            ys.append((d["synthetic_scenario"].to_numpy() != "").astype(np.int8)); sps.append(model.split(d["timestamp"]))
            labs.append(d["synthetic_scenario"].to_numpy())
        score = np.concatenate(scores); y = np.concatenate(ys); sp = np.concatenate(sps); lab = np.concatenate(labs)
        va = sp == "validation"
        thr = float(np.quantile(score[va], 0.99)) if va.any() else 0.5
        pred = (score >= thr).astype(np.int8)
        for s_name in ("train", "validation", "test"):
            m = model.metrics(y, score, pred, sp == s_name)
            m["alerts"] = int(pred[sp == s_name].sum())
            m["detected"] = int((pred[sp == s_name] == 1)[y[sp == s_name] == 1].sum())  # true positives, so recall = detected / positives
            for k, v in m.items():
                W.add({"record_type": "metric", "domain": domain, "model": "xgboost", "scenario": "all", "split": s_name,
                       "metric": k, "value": float(v), "alert_rate": m["alert_rate"], "train_rows": ntr,
                       "sample_method": method, "dataset_id": tb,
                       "note": f"negative sample fraction {frac[tb]:.6f}; all positives kept; scored all rows"})
        test = sp == "test"
        for scen in sorted(set(lab[lab != ""])):
            mk = test & (lab == scen)
            if mk.sum():
                W.add({"record_type": "metric", "domain": domain, "model": "xgboost", "scenario": scen, "split": "test",
                       "metric": "recall", "value": float(pred[mk].mean()), "dataset_id": tb})
                W.add({"record_type": "metric", "domain": domain, "model": "xgboost", "scenario": scen, "split": "test",
                       "metric": "detected", "value": float(pred[mk].sum()), "dataset_id": tb})
        for pct in (-20, -10, 0, 10, 20):
            th = thr * (1 + pct / 100); p = score[test] >= th
            W.add({"record_type": "threshold", "domain": domain, "model": "xgboost", "scenario": "all",
                   "threshold_change_pct": float(pct), "threshold": float(th), "alert_count": int(p.sum()),
                   "detected_count": int((p & (y[test] == 1)).sum())})
        # score rows for the test split, and drift over all months, one bucket file at a time
        off = 0; drift = None
        for fp, sc in zip(mi["files"], scores):
            d = pd.read_parquet(fp); k = len(d); s_sp = sp[off:off + k]; s_pred = pred[off:off + k]; s_y = y[off:off + k]; off += k
            mon = d["timestamp"].dt.strftime("%Y-%m").to_numpy()
            band = pd.cut(sc, BANDS, include_lowest=True, labels=BAND_LABELS)
            ct = pd.crosstab(mon, band); drift = ct if drift is None else drift.add(ct, fill_value=0)
            m = s_sp == "test"; dd = d.loc[m]
            W.write(pd.DataFrame({"record_type": "score", "domain": domain, "dataset_id": tb, "model": "xgboost", "scenario": "all",
                                  "split": "test", "record_id": dd["txn_id"].to_numpy(), "entity_id": dd[ent].to_numpy(), "entity_type": etype,
                                  "event_timestamp": dd["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy(),
                                  "month": mon[m], "score": sc[m], "threshold": thr, "predicted_label": s_pred[m],
                                  "true_label": s_y[m], "true_scenario": dd["synthetic_scenario"].to_numpy(),
                                  "amount": dd["amount"].to_numpy(), "currency": dd["currency"].to_numpy() if "currency" in dd else "GHS"}))
        drift = drift.div(drift.sum(axis=1), axis=0)
        for mo, r in drift.iterrows():
            for b, v in r.items():
                W.add({"record_type": "drift", "domain": domain, "model": "xgboost", "month": mo, "score_band": str(b), "band_share": float(v)})
        W.add({"record_type": "metric", "domain": domain, "model": "xgboost", "metric": "train_seconds", "value": time.time() - mt,
               "runtime_seconds": time.time() - mt, "train_rows": ntr, "sample_method": method, "dataset_id": tb})
        del score, y, sp, lab, pred, scores
    st["model"] = time.time() - t

    # Step 6: coverage, Benford, edges, geo, run rows
    t = time.time()
    for domain in ("banking", "telecom"):
        for scen in cfg["scenarios"][domain]:
            W.add({"record_type": "coverage", "domain": domain, "scenario": scen, "covered": scen in covered,
                   "note": "rule present" if scen in covered else "no rule yet"})
    for tb, domain in (("B1", "banking"), ("B7", "banking"), ("T4", "telecom")):
        for k in range(1, 10):
            W.add({"record_type": "benford", "domain": domain, "dataset_id": tb, "first_digit": k,
                   "observed_count": int(benford[tb][k]), "expected_share": BENFORD[k]})
    if edges["B1"]:
        e = pd.concat(edges["B1"], ignore_index=True)
        W.write(pd.DataFrame({"record_type": "edge", "domain": "banking", "entity_type": "account", "source_id": e["account_id"],
                              "target_id": e["counterparty_account"], "edge_weight": e["sum"], "edge_count": e["size"]}))
    if edges["T4"]:
        e = pd.concat(edges["T4"], ignore_index=True)
        W.write(pd.DataFrame({"record_type": "edge", "domain": "telecom", "entity_type": "agent", "source_id": e["agent_id"],
                              "target_id": e["wallet_id"], "edge_weight": e["sum"], "edge_count": e["size"]}))
    t8 = small["T8_interconnect_traffic"]
    g8 = t8.assign(day=pd.to_datetime(t8["traffic_date"]).dt.strftime("%Y-%m-%d")).groupby(["route", "day"])["minutes"].sum()
    geo = pd.concat([geo1_s.rename("geo_minutes"), g8.rename("geo_settled_minutes")], axis=1).reset_index()
    W.write(pd.DataFrame({"record_type": "geo", "domain": "telecom", "dataset_id": "T1", "route": geo["route"],
                          "month": geo["day"], "geo_minutes": geo["geo_minutes"], "geo_settled_minutes": geo["geo_settled_minutes"],
                          "note": "latitude and longitude not available, see docs/open_questions.md"}))
    shutil.rmtree(tmp)
    st["output"] = time.time() - t
    for s_name, s in st.items():
        W.add({"record_type": "run", "stage": s_name, "runtime_seconds": s, "peak_memory_mb": peak_mb(),
               "note": "load includes data_quality (one streaming pass)" if s_name in ("load", "data_quality") else None})
    W.add({"record_type": "run", "stage": "total", "runtime_seconds": time.time() - T0, "peak_memory_mb": peak_mb(),
           "note": f"input rows {total_rows}"})
    csv_full = a.csv_scores == "yes" or (a.csv_scores == "auto" and total_rows <= 2_000_000)
    path = W.close(csv_full=csv_full)
    print(f"results: {path}")
    for s_name, s in st.items():
        print(f"{s_name}\t{s:.1f}s")
    print(f"total\t{time.time() - T0:.1f}s\tpeak_mb\t{peak_mb():.0f}\tinput_rows\t{total_rows}")
    return path


if __name__ == "__main__":
    main()
