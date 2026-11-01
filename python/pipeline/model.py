"""Step 5: XGBoost with a time based split (first 9 months train, then 1 month validation, last 2 months test).
Labels come only from the planted SYNTHETIC scenario column."""
from __future__ import annotations

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score

TRAIN_END = pd.Timestamp("2025-10-01")
VALID_END = pd.Timestamp("2025-11-01")


def split(t: pd.Series) -> np.ndarray:
    return np.where(t < TRAIN_END, "train", np.where(t < VALID_END, "validation", "test"))


def fit(Xtr, ytr, Xva, yva, seed: int = 42):
    pos = max(1, int(ytr.sum()))
    clf = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
                            tree_method="hist", scale_pos_weight=(len(ytr) - pos) / pos, eval_metric="aucpr",
                            early_stopping_rounds=30, random_state=seed, n_jobs=-1)
    clf.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
    return clf


def fit_score(df: pd.DataFrame, feats: list[str], tcol: str, seed: int = 42):
    y = (df["synthetic_scenario"] != "").astype(int).to_numpy()
    sp = split(df[tcol])
    tr, va = sp == "train", sp == "validation"
    pos = max(1, y[tr].sum())
    clf = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
                            tree_method="hist", scale_pos_weight=(tr.sum() - pos) / pos, eval_metric="aucpr",
                            early_stopping_rounds=30, random_state=seed, n_jobs=-1)
    clf.fit(df.loc[tr, feats], y[tr], eval_set=[(df.loc[va, feats], y[va])], verbose=False)
    score = clf.predict_proba(df[feats])[:, 1]
    # threshold chosen on validation to hit 1 percent alert rate (ASSUMPTION budget)
    thr = float(np.quantile(score[va], 0.99)) if va.any() else 0.5
    return score, y, sp, thr, int(tr.sum()), clf


def metrics(y, score, pred, mask) -> dict:
    yy, ss, pp = y[mask], score[mask], pred[mask]
    out = {"rows": int(mask.sum()), "positives": int(yy.sum()), "alert_rate": float(pp.mean()) if len(pp) else 0.0}
    if yy.sum() and yy.sum() < len(yy):
        out.update(pr_auc=float(average_precision_score(yy, ss)), roc_auc=float(roc_auc_score(yy, ss)),
                   precision=float(precision_score(yy, pp, zero_division=0)), recall=float(recall_score(yy, pp, zero_division=0)))
    return out
