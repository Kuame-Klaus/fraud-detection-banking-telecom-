"""Render 12 PNG mockups of the Power BI pages in docs/powerbi_design.md (Klaus Konsults).

Mockups only, not a Power BI build. Every number comes from the shared results file
outputs/sample/results_latest.csv (SYNTHETIC sample run). Pages without data show a labelled placeholder.
Run from the repo root: python docs/powerbi_mockups/render_mockups.py
"""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SRC = ROOT / "outputs/sample/results_latest.csv"

# Theme from docs/powerbi_design.md
LIGHT = ["#9DC3E6", "#F4B183", "#A9D18E", "#D9D9D9", "#BDD7EE", "#FFE699", "#595959"]
C = dict(data=["#1F4E79", "#C55A11", "#548235", "#7F7F7F", "#2E75B6", "#BF9000", "#A5A5A5", "#70AD47"],
         fg="#222222", label="#444444", accent="#1F4E79", good="#548235", neutral="#BF9000", bad="#C00000",
         center="#F2F2F2", bg="#FFFFFF")
STACK = {"python": "#1F4E79", "alteryx": "#C55A11", "knime": "#548235"}

FONT = "Arial" if any("Arial" == f.name for f in font_manager.fontManager.ttflist) else "Liberation Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 10, "text.color": C["fg"], "axes.edgecolor": "#BBBBBB",
                     "axes.labelcolor": C["label"], "xtick.color": C["label"], "ytick.color": C["label"],
                     "axes.titlesize": 12, "axes.titleweight": "regular", "axes.titlelocation": "left",
                     "axes.spines.top": False, "axes.spines.right": False})

r = pd.read_csv(SRC, low_memory=False)
try:
    COMMIT = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%h", "--", str(SRC)],
                            capture_output=True, text=True).stdout.strip() or "unknown"
except Exception:
    COMMIT = "unknown"
RUN = r["run_id"].dropna().iloc[0]
T = lambda t: r[r["record_type"] == t]


def page(num, title, note, slicers):
    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=C["bg"])
    fig.text(0.025, 0.955, f"{num}. {title}", fontsize=20, color=C["fg"], va="center")
    fig.text(0.025, 0.915, note, fontsize=11, color=C["label"], va="center")
    x = 0.025
    w = (0.95 - 0.01 * 4) / 5
    for name, val in slicers:
        ax = fig.add_axes([x, 0.845, w, 0.045]); ax.axis("off")
        ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.08",
                                    fc=C["center"], ec="#D0D0D0", transform=ax.transAxes))
        ax.text(0.04, 0.5, f"{name}:", fontsize=10, color=C["label"], va="center", transform=ax.transAxes)
        ax.text(0.96, 0.5, val, fontsize=10, color=C["accent"], va="center", ha="right", transform=ax.transAxes)
        x += w + 0.01
    fig.add_artist(plt.Line2D([0.025, 0.975], [0.06, 0.06], color="#DDDDDD", lw=1))
    fig.text(0.025, 0.035, "SYNTHETIC data. Klaus Konsults.", fontsize=10, color=C["label"], va="center")
    fig.text(0.975, 0.035, f"Mockup, not a Power BI build. Source: outputs/sample/results_latest.csv, run {RUN}, commit {COMMIT}",
             fontsize=9, color="#888888", va="center", ha="right")
    return fig


def slic(domain="banking", stack="python", scen="All", month="All", thr="0%"):
    return [("Domain", domain), ("Stack", stack), ("Scenario", scen), ("Month", month), ("Threshold change", thr)]


def card(fig, rect, label, value):
    ax = fig.add_axes(rect); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, fc=C["bg"], ec="#DDDDDD", transform=ax.transAxes))
    ax.text(0.5, 0.6, value, fontsize=26, color=C["accent"], ha="center", va="center", transform=ax.transAxes)
    ax.text(0.5, 0.22, label, fontsize=11, color=C["label"], ha="center", va="center", transform=ax.transAxes)


