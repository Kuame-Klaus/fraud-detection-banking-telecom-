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
    r = d[(d.record_type == "run") & ~d.stage.isin(["total", "data_quality"])]
    fig, ax = plt.subplots(figsize=(7, 3)); ax.bar(r.stage, r.runtime_seconds.astype(float))
    ax.set_ylabel("seconds"); ax.set_title("Python stage runtime (measured)")
    return _save(fig, out, "11_runtime.png")


def leaderboards(d, out):
    s = d[(d.record_type == "score") & (d.predicted_label == 1)]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, dom in zip(axes, ("banking", "telecom")):
        x = s[s.domain == dom]
        g = x.groupby(["entity_type", "entity_id"]).agg(alerts=("score", "size"), amount=("amount", "sum"),
                                                        planted=("true_label", "max")).reset_index()
        ms = d[(d.record_type == "score") & (d.model == "xgboost") & (d.domain == dom)].groupby("entity_id")["score"].max()
        g["max_score"] = g.entity_id.map(ms).fillna(0)
        g = g[g.entity_type.isin(["account", "wallet"])].sort_values(["alerts", "amount"], ascending=False).head(15)[::-1]
        colors = ["#d62728" if p == 1 else "#1f77b4" for p in g.planted]
        ax.barh(g.entity_id.astype(str), g.alerts, color=colors)
        for i, (a_, m) in enumerate(zip(g.amount, g.max_score)):
            ax.text(a_ if False else g.alerts.iloc[i], i, f"  max model score {m:.2f}, amount {a_:,.0f}", va="center", fontsize=6)
        ax.set_xlabel("alerts (rules and model)"); ax.set_title(f"Risk leaderboard, {dom} (red = has planted case)")
        ax.tick_params(axis="y", labelsize=6)
    return _save(fig, out, "05_risk_leaderboards.png")


def networks(d, out, top=12):
    e = d[d.record_type == "edge"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.5))
    for ax, (dom, label) in zip(axes, (("banking", "mule network (accounts)"), ("telecom", "agent network (agent to wallets)"))):
        x = e[e.domain == dom]
        hubs = x.groupby("source_id")["edge_weight"].sum().sort_values(ascending=False).head(top).index
        x = x[x.source_id.isin(hubs)]
        ang = np.linspace(0, 2 * np.pi, len(hubs), endpoint=False)
        pos = {h: (np.cos(a) * 3, np.sin(a) * 3) for h, a in zip(hubs, ang)}
        wmax = x.edge_weight.max() if len(x) else 1
        for h, a in zip(hubs, ang):
            tg = x[x.source_id == h]
            ta = a + np.linspace(-0.35, 0.35, max(len(tg), 1))
            for (_, r), b in zip(tg.iterrows(), ta):
                tx, ty = np.cos(b) * 4.6, np.sin(b) * 4.6
                ax.plot([pos[h][0], tx], [pos[h][1], ty], color="grey", lw=0.3 + 2.5 * r.edge_weight / wmax, alpha=0.6)
                ax.scatter(tx, ty, s=8, color="#1f77b4")
            ax.scatter(*pos[h], s=60, color="#d62728", zorder=3)
            ax.annotate(str(h), pos[h], fontsize=6, ha="center", va="bottom")
        ax.set_title(f"{label}: top {len(hubs)} hubs by amount"); ax.axis("off"); ax.set_aspect("equal")
    return _save(fig, out, "06_networks.png")


def threshold_slider(d, out):
    t = d[d.record_type == "threshold"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
    for ax, dom in zip(axes, ("banking", "telecom")):
        x = t[t.domain == dom].sort_values("threshold_change_pct")
        ax.plot(x.threshold_change_pct, x.alert_count, "o-", label="alerts")
        ax.plot(x.threshold_change_pct, x.detected_count, "s-", label="planted cases detected")
        ax.set_xlabel("threshold change (percent)"); ax.set_title(f"Threshold sensitivity, {dom} XGBoost test split"); ax.legend()
    p = _save(fig, out, "09_threshold_sensitivity.png")
    # interactive page: alerts and detections for any threshold, from the scored test rows
    import json
    s = d[(d.record_type == "score") & (d.model == "xgboost")]
    data = {}
    grid = np.round(np.linspace(0, 1, 201), 3)
    for dom in ("banking", "telecom"):
        x = s[s.domain == dom]
        sc = x.score.to_numpy(dtype=float); y = x.true_label.to_numpy(dtype=int)
        data[dom] = {"grid": grid.tolist(), "alerts": [int((sc >= g).sum()) for g in grid],
                     "detected": [int(((sc >= g) & (y == 1)).sum()) for g in grid], "planted": int(y.sum()),
                     "current": float(x.threshold.iloc[0]) if len(x) else 0.5}
    html = """<!doctype html><html><head><meta charset="utf-8"><title>Threshold slider (SYNTHETIC data, Klaus Konsults)</title>
<style>body{font-family:sans-serif;margin:2em}td{padding:4px 10px}</style></head><body>
<h2>Threshold slider, XGBoost test split</h2><p>SYNTHETIC data, Klaus Konsults. Move the slider to see alerts and planted cases detected.</p>
<div id="ui"></div><script>
const D = DATA;
const ui = document.getElementById('ui');
for (const dom of Object.keys(D)) {
  const d = D[dom]; const div = document.createElement('div');
  div.innerHTML = `<h3>${dom}</h3><input type="range" min="0" max="${d.grid.length-1}" value="${Math.round(d.current*200)}" style="width:400px">
  <table><tr><td>threshold</td><td class="t"></td></tr><tr><td>alerts</td><td class="a"></td></tr>
  <tr><td>planted detected</td><td class="d"></td></tr><tr><td>recall</td><td class="r"></td></tr><tr><td>precision</td><td class="p"></td></tr></table>`;
  ui.appendChild(div);
  const s = div.querySelector('input');
  const upd = () => { const i = +s.value; const a = d.alerts[i], k = d.detected[i];
    div.querySelector('.t').textContent = d.grid[i].toFixed(3); div.querySelector('.a').textContent = a;
    div.querySelector('.d').textContent = k + ' of ' + d.planted;
    div.querySelector('.r').textContent = d.planted ? (k/d.planted).toFixed(3) : 'n/a';
    div.querySelector('.p').textContent = a ? (k/a).toFixed(3) : 'n/a'; };
  s.oninput = upd; upd();
}
</script></body></html>""".replace("DATA", json.dumps(data))
    (out / "09_threshold_slider.html").write_text(html)
    return p


ALL = [kpi_overview, detection_heatmap, pr_and_confusion, alert_trends, leaderboards, networks, hour_weekday, benford,
       threshold_slider, dq_page, runtime]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="outputs/sample/results_python_sample.parquet")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    res = Path(a.results)
    cols = ["record_type", "domain", "dataset_id", "scenario", "model", "split", "entity_id", "entity_type", "event_timestamp",
            "month", "score", "threshold", "predicted_label", "true_label", "amount", "metric", "value", "step", "check_name",
            "expected", "observed", "passed", "threshold_change_pct", "alert_count", "detected_count", "source_id", "target_id",
            "edge_weight", "edge_count", "first_digit", "observed_count", "expected_share", "runtime_seconds", "stage"]
    d = pd.read_parquet(res, columns=cols) if res.suffix == ".parquet" else pd.read_csv(res, usecols=cols, low_memory=False)
    out = Path(a.out) if a.out else res.parent / "charts"; out.mkdir(parents=True, exist_ok=True)
    paths = [f(d, out) for f in ALL]
    for p in paths:
        print(p)
    return paths


if __name__ == "__main__":
    main()
