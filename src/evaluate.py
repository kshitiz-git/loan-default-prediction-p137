"""Phase 5a: score the untouched test set once - metrics for all three candidates, risk bands, NPA back-test."""
import json
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve
from src.config import (PROCESSED, MODELS, CANDIDATES_DIR, REPORTS, TARGET, FEATURES, MODEL_VERSION,
                        APPROVE_BELOW, REJECT_FROM)
from src.train import metrics, MODEL_FACTORIES

GRADE_RULES = {"A only": ["A"], "A-B": ["A", "B"], "A-C": ["A", "B", "C"],
               "A-D": ["A", "B", "C", "D"], "All grades": list("ABCDEFG")}
CURVE_RATES = [0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]


def npa_ratio(amount, defaulted, approved) -> float:
    """Gross NPA ratio by amount = defaulted amount / total amount lent, over approved loans only."""
    return float((amount * defaulted)[approved].sum() / amount[approved].sum())


def approve_lowest(pd_hat, rate: float) -> np.ndarray:
    """Approve the round(rate * n) applicants with the lowest PD (stable sort); returns a boolean mask."""
    k = int(round(rate * len(pd_hat)))
    mask = np.zeros(len(pd_hat), dtype=bool)
    mask[np.argsort(pd_hat, kind="stable")[:k]] = True
    return mask


def score_candidates(test: pd.DataFrame) -> tuple[dict, dict]:
    """Test metrics and ROC curve for every saved candidate pipeline."""
    test_metrics, curves = {}, {}
    for name in MODEL_FACTORIES:
        pipe = joblib.load(CANDIDATES_DIR / f"{name}.joblib")
        p = pipe.predict_proba(test[FEATURES])[:, 1]
        test_metrics[name] = metrics(test[TARGET], p)
        curves[name] = roc_curve(test[TARGET], p)[:2]
        print(f"TEST {name:20s} {test_metrics[name]}")
    return test_metrics, curves


def risk_bands(pd_hat: np.ndarray, y: np.ndarray) -> dict:
    """Share of applicants and actual default rate in each decision band."""
    masks = {"APPROVE": pd_hat < APPROVE_BELOW,
             "REVIEW": (pd_hat >= APPROVE_BELOW) & (pd_hat < REJECT_FROM),
             "REJECT": pd_hat >= REJECT_FROM}
    bands = {b: {"share": round(float(m.mean()), 3), "default_rate": round(float(y[m].mean()), 3)}
             for b, m in masks.items()}
    print("Bands: " + " | ".join(f"{b} share {v['share']}, default rate {v['default_rate']}" for b, v in bands.items()))
    return bands


def grade_backtest(test: pd.DataFrame, pd_hat: np.ndarray) -> pd.DataFrame:
    """Each grade rule vs the model approving the same share of applicants (matched approval rate)."""
    amount, defaulted = test["loan_amnt"].to_numpy(), test[TARGET].to_numpy()
    rows = []
    for rule, grades in GRADE_RULES.items():
        rule_mask = test["loan_grade"].isin(grades).to_numpy()
        model_mask = approve_lowest(pd_hat, rule_mask.mean())
        rule_npa, model_npa = npa_ratio(amount, defaulted, rule_mask), npa_ratio(amount, defaulted, model_mask)
        rows.append({"rule": rule, "approval_rate": round(float(rule_mask.mean()), 3),
                     "rule_npa": round(rule_npa, 4), "model_npa": round(model_npa, 4),
                     "cut_%": round((1 - model_npa / rule_npa) * 100, 1)})
    table = pd.DataFrame(rows)
    print("\n" + table.to_string(index=False) + "\n")
    return table


def policies(test: pd.DataFrame, pd_hat: np.ndarray) -> dict:
    amount, defaulted = test["loan_amnt"].to_numpy(), test[TARGET].to_numpy()
    out = {}
    for label, mask in [("Approve everyone", np.ones(len(pd_hat), dtype=bool)),
                        ("Model bands: APPROVE only (PD<0.20)", pd_hat < APPROVE_BELOW),
                        ("Model bands: APPROVE + REVIEW (PD<0.50)", pd_hat < REJECT_FROM)]:
        out[label] = {"approval_rate": round(float(mask.mean()), 3), "npa": round(npa_ratio(amount, defaulted, mask), 4)}
        print(f"{label:42s} approval {out[label]['approval_rate']:.3f}   NPA {out[label]['npa']:.4f}")
    return out


def model_curve(test: pd.DataFrame, pd_hat: np.ndarray) -> dict:
    amount, defaulted = test["loan_amnt"].to_numpy(), test[TARGET].to_numpy()
    curve = {f"{r:.2f}": round(npa_ratio(amount, defaulted, approve_lowest(pd_hat, r)), 4) for r in CURVE_RATES}
    print("\nModel curve: " + " | ".join(f"{r} -> {v:.4f}" for r, v in curve.items()))
    return curve


def plot_roc(curves: dict, test_metrics: dict) -> None:
    plt.figure(figsize=(6, 5))
    for name, (fpr, tpr) in curves.items():
        plt.plot(fpr, tpr, label=f"{name} (AUC {test_metrics[name]['auc']:.4f})")
    plt.plot([0, 1], [0, 1], "k--", lw=1, label="random")
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate")
    plt.title("ROC curves on the test set"); plt.legend(loc="lower right"); plt.tight_layout()
    plt.savefig(REPORTS / "roc_curves.png", dpi=150); plt.close()


def plot_npa(curve: dict, table: pd.DataFrame) -> None:
    plt.figure(figsize=(7, 5))
    plt.plot([float(r) * 100 for r in curve], [v * 100 for v in curve.values()], "o-", label="Model (lowest PD first)")
    plt.plot(table["approval_rate"] * 100, table["rule_npa"] * 100, "s--", label="Grade rules (A, A-B, ... all)")
    for _, r in table.iterrows():
        plt.annotate(r["rule"], (r["approval_rate"] * 100, r["rule_npa"] * 100), textcoords="offset points",
                     xytext=(-10, 6), fontsize=8)
    plt.xlabel("Share of applicants approved (%)"); plt.ylabel("NPA ratio by amount (%)")
    plt.title("NPA ratio vs approval rate (test set)"); plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(REPORTS / "npa_vs_approval.png", dpi=150); plt.close()


if __name__ == "__main__":
    test = pd.read_csv(PROCESSED / "test.csv")
    REPORTS.mkdir(exist_ok=True)
    test_metrics, curves = score_candidates(test)
    model = joblib.load(MODELS / f"model_{MODEL_VERSION}.joblib")
    pd_hat = model.predict_proba(test[FEATURES])[:, 1]
    bands = risk_bands(pd_hat, test[TARGET].to_numpy())
    table = grade_backtest(test, pd_hat)
    pol = policies(test, pd_hat)
    curve = model_curve(test, pd_hat)
    plot_roc(curves, test_metrics)
    plot_npa(curve, table)
    report = {"test_metrics": test_metrics, "bands": bands, "grade_backtest": table.to_dict(orient="records"),
              "policies": pol, "model_curve": curve}
    (REPORTS / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Saved reports/evaluation.json, roc_curves.png, npa_vs_approval.png")