def table(fig, rect, df, title=None, colw=None, fs=10, red=None):
    ax = fig.add_axes(rect); ax.axis("off")
    if title:
        ax.set_title(title, loc="left", fontsize=12, pad=6)
    t = ax.table(cellText=df.values, colLabels=list(df.columns), loc="upper left", cellLoc="left", colLoc="left",
                 colWidths=colw, bbox=[0, 0, 1, 1])
    t.auto_set_font_size(False); t.set_fontsize(fs)
    for (i, j), c in t.get_celld().items():
        c.set_edgecolor("#E3E3E3"); c.get_text().set_fontfamily(FONT)
        if i == 0:
            c.set_facecolor(C["accent"]); c.get_text().set_color("white")
        elif red is not None and red(i - 1):
            c.get_text().set_color(C["bad"])
    return ax


def placeholder(fig, rect, text):
    ax = fig.add_axes(rect); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, fc="#FAFAFA", ec=C["neutral"], ls="--", lw=1.5, transform=ax.transAxes))
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=13, color=C["label"], transform=ax.transAxes, wrap=True)


def fmt(v, d=0):
    return f"{v:,.{d}f}"


S = T("score")
M = T("metric")
MODEL = "logistic_regression" if (M.model == "logistic_regression").any() else "xgboost"
MLAB = "logistic regression" if MODEL == "logistic_regression" else "XGBoost"
SX = S[(S.model == MODEL)]


def save(fig, n, slug):
    fig.savefig(OUT / f"page_{n:02d}_{slug}.png", dpi=100, facecolor=C["bg"])
    plt.close(fig)


# 1 KPI overview
fig = page(1, "KPI overview", "How many records were scored, how many alerted, and how many planted cases were caught (model, test split).", slic())
b = SX[SX.domain == "banking"]
tp = ((b.predicted_label == 1) & (b.true_label == 1)).sum(); al = (b.predicted_label == 1).sum(); pl = (b.true_label == 1).sum()
for i, (lab, val) in enumerate([("Records scored", fmt(len(b))), ("Alerts", fmt(al)),
                                ("Recall", f"{tp / pl:.2f}" if pl else "n/a"), ("Precision", f"{tp / al:.2f}" if al else "n/a")]):
    card(fig, [0.025 + i * 0.2425, 0.6, 0.2275, 0.2], lab, val)
rows = []
for st in ["python", "alteryx", "knime"]:
    for dom in ["banking", "telecom"]:
        d = SX[(SX.domain == dom) & (SX["stack"] == st)]
        if len(d) == 0:
            rows.append([st, dom, "no run yet", "", "", ""]); continue
        pa = M[(M.model == MODEL) & (M.domain == dom) & (M.split == "test") & (M.metric == "pr_auc")]["value"]
        rows.append([st, dom, f"{(d.predicted_label == 1).mean():.3f}", fmt(d.loc[d.predicted_label == 1, "amount"].sum(), 2),
                     fmt(d.loc[(d.predicted_label == 1) & (d.true_label == 1), "amount"].sum(), 2), f"{pa.iloc[0]:.3f}" if len(pa) else ""])
table(fig, [0.025, 0.1, 0.95, 0.42], pd.DataFrame(rows, columns=["Stack", "Domain", "Alert rate", "Alerted amount", "Detected amount", "PR AUC"]),
      title="By stack and domain (test split)", fs=11)
save(fig, 1, "kpi_overview")

# 2 Detection heat map
fig = page(2, "Detection heat map by scenario and tool", "Share of planted cases each tool caught, per scenario. Darker is better.", slic())
rr = M[(M.model == "rule") & (M.metric == "recall") & (M.domain == "banking")].groupby("scenario")["value"].max()
xr = M[(M.model == MODEL) & (M.metric == "recall") & (M.domain == "banking") & (M.scenario != "all")].set_index("scenario")["value"]
scen = sorted(rr.index)
mat = np.array([[rr.get(s, np.nan), xr.get(s, np.nan), np.nan, np.nan] for s in scen])
ax = fig.add_axes([0.25, 0.1, 0.62, 0.7])
cm = matplotlib.colors.LinearSegmentedColormap.from_list("kk", ["#FFFFFF", C["accent"]])
ax.imshow(np.nan_to_num(mat, nan=0), cmap=cm, vmin=0, vmax=1, aspect="auto")
for i in range(len(scen)):
    for j in range(4):
        v = mat[i, j]
        ax.text(j, i, "no run yet" if j >= 2 else ("none" if np.isnan(v) else f"{v:.2f}"), ha="center", va="center",
                fontsize=10, color="white" if (not np.isnan(v) and v > 0.6) else C["label"])
