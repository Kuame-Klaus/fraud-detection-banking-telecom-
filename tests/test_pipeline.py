"""Tests run on a tiny SYNTHETIC dataset generated into a temp folder."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from python.pipeline import run
from python.synthetic import generate
from python.viz import charts

ROOT = Path(__file__).resolve().parents[1]
DICT = (ROOT / "docs/data_dictionary.md").read_text()


@pytest.fixture(scope="session")
def data(tmp_path_factory):
    out = tmp_path_factory.mktemp("syn")
    counts = generate.main(["--mode", "sample", "--out", str(out)])
    return out, counts


def test_all_datasets_generated(data):
    _, counts = data
    assert len(counts) == 26
    assert {k.split("_")[0] for k in counts} == {f"B{i}" for i in range(1, 15)} | {f"T{i}" for i in range(1, 13)}


def test_seeded_and_reproducible(tmp_path, data):
    out, _ = data
    generate.main(["--mode", "sample", "--out", str(tmp_path)])
    a = pd.read_parquet(out / "banking/B1_transactions"); b = pd.read_parquet(tmp_path / "banking/B1_transactions")
    pd.testing.assert_frame_equal(a, b)


def test_columns_in_data_dictionary(data):
    out, _ = data
    for p in list((out / "banking").iterdir()) + list((out / "telecom").iterdir()):
        for c in pd.read_parquet(p).columns:
            if c not in ("synthetic", "synthetic_scenario"):
                assert c in DICT, f"{p.name}.{c} missing from docs/data_dictionary.md"


def test_every_scenario_planted(data):
    import yaml
    out, _ = data
    cfg = yaml.safe_load(open(ROOT / "python/synthetic/config.yaml"))
    for dom in ("banking", "telecom"):
        labels = set()
        for p in (out / dom).iterdir():
            df = pd.read_parquet(p)
            if "synthetic_scenario" in df:
                labels |= set(df["synthetic_scenario"].unique())
        missing = set(cfg["scenarios"][dom]) - labels
        assert not missing, f"{dom} scenarios not planted: {missing}"


def test_domains_share_no_keys(data):
    out, _ = data
    b = pd.read_parquet(out / "banking/B3_persons")["person_id"]
    t = pd.read_parquet(out / "telecom/T2_subscribers")["person_id"]
    assert not set(b) & set(t)


def test_all_rows_marked_synthetic(data):
    out, _ = data
    for p in list((out / "banking").iterdir()) + list((out / "telecom").iterdir()):
        assert pd.read_parquet(p)["synthetic"].all()


def test_pipeline_and_charts(data, tmp_path):
    out, _ = data
    path = run.main(["--data", str(out), "--out", str(tmp_path), "--run-id", "test"])
    d = pd.read_parquet(path)
    assert {"score", "metric", "dq", "coverage", "benford", "run", "threshold", "drift", "edge", "geo"} <= set(d.record_type)
    assert (d["stack"] == "python").all()
    assert d.loc[d.record_type == "dq", "passed"].astype(bool).all()
    assert len(charts.main(["--results", str(path), "--out", str(tmp_path / "c")])) == 11


def test_export_full_parts_and_manifest(data, tmp_path):
    import json
    from python.pipeline import load
    out, counts = data
    generate.export_full(out, tmp_path / "full")
    m = json.loads((tmp_path / "full/manifest.json").read_text())
    assert len(m["datasets"]) == 26
    for name, d in m["datasets"].items():
        assert d["rows"] == counts[name]
        assert all(p["bytes"] <= generate.MAX_PART_BYTES for p in d["parts"])
    b1 = load.read_manifest_dataset(tmp_path / "full", "B1_transactions", verify=True)
    assert len(b1) == counts["B1_transactions"]


def test_chunked_path_matches_single_chunk(data, tmp_path):
    """Split every table into 4 part files and use small buckets: rule results must equal the one chunk run."""
    out, _ = data
    split_dir = tmp_path / "parts"
    for dom in ("banking", "telecom"):
        for p in (out / dom).iterdir():
            df = pd.read_parquet(p); (split_dir / dom / p.name).mkdir(parents=True)
            for i, ix in enumerate(np.array_split(np.arange(len(df)), 4)):
                part = df.iloc[ix]
                part.to_parquet(split_dir / dom / p.name / f"part_{i:05d}.parquet", index=False)
    one = pd.read_parquet(run.main(["--data", str(out), "--out", str(tmp_path / "o1"), "--run-id", "one"]))
    many = pd.read_parquet(run.main(["--data", str(split_dir), "--out", str(tmp_path / "o2"), "--run-id", "many",
                                     "--bucket-rows", "3000", "--max-train-rows", "20000"]))
    k = ["rule_id", "scenario", "metric"]
    a = one[(one.record_type == "metric") & (one.model == "rule")].set_index(k)["value"].sort_index()
    b = many[(many.record_type == "metric") & (many.model == "rule")].set_index(k)["value"].sort_index()
    pd.testing.assert_series_equal(a, b)
    assert many.loc[many.record_type == "dq", "passed"].astype(bool).all()
    # every test split row is scored in both runs
    sc = lambda d: d[(d.record_type == "score") & (d.model == "xgboost")].groupby("domain").size()
    pd.testing.assert_series_equal(sc(one), sc(many))
    # stratified sampling is recorded
    assert set(many.loc[(many.record_type == "metric") & (many.model == "xgboost"), "sample_method"].dropna()) <= {"none", "stratified"}


def test_insider_and_imei_rules_catch_plants(data):
    from python.pipeline import rules
    out, _ = data
    d = pd.read_parquet(out / "telecom/T3_sims_and_sim_swap_events")
    for f, s in [(rules.insider, "insider_sim_swap_or_access_abuse"), (rules.imei, "imei_churn")]:
        flag = f(d).astype(bool); y = d["synthetic_scenario"] == s
        assert y.sum() > 0 and (flag & y).sum() == y.sum()


def test_model_detected_matches_recall(data, tmp_path):
    out, _ = data
    d = pd.read_parquet(run.main(["--data", str(out), "--out", str(tmp_path / "o"), "--run-id", "det"]))
    m = d[(d.record_type == "metric") & (d.model == "xgboost") & (d.scenario == "all")]
    for (dom, sp), g in m.groupby(["domain", "split"]):
        v = g.set_index("metric")["value"]
        if "recall" in v:
            assert v["detected"] == round(v["recall"] * v["positives"])


def test_leakage_rule_route_day(data):
    from python.pipeline import rules
    out, _ = data
    t1 = pd.read_parquet(out / "telecom/T1_cdrs"); t8 = pd.read_parquet(out / "telecom/T8_interconnect_traffic")
    assert t8["route"].nunique() == t1["route"].nunique()  # every route has a settlement row
    m = t1.groupby([t1["route"], pd.to_datetime(t1["start_time"], utc=True).dt.strftime("%Y-%m-%d").rename("day")])["duration_sec"].sum() / 60
    g = rules.leak_route_day(m, t8)
    y = g["synthetic_scenario"] == "interconnect_leakage"
    assert y.sum() > 0 and (g["flag"] & y).sum() == y.sum()
    assert (g.loc[~y, "unsettled_minutes"] >= 0).all() and (g.loc[y, "unsettled_share"] > 0.35).all()


def test_rule_versions_default_beats_v1(data, tmp_path):
    """Default rules (approved) and v1 both run; the four changed rules catch every plant with fewer or equal false alerts."""
    out, _ = data
    res = {}
    for v in ("default", "v1"):
        d = pd.read_parquet(run.main(["--data", str(out), "--out", str(tmp_path / v), "--run-id", v, "--rules", v]))
        m = d[(d.record_type == "metric") & (d.model == "rule")]
        res[v] = m.pivot_table(index="rule_id", columns="metric", values="value", aggfunc="first")
    new, old = res["default"], res["v1"]
    for rid in ("R_B06", "R_B09", "R_B16", "R_T01"):
        assert new.loc[rid, "recall"] == 1.0
        assert new.loc[rid, "recall"] >= old.loc[rid, "recall"]
    for rid in ("R_B06", "R_B09", "R_B16"):
        assert new.loc[rid, "precision"] > old.loc[rid, "precision"]
    other = [r for r in new.index if r not in ("R_B06", "R_B09", "R_B16", "R_T01")]
    pd.testing.assert_frame_equal(new.loc[other], old.loc[other])


def test_benford_account_month_flags_planted_cluster():
    from python.pipeline import rules
    rng = np.random.default_rng(0)
    n = 2000
    amt = np.exp(rng.uniform(np.log(10), np.log(100000), n))  # log uniform follows Benford
    d = pd.DataFrame({"account_id": rng.integers(0, 200, n).astype(str), "amount": amt,
                      "timestamp": pd.Timestamp("2025-03-01") + pd.to_timedelta(rng.integers(0, 28 * 86400, n), unit="s")})
    plant = pd.DataFrame({"account_id": "X", "amount": [700.5, 812.0, 7450.0, 8100.0, 760.0, 7020.0, 880.0, 8890.0, 790.0, 7300.0],
                          "timestamp": pd.Timestamp("2025-03-05")})
    d = pd.concat([d, plant], ignore_index=True)
    f = rules.benford_account_month(d)
    assert f[d.account_id == "X"].all() and f[d.account_id != "X"].sum() == 0
