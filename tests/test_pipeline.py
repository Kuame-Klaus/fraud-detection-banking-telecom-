"""Tests run on a tiny SYNTHETIC dataset generated into a temp folder."""
from pathlib import Path

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
    assert len(charts.main(["--results", str(path), "--out", str(tmp_path / "c")])) == 8


def test_release_package_splits(data, tmp_path):
    out, _ = data
    generate.package_release(out, tmp_path / "rel", part_bytes=1_000_000)
    import json
    m = json.loads((tmp_path / "rel/manifest.json").read_text())
    assert len(m["parts"]) > 1 and all(p["bytes"] <= 1_000_000 for p in m["parts"])