ax.set_xticks(range(4), ["python rule", "python " + MLAB, "alteryx", "knime"]); ax.xaxis.tick_top()
ax.set_yticks(range(len(scen)), [s.replace("_", " ") for s in scen]); ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
fig.text(0.885, 0.75, "Recall\n0 to 1\n\nmodel: test\nsplit only.\n'none' = no\nplanted case\nin test.", fontsize=10, color=C["label"], va="top")
save(fig, 2, "detection_heatmap")

# 3 PR curves and confusion matrices
fig = page(3, "Precision and recall curves and confusion matrices", "How precision trades against recall as the threshold moves, and the counts at the chosen threshold.", slic())
ax = fig.add_axes([0.05, 0.12, 0.55, 0.66])
PC = T("pr_curve")
for dom, col in [("banking", C["data"][0]), ("telecom", C["data"][5])]:
    d = PC[(PC.domain == dom) & (PC.model == MODEL)].sort_values("curve_recall")
    ax.plot(d.curve_recall, d.curve_precision, color=col, lw=2, label=f"python {dom}")
ax.set_xlabel("Recall"); ax.set_ylabel("Precision"); ax.set_xlim(0, 1.02); ax.set_ylim(0, 1.05)
ax.set_title(f"Curve points from the pr_curve rows ({MLAB}, test split)", fontsize=12); ax.legend(frameon=False, loc="lower left")
for i, (dom, st) in enumerate([("banking", "python"), ("telecom", "python"), ("banking", "alteryx or knime")]):
    rect = [0.66, 0.56 - i * 0.22, 0.3, 0.19]
    if st != "python":
        placeholder(fig, rect, "Alteryx and KNIME: no run yet"); continue
    d = SX[SX.domain == dom]
    tpv = int(((d.predicted_label == 1) & (d.true_label == 1)).sum()); fp = int(((d.predicted_label == 1) & (d.true_label == 0)).sum())
    fn = int(((d.predicted_label == 0) & (d.true_label == 1)).sum()); tn = int(((d.predicted_label == 0) & (d.true_label == 0)).sum())
    table(fig, rect, pd.DataFrame([["Alert", fmt(tpv), fmt(fp)], ["No alert", fmt(fn), fmt(tn)]],
                                  columns=[f"{st} {dom}", "Fraud", "Not fraud"]), fs=11)
save(fig, 3, "pr_curves_confusion")

# 4 Alert trends
fig = page(4, "Alert trends", "When alerts happen over time, and which scenarios drive them (rule alerts, all splits).", slic())
R = S[(S.model == "rule") & (S.domain == "banking")].copy()
R["day"] = pd.to_datetime(R.event_timestamp).dt.floor("D").dt.tz_localize(None)
ax = fig.add_axes([0.05, 0.5, 0.92, 0.28])
dly = R.groupby("day").size(); ax.plot(dly.index, dly.values, color=STACK["python"], lw=1.5, label="python")
ax.set_title("Rule alerts per day", fontsize=12); ax.legend(frameon=False)
ax = fig.add_axes([0.05, 0.1, 0.72, 0.32])
pv = R.groupby(["month", "scenario"]).size().unstack(fill_value=0)
bottom = np.zeros(len(pv))
for i, c in enumerate(pv.columns):
    ax.bar(pv.index, pv[c], bottom=bottom, color=(C["data"] + LIGHT)[i % 15], label=c.replace("_", " ")); bottom += pv[c].to_numpy()
ax.set_title("Rule alerts by month and scenario", fontsize=12); ax.tick_params(axis="x", labelsize=8)
ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0))
save(fig, 4, "alert_trends")

