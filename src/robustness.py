"""Phase 5b: stability checks - 5-fold cross-validated AUC per model and an ablation without the lender's grade/rate.
Nothing here influences model selection; it only shows how much the result can be trusted."""
import json
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from src.config import PROCESSED, REPORTS, TARGET, NUM, CAT, FEATURES
from src.data_prep import load_and_clean
from src.train import MODEL_FACTORIES, XGB_PARAMS, tree_prep


def cross_validation(data: pd.DataFrame) -> dict:
    """Different seed (7) from the split so the folds are independent of the train/val/test cut."""
    out = {}
    for name, make in MODEL_FACTORIES.items():
        scores = cross_val_score(make(), data[FEATURES], data[TARGET],
                                 cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=7),
                                 scoring="roc_auc", n_jobs=1)
        out[name] = {"mean": round(float(scores.mean()), 4), "sd": round(float(scores.std()), 4),
                     "min": round(float(scores.min()), 4), "folds": [round(float(s), 4) for s in scores]}
        print(f"{name:20s} 5-fold AUC mean {out[name]['mean']:.4f}  sd {out[name]['sd']:.4f}  min {out[name]['min']:.4f}")
    return out


def ablation() -> float:
    """XGBoost without loan_grade and loan_int_rate: how much does the model rely on the lender's own pricing?"""
    num2 = [c for c in NUM if c != "loan_int_rate"]
    cat2 = [c for c in CAT if c != "loan_grade"]
    train, test = pd.read_csv(PROCESSED / "train.csv"), pd.read_csv(PROCESSED / "test.csv")
    pipe = Pipeline([("prep", tree_prep(num2, cat2)), ("model", XGBClassifier(**XGB_PARAMS))])
    pipe.fit(train[num2 + cat2], train[TARGET])
    auc = round(float(roc_auc_score(test[TARGET], pipe.predict_proba(test[num2 + cat2])[:, 1])), 4)
    print(f"XGBoost without loan_grade and loan_int_rate: test AUC {auc:.4f}")
    return auc


if __name__ == "__main__":
    cv = cross_validation(load_and_clean())
    abl = ablation()
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "robustness.json").write_text(json.dumps({"cv_5fold": cv, "ablation_no_grade_no_rate_test_auc": abl},
                                                        indent=2), encoding="utf-8")
    print("Saved reports/robustness.json")
