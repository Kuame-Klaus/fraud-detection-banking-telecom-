"""First Python charts, built only from the shared results file (SYNTHETIC data).

    python -m python.viz.charts --results outputs/sample/results_python_sample.parquet --out outputs/sample/charts
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_curve

NOTE = "SYNTHETIC data, Klaus Konsults"


def _save(fig, out, name):
    fig.text(0.99, 0.01, NOTE, ha="right", va="bottom", fontsize=7, color="grey")
    fig.tight_layout(); p = out / name; fig.savefig(p, dpi=110); plt.close(fig); return p


def kpi_overview(d, out):
    s = d[(d.record_type == "score") & (d.model == "xgboost")]
    m = d[(d.record_type == "metric") & (d.model == "xgboost") & (d.split == "test") & (d.scenario == "all")]
    fig, ax = plt.subplots(figsize=(9, 3)); ax.axis("off")
    rows = []
    for dom in ("banking", "telecom"):
        ss, mm = s[s.domain == dom], m[m.domain == dom].set_index("metric")["value"]
        rows.append([dom, f"{len(ss):,}", f"{int(ss.predicted_label.sum()):,}", f"{int(ss.true_label.sum()):,}",
                     f"{mm.get('pr_auc', np.nan):.3f}", f"{mm.get('precision', np.nan):.3f}", f"{mm.get('recall', np.nan):.3f}",
                     f"{ss.loc[(ss.predicted_label == 1) & (ss.true_label == 1), 'amount'].sum():,.0f}"])
    t = ax.table(cellText=rows, colLabels=["domain", "test rows", "alerts", "planted", "PR AUC", "precision", "recall", "amount caught"], loc="center")
    t.scale(1, 1.6); ax.set_title("KPI overview, XGBoost test split")
    return _save(fig, out, "01_kpi_overview.png")


def detection_heatmap(d, out):
    m = d[(d.record_type == "metric") & (d.metric == "recall") & (d.scenario != "all")]
    piv = m.groupby(["scenario", "model"])["value"].max().unstack()
    fig, ax = plt.subplots(figsize=(6, 0.32 * len(piv) + 1.5))
    im = ax.imshow(piv.to_numpy(dtype=float), cmap="viridis", vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(len(piv)), piv.index, fontsize=7); ax.set_xticks(range(piv.shape[1]), piv.columns)
    for (i, j), v in np.ndenumerate(piv.to_numpy(dtype=float)):
        if not np.isnan(v):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6, color="white" if v < 0.6 else "black")
    fig.colorbar(im, ax=ax, label="recall"); ax.set_title("Detection heat map by scenario (python stack)")
    return _save(fig, out, "02_detection_heatmap.png")


def pr_and_confusion(d, out):
    s = d[(d.record_type == "score") & (d.model == "xgboost")]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for dom in ("banking", "telecom"):
        x = s[s.domain == dom]
        if x.true_label.nunique() > 1:
            p, r, _ = precision_recall_curve(x.true_label.astype(int), x.score.astype(float))
            axes[0].plot(r, p, label=dom)
    axes[0].set_xlabel("recall"); axes[0].set_ylabel("precision"); axes[0].legend(); axes[0].set_title("PR curves, test split")
    for ax, dom in zip(axes[1:], ("banking", "telecom")):
        x = s[s.domain == dom]
        cm = confusion_matrix(x.true_label.astype(int), x.predicted_label.astype(int), labels=[0, 1])
        ax.imshow(cm, cmap="Blues")
        for (i, j), v in np.ndenumerate(cm):
            ax.text(j, i, f"{v:,}", ha="center", va="center")
        ax.set_xticks([0, 1], ["pred 0", "pred 1"]); ax.set_yticks([0, 1], ["true 0", "true 1"]); ax.set_title(f"Confusion matrix, {dom}")
    return _save(fig, out, "03_pr_curves_confusion.png")


def alert_trends(d, out):
    s = d[(d.record_type == "score") & (d.predicted_label == 1)]
    piv = s.groupby(["month", "domain"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(9, 3.5)); piv.plot(ax=ax, marker="o")
    ax.set_ylabel("alerts (rules and model)"); ax.set_title("Alert trends by month")
    return _save(fig, out, "04_alert_trends.png")


def hour_weekday(d, out):
    s = d[(d.record_type == "score") & (d.predicted_label == 1)]
    t = pd.to_datetime(s.event_timestamp)
    piv = pd.crosstab(t.dt.weekday, t.dt.hour).reindex(index=range(7), columns=range(24), fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 3.2)); im = ax.imshow(piv, aspect="auto", cmap="magma")
    ax.set_yticks(range(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]); ax.set_xlabel("hour (UTC)")
    fig.colorbar(im, ax=ax, label="alerts"); ax.set_title("Alerts by hour and weekday")
    return _save(fig, out, "07_hour_weekday.png")


def benford(d, out):
    b = d[d.record_type == "benford"]
    ds = sorted(b.dataset_id.unique())
    fig, axes = plt.subplots(1, len(ds), figsize=(4 * len(ds), 3.2))
    for ax, k in zip(np.atleast_1d(axes), ds):
        x = b[b.dataset_id == k].sort_values("first_digit")
        ax.bar(x.first_digit, x.observed_count / x.observed_count.sum(), label="observed")
        ax.plot(x.first_digit, x.expected_share, "r-o", label="Benford")
        ax.set_title(k); ax.set_xticks(range(1, 10))
    np.atleast_1d(axes)[0].legend()
    return _save(fig, out, "08_benford.png")


def dq_page(d, out):
    q = d[(d.record_type == "dq") & (d.check_name != "monthly_row_count")]
    fig, ax = plt.subplots(figsize=(11, 0.22 * len(q) + 1)); ax.axis("off")
    cell = q[["dataset_id", "step", "check_name", "expected", "observed", "passed"]].astype(str).to_numpy()
    t = ax.table(cellText=cell, colLabels=["dataset", "step", "check", "expected", "observed", "passed"], loc="center")
    t.auto_set_font_size(False); t.set_fontsize(6)
    for i, p in enumerate(q.passed, start=1):
        t[i, 5].set_facecolor("#c8f7c5" if p is True or p == "True" else "#f7c5c5")
    ax.set_title(f"Data quality and reconciliation ({int((q.passed.astype(str) == 'True').sum())} of {len(q)} passed)")
    return _save(fig, out, "10_data_quality.png")


def runtime(d, out):
    r = d[(d.record_type == "run") & (d.stage != "total")]
    fig, ax = plt.subplots(figsize=(7, 3)); ax.bar(r.stage, r.runtime_seconds.astype(float))
    ax.set_ylabel("seconds"); ax.set_title("Python stage runtime (measured)")
    return _save(fig, out, "11_runtime.png")


ALL = [kpi_overview, detection_heatmap, pr_and_confusion, alert_trends, hour_weekday, benford, dq_page, runtime]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="outputs/sample/results_python_sample.parquet")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    res = Path(a.results); d = pd.read_parquet(res) if res.suffix == ".parquet" else pd.read_csv(res, low_memory=False)
    out = Path(a.out) if a.out else res.parent / "charts"; out.mkdir(parents=True, exist_ok=True)
    paths = [f(d, out) for f in ALL]
    for p in paths:
        print(p)
    return paths


if __name__ == "__main__":
    main()