# 5 Risk leaderboards
fig = page(5, "Risk leaderboards", "The entities with the highest scores and the largest alerted amounts (model, test split).", slic())
b = SX[SX.domain == "banking"]
g = b.groupby(["entity_id", "entity_type"]).agg(max_score=("score", "max"), alerted=("amount", lambda s: s[b.loc[s.index, "predicted_label"] == 1].sum()),
                                                scenario=("true_scenario", lambda s: ", ".join(sorted(set(s.dropna()) - {""})) or "none")).reset_index()
t1 = g.sort_values("max_score", ascending=False).head(20)
t2 = g.sort_values("alerted", ascending=False).head(20)
f = lambda t: pd.DataFrame({"Entity": t.entity_id, "Type": t.entity_type, "Max score": t.max_score.map("{:.3f}".format),
                            "Alerted amount": t.alerted.map(lambda v: fmt(v, 2)), "Planted scenario": t.scenario.str.replace("_", " ").map(lambda v: "\n".join(textwrap.wrap(v, 26)))})
table(fig, [0.025, 0.1, 0.465, 0.68], f(t1), title="Top 20 by max score", fs=8.5, colw=[0.2, 0.12, 0.14, 0.2, 0.34])
table(fig, [0.51, 0.1, 0.465, 0.68], f(t2), title="Top 20 by alerted amount", fs=8.5, colw=[0.2, 0.12, 0.14, 0.2, 0.34])
save(fig, 5, "risk_leaderboards")

# 6 Network
fig = page(6, "Mule and agent network graphs", "Who sends money to whom. Thicker lines carry more money.", slic())
E = T("edge")
eb = E[E.domain == "banking"]
if len(eb):
    ax = fig.add_axes([0.025, 0.1, 0.58, 0.7]); ax.axis("off")
    G = nx.DiGraph()
    for _, e in eb.iterrows():
        G.add_edge(e.source_id, e.target_id, w=e.edge_weight)
    pos = nx.spring_layout(G, seed=42, k=0.35)
    ws = np.array([G[u][v]["w"] for u, v in G.edges()])
    nx.draw_networkx_edges(G, pos, ax=ax, width=0.5 + 3 * ws / ws.max(), edge_color="#9DB3C9", arrows=False)
    src = {u for u, _ in G.edges()}
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=28, node_color=[C["accent"] if n in src else C["data"][3] for n in G.nodes()])
    ax.set_title(f"Banking account network: {len(eb)} edges from the results file (sending accounts in blue)", fontsize=12)
    top = eb.sort_values("edge_weight", ascending=False).head(18)
    table(fig, [0.63, 0.1, 0.345, 0.68], pd.DataFrame({"Source": top.source_id, "Target": top.target_id,
                                                         "Amount": top.edge_weight.map(lambda v: fmt(v, 2)), "Count": top.edge_count.astype(int)}),
          title="Largest links", fs=9)
else:
    placeholder(fig, [0.025, 0.1, 0.95, 0.7], "PLACEHOLDER: no edge rows in the results file yet")
save(fig, 6, "network_graphs")

# 7 Hour by weekday
fig = page(7, "Hour by weekday heat maps", "When in the week alerts cluster (rule alerts, all splits).", slic())
ts = pd.to_datetime(R.event_timestamp)
hm = pd.crosstab(ts.dt.day_of_week, ts.dt.hour).reindex(index=range(7), columns=range(24), fill_value=0)
ax = fig.add_axes([0.08, 0.12, 0.84, 0.64])
ax.imshow(hm.values, cmap=cm, aspect="auto")
for i in range(7):
    for j in range(24):
        v = hm.values[i, j]; ax.text(j, i, str(v), ha="center", va="center", fontsize=8, color="white" if v > hm.values.max() * 0.6 else C["label"])
