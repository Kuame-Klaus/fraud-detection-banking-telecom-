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


# Logistic regression (the default model from round 7, approved by Klaus Konsults)
from sklearn.linear_model import LogisticRegression  # noqa: E402


class LogReg:
    """Logistic regression on signed log transformed, standardised features, with balanced class weights.
    Coefficients are per one standard deviation of the transformed feature, so they can be compared."""

    def __init__(self, seed: int = 42):
        self.seed = seed

    @staticmethod
    def _t(X):
        X = np.asarray(X, dtype=np.float64)
        return np.sign(X) * np.log1p(np.abs(X))

    def fit(self, X, y):
        self.cols = list(X.columns); Z = self._t(X)
        self.mu = Z.mean(axis=0); self.sd = Z.std(axis=0); self.sd[self.sd == 0] = 1
        self.clf = LogisticRegression(class_weight="balanced", C=1.0, max_iter=2000, random_state=self.seed)
        self.clf.fit((Z - self.mu) / self.sd, y)
        return self

    def predict_proba(self, X):
        return self.clf.predict_proba((self._t(X) - self.mu) / self.sd)

    def coefficients(self) -> pd.DataFrame:
        c = pd.DataFrame({"feature": self.cols, "coefficient": self.clf.coef_[0]})
        c["odds_ratio"] = np.exp(c["coefficient"])
        return c.reindex(c["coefficient"].abs().sort_values(ascending=False).index).reset_index(drop=True)


def fit_model(kind: str, Xtr, ytr, Xva, yva, seed: int = 42):
    return LogReg(seed).fit(Xtr, ytr) if kind == "logistic_regression" else fit(Xtr, ytr, Xva, yva, seed=seed)


def pr_curve(y, score, points: int = 101) -> pd.DataFrame:
    """Precision and recall curve on up to `points` recall levels 0, 0.01, ..., 1. For each level, the point with the
    highest threshold whose recall is at least that level (duplicates removed), so the curve is even along recall."""
    from sklearn.metrics import precision_recall_curve
    p, r, t = precision_recall_curve(y, score)
    p, r = p[:-1], r[:-1]  # drop the end point that has no threshold; r is non increasing along t
    lev = np.linspace(0, 1, points)
    idx = np.searchsorted(-r, -lev, side="right") - 1  # last index with r >= level
    idx = np.unique(idx[idx >= 0])
    return pd.DataFrame({"threshold": t[idx], "precision": p[idx], "recall": r[idx]})


FEATURE_TEXT = {
    "log_amount": "the size of the amount", "hour": "the hour of day", "weekday": "the day of the week",
    "secs_since_prev": "the time since the previous event of the same account or wallet",
    "secs_to_next": "the time until the next event of the same account or wallet",
    "ent_day_count": "the number of events of the account or wallet that day", "ent_day_sum": "the total amount of the account or wallet that day",
    "amount_z": "how unusual the amount is for this account or wallet", "ent_count": "the number of events of the account or wallet in the year",
    "near_threshold": "an amount just under the 10,000 reporting level", "declined": "a declined transaction",
    "is_debit": "a debit (money out)", "foreign": "a transaction outside Ghana",
    "country_change_fast": "a change of country within an hour", "lead_digit": "the first digit of the amount",
    "merch_day_count": "repeat payments to the same merchant that day", "acct_dormant": "a dormant account",
    "amount_vs_expected": "the amount against the account's expected monthly volume", "reversal_flag": "a reversal",
    "channel_card": "the card channel", "channel_mobile": "the mobile channel", "channel_web": "the web channel",
    "channel_branch": "the branch channel", "channel_atm": "the ATM channel",
    "wallet_limit": "the wallet tier limit", "over_tier": "an amount above the wallet tier limit",
    "wallet_dormant": "a dormant wallet", "round_amount": "a round amount (a multiple of 100)",
    "has_reversal": "a reversal", "agent_day_count": "the number of transactions of the agent that day",
    "hours_since_swap": "the hours since the latest SIM swap on the number",
    "type_p2p": "a person to person transfer", "type_cash_in": "a cash in", "type_cash_out": "a cash out",
    "type_merchant": "a merchant payment", "type_airtime": "an airtime purchase",
}


BINARY = {"near_threshold", "declined", "is_debit", "foreign", "country_change_fast", "acct_dormant", "reversal_flag",
          "over_tier", "wallet_dormant", "round_amount", "has_reversal"} | {k for k in FEATURE_TEXT if k.startswith(("channel_", "type_"))}


def drivers_markdown(drivers: dict, run_id: str, top: int = 10) -> str:
    L = [f"# Model drivers: logistic regression (run {run_id})", "",
         "SYNTHETIC data only. Prepared by Klaus Konsults. Each feature is log transformed (signed) and standardised, so a "
         "coefficient is the change in log odds of fraud for one standard deviation of the feature. The odds ratio is "
         "exp(coefficient): above 1 raises the fraud score, below 1 lowers it. These drivers describe the synthetic "
         "planting and must be re-estimated on real client data. Related features (for example amount, daily total and how "
         "unusual the amount is) share signal, so one of them can take a negative sign while the group together raises the "
         "score. Read a driver together with its related features.", ""]
    for domain, co in drivers.items():
        L += [f"## {domain.capitalize()}: top {top} drivers", "", "| rank | feature | coefficient | odds ratio | plain English |", "|---|---|---|---|---|"]
        for i, r in co.head(top).iterrows():
            way = "raises" if r["coefficient"] > 0 else "lowers"
            f = r["feature"]; ft = FEATURE_TEXT.get(f, f)
            txt = (f"{ft[0].upper() + ft[1:]} {way} the fraud score" if f in BINARY
                   else f"A higher value of {ft} {way} the fraud score")
            L.append(f"| {i + 1} | {r['feature']} | {r['coefficient']:.3f} | {r['odds_ratio']:.3f} | {txt} |")
        L.append("")
    return "\n".join(L)
