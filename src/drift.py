"""Phase 8: drift monitoring - PSI per feature and on the model score, plus an Evidently HTML report."""
import joblib
import numpy as np
import pandas as pd
from src.config import PROCESSED, MODELS, REPORTS, NUM, CAT, FEATURES, MODEL_VERSION, APPROVE_BELOW, REJECT_FROM

PSI_WATCH, PSI_ALERT = 0.10, 0.25          # <0.10 stable, 0.10-0.25 watch, >=0.25 alert
EPS = 1e-4                                  # floor for empty bins so log() never breaks


def psi_numeric(ref: pd.Series, cur: pd.Series, bins: int = 10) -> float:
    ref, cur = ref.dropna(), cur.dropna()
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))     # training deciles
    edges[0], edges[-1] = -np.inf, np.inf                                # catch values outside the training range
    e = np.histogram(ref, edges)[0] / len(ref)
    a = np.histogram(cur, edges)[0] / len(cur)
    e, a = np.clip(e, EPS, None), np.clip(a, EPS, None)
    return float(np.sum((a - e) * np.log(a / e)))


def psi_categorical(ref: pd.Series, cur: pd.Series) -> float:
    cats = sorted(set(ref.dropna()) | set(cur.dropna()))
    e = ref.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    a = cur.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    e, a = np.clip(e, EPS, None), np.clip(a, EPS, None)
    return float(np.sum((a - e) * np.log(a / e)))


def status(psi: float) -> str:
    return "alert" if psi >= PSI_ALERT else "watch" if psi >= PSI_WATCH else "stable"


def drift_table(ref: pd.DataFrame, cur: pd.DataFrame, model=None) -> pd.DataFrame:
    rows = [{"feature": c, "psi": psi_numeric(ref[c], cur[c]) if c in NUM else psi_categorical(ref[c], cur[c])}
            for c in FEATURES]
    if model is not None:                                                # prediction drift on the PD score
        rows.append({"feature": "model_score_PD", "psi": psi_numeric(
            pd.Series(model.predict_proba(ref[FEATURES])[:, 1]), pd.Series(model.predict_proba(cur[FEATURES])[:, 1]))})
    out = pd.DataFrame(rows)
    out["psi"] = out["psi"].round(4)
    out["status"] = out["psi"].map(status)
    return out


def evidently_report(ref: pd.DataFrame, cur: pd.DataFrame, path) -> None:
    """Evidently 0.7.x API (the old evidently.report / evidently.metric_preset modules no longer exist)."""
    from evidently import Report, Dataset, DataDefinition
    from evidently.presets import DataDriftPreset
    definition = DataDefinition(numerical_columns=NUM, categorical_columns=CAT)
    snapshot = Report([DataDriftPreset()]).run(
        current_data=Dataset.from_pandas(cur[FEATURES], data_definition=definition),
        reference_data=Dataset.from_pandas(ref[FEATURES], data_definition=definition))
    snapshot.save_html(str(path))


def stress(df: pd.DataFrame) -> pd.DataFrame:
    """Simulated downturn: incomes fall 20%, lenders add 2 points of interest."""
    s = df.copy()
    s["person_income"] = (s["person_income"] * 0.8).round()
    s["loan_int_rate"] = s["loan_int_rate"] + 2
    s["loan_percent_income"] = (s["loan_amnt"] / s["person_income"]).round(2)
    return s


if __name__ == "__main__":
    model = joblib.load(MODELS / f"model_{MODEL_VERSION}.joblib")
    ref = pd.read_csv(PROCESSED / "train.csv")
    normal = pd.read_csv(PROCESSED / "test.csv")
    downturn = stress(normal)
    summary = (drift_table(ref, normal, model).rename(columns={"psi": "psi_normal", "status": "status_normal"})
               .merge(drift_table(ref, downturn, model).rename(columns={"psi": "psi_downturn", "status": "status_downturn"}),
                      on="feature"))
    print(summary.to_string(index=False))
    for name, df in [("normal", normal), ("downturn", downturn)]:
        p = model.predict_proba(df[FEATURES])[:, 1]
        print(f"{name}: mean PD {p.mean():.3f}, approve {np.mean(p < APPROVE_BELOW):.3f}, "
              f"review {np.mean((p >= APPROVE_BELOW) & (p < REJECT_FROM)):.3f}, reject {np.mean(p >= REJECT_FROM):.3f}")
    REPORTS.mkdir(exist_ok=True)
    summary.to_csv(REPORTS / "drift_summary.csv", index=False)
    evidently_report(ref, downturn, REPORTS / "drift_report_downturn.html")
    print("Saved reports/drift_summary.csv and reports/drift_report_downturn.html")