ax.set_yticks(range(7), ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
ax.set_xticks(range(24), [str(h) for h in range(24)]); ax.set_xlabel("Hour of day (UTC)"); ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
save(fig, 7, "hour_weekday_heatmap")

# 8 Benford
fig = page(8, "Benford chart", "Do leading digits follow the natural pattern? Big gaps can point to made up amounts.", slic(scen="benford anomaly"))
B = T("benford")
ax = fig.add_axes([0.05, 0.12, 0.66, 0.64])
d = B[B.dataset_id == "B1"].sort_values("first_digit")
obs = d.observed_count / d.observed_count.sum()
ax.bar(d.first_digit, obs, color=C["accent"], label="Observed share (B1 amount)")
ax.plot(d.first_digit, d.expected_share, color=C["data"][1], marker="o", lw=2, label="Benford expected share")
ax.set_xticks(range(1, 10)); ax.set_xlabel("First digit"); ax.set_ylabel("Share"); ax.legend(frameon=False)
ax2 = fig.add_axes([0.75, 0.55, 0.2, 0.2]); ax2.axis("off")
ax2.text(0, 1, "Dataset", fontsize=12, va="top")
for i, ds in enumerate(sorted(B.dataset_id.unique())):
    ax2.text(0, 0.75 - i * 0.22, ("[x] " if ds == "B1" else "[  ] ") + ds, fontsize=11, va="top", color=C["accent"] if ds == "B1" else C["label"])
gap = (obs.to_numpy() - d.expected_share.to_numpy())
card(fig, [0.75, 0.25, 0.2, 0.2], "Largest gap (digit " + str(int(d.first_digit.iloc[np.abs(gap).argmax()])) + ")", f"{gap[np.abs(gap).argmax()]:+.3f}")
save(fig, 8, "benford")

# 9 Threshold slider
fig = page(9, "Threshold slider", "What happens to alerts and caught cases if the model threshold moves up or down.", slic())
TH = T("threshold")
ax = fig.add_axes([0.05, 0.69, 0.9, 0.08]); ax.set_xlim(-22, 22); ax.set_ylim(0, 1); ax.axis("off")
ax.plot([-20, 20], [0.5, 0.5], color="#CCCCCC", lw=4)
for p in [-20, -10, 0, 10, 20]:
    ax.text(p, 0.0, f"{p:+d}%" if p else "0%", ha="center", fontsize=10, color=C["label"])
ax.plot([0], [0.5], "o", ms=16, color=C["accent"])
ax.text(-22, 0.85, "Threshold change", fontsize=11, color=C["label"])
t0 = TH[(TH.domain == "banking") & (TH.threshold_change_pct == 0)].iloc[0]
card(fig, [0.05, 0.45, 0.2, 0.18], "Alerts at threshold", fmt(t0.alert_count))
card(fig, [0.05, 0.22, 0.2, 0.18], "Detected at threshold", fmt(t0.detected_count))
ax = fig.add_axes([0.32, 0.12, 0.63, 0.5])
for dom, col in [("banking", C["data"][0]), ("telecom", C["data"][5])]:
    d = TH[TH.domain == dom].sort_values("threshold_change_pct")
    ax.plot(d.threshold_change_pct, d.alert_count, marker="o", color=col, lw=2, label=f"xgboost {dom}: alerts")
    ax.plot(d.threshold_change_pct, d.detected_count, marker="s", ls="--", color=col, lw=1.5, label=f"xgboost {dom}: detected")
ax.set_xticks([-20, -10, 0, 10, 20]); ax.set_xlabel("Threshold change (%)"); ax.set_ylabel("Count (test split)")
ax.legend(frameon=False, fontsize=9, ncol=2); ax.set_title("Rules use fixed thresholds and are not swept yet", fontsize=11)
save(fig, 9, "threshold_slider")

# 10 DQ
fig = page(10, "Data quality and reconciliation", "Did every load and quality check pass before analysis?", slic(scen="n/a"))
Q = T("dq")
q = Q[Q.check_name != "monthly_row_count"]
card(fig, [0.025, 0.62, 0.3, 0.16], "DQ checks (excluding monthly counts)", fmt(len(q)))
card(fig, [0.35, 0.62, 0.3, 0.16], "Failed", fmt((~q.passed.astype(bool)).sum()))
card(fig, [0.675, 0.62, 0.3, 0.16], "Pass rate", f"{q.passed.astype(bool).mean():.0%}")
qb = q[q.domain == "banking"].head(22)
table(fig, [0.025, 0.08, 0.95, 0.5], pd.DataFrame({"Step": qb.step.astype(int), "Dataset": qb.dataset_id, "Check": qb.check_name,
                                                    "Expected": qb.expected.fillna("").astype(str),
                                                    "Observed": qb.observed.astype(str), "Passed": qb.passed.astype(str)}),
      fs=8, colw=[0.05, 0.07, 0.25, 0.2, 0.33, 0.1], red=lambda i: not bool(qb.passed.iloc[i]))
save(fig, 10, "dq_reconciliation")

# 11 Runtime
fig = page(11, "Tool runtime and memory", "How long each stage took and how much memory each tool used on this run.", slic(scen="n/a"))
U = T("run")
u = U[U.stage != "total"]
ax = fig.add_axes([0.06, 0.4, 0.42, 0.36])
ax.barh(u.stage, u.runtime_seconds, color=STACK["python"]); ax.invert_yaxis(); ax.set_xlabel("Seconds"); ax.set_title("Runtime by stage (python)", fontsize=12)
ax = fig.add_axes([0.56, 0.4, 0.4, 0.36])
tot = U[U.stage == "total"].iloc[0]
ax.bar(["python", "alteryx", "knime"], [tot.peak_memory_mb, 0, 0], color=[STACK["python"], "#EEEEEE", "#EEEEEE"])
ax.text(1, tot.peak_memory_mb * 0.05, "no run yet", ha="center", color=C["label"]); ax.text(2, tot.peak_memory_mb * 0.05, "no run yet", ha="center", color=C["label"])
ax.set_ylabel("Peak memory (MB)"); ax.set_title("Peak memory by stack", fontsize=12)
table(fig, [0.06, 0.08, 0.9, 0.24], pd.DataFrame({"Stage": U.stage, "Runtime (s)": U.runtime_seconds.map("{:.2f}".format),
                                                  "Peak memory (MB)": U.peak_memory_mb.map("{:.0f}".format), "Stack": "python"}), fs=9)
save(fig, 11, "runtime_memory")

# 12 Routes and cells
fig = page(12, "Telecom route and cell maps", "Where traffic flows, and which routes carry minutes that were not settled.", slic(domain="telecom"))
Gd = T("geo")
Gc = Gd[Gd.cell_id.notna() & Gd.latitude.notna()]
ax = fig.add_axes([0.05, 0.1, 0.45, 0.68])
if len(Gc):
    ax.scatter(Gc.longitude, Gc.latitude, s=20 + 180 * Gc.geo_minutes / Gc.geo_minutes.max(), color=C["data"][5], alpha=0.6, edgecolors="none")
ax.set_xlim(-3.4, 1.3); ax.set_ylim(4.5, 11.3); ax.set_aspect("equal")
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
ax.set_title("SYNTHETIC cell site locations in Ghana (not real sites). Bubble size = T1 minutes", fontsize=11)
Gd = Gd[Gd.cell_id.isna()]
# Only route days with a T8 settlement row: T8 does not cover every day, and days without a row are not unsettled
Gd = Gd[Gd.geo_settled_minutes.notna()].assign(geo_minutes=lambda x: x.geo_minutes.fillna(0))
gr = Gd.groupby("route")[["geo_minutes", "geo_settled_minutes"]].sum()
gr["unsettled"] = gr.geo_minutes - gr.geo_settled_minutes
gr = gr.sort_values("unsettled", ascending=False).head(18).reset_index()
table(fig, [0.55, 0.1, 0.425, 0.68], pd.DataFrame({"Route": gr.route, "Route minutes (T1)": gr.geo_minutes.map(lambda v: fmt(v, 1)),
                                                   "Settled minutes (T8)": gr.geo_settled_minutes.map(lambda v: fmt(v, 1)),
                                                   "Unsettled": gr.unsettled.map(lambda v: fmt(v, 1))}),
      title="Routes with the most unsettled minutes (route days with a T8 row)", fs=9)
save(fig, 12, "route_cell_maps")
print("font", FONT, "commit", COMMIT, "run", RUN)
