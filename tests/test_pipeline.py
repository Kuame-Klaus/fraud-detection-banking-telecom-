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
