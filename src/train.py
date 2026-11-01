"""Phase 4: train Logistic Regression, Random Forest and XGBoost; pick the best on validation AUC; save it."""
import json
import time
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, roc_curve
from xgboost import XGBClassifier
from src.config import PROCESSED, MODELS, CANDIDATES_DIR, TARGET, NUM, CAT, FEATURES, SEED, MODEL_VERSION

XGB_PARAMS = dict(n_estimators=600, learning_rate=0.05, max_depth=5, subsample=0.8, colsample_bytree=0.8,
                  eval_metric="auc", n_jobs=-1, random_state=SEED)


def metrics(y, p) -> dict:
    auc = roc_auc_score(y, p)
    fpr, tpr, _ = roc_curve(y, p)
    return {"auc": round(auc, 4), "gini": round(2 * auc - 1, 4), "pr_auc": round(average_precision_score(y, p), 4),
            "ks": round(float(np.max(tpr - fpr)), 4), "brier": round(brier_score_loss(y, p), 4)}


def linear_prep(num=NUM, cat=CAT):   # LR needs scaled numbers and one column per category value
    return ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat)])


def tree_prep(num=NUM, cat=CAT):     # trees need no scaling; one integer column per category keeps SHAP per feature
    return ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), num),
        ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), cat)],
        verbose_feature_names_out=False)


MODEL_FACTORIES = {
    "logistic_regression": lambda: Pipeline([("prep", linear_prep()),
        ("model", LogisticRegression(max_iter=2000, class_weight="balanced"))]),
    "random_forest": lambda: Pipeline([("prep", tree_prep()),
        ("model", RandomForestClassifier(n_estimators=400, min_samples_leaf=2, class_weight="balanced_subsample",
                                         n_jobs=-1, random_state=SEED))]),
    "xgboost": lambda: Pipeline([("prep", tree_prep()), ("model", XGBClassifier(**XGB_PARAMS))]),
}

if __name__ == "__main__":
    train = pd.read_csv(PROCESSED / "train.csv")
    val = pd.read_csv(PROCESSED / "val.csv")
    results, fitted = {}, {}
    for name, make in MODEL_FACTORIES.items():
        pipe = make()
        start = time.time()
        pipe.fit(train[FEATURES], train[TARGET])
        results[name] = metrics(val[TARGET], pipe.predict_proba(val[FEATURES])[:, 1])
        results[name]["train_seconds"] = round(time.time() - start, 1)
        fitted[name] = pipe
        print(f"{name:20s} {results[name]}")

    best = max(results, key=lambda n: results[n]["auc"])
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    for name, pipe in fitted.items():                       # kept so evaluate.py can report all three on test
        joblib.dump(pipe, CANDIDATES_DIR / f"{name}.joblib", compress=3)
    joblib.dump(fitted[best], MODELS / f"model_{MODEL_VERSION}.joblib")
    meta = {"model_version": MODEL_VERSION, "model_name": best,
            "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "features": FEATURES, "validation_metrics": results,
            "train_rows": len(train), "train_default_rate": round(float(train[TARGET].mean()), 4)}
    (MODELS / f"metadata_{MODEL_VERSION}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Best model: {best} (val AUC {results[best]['auc']}) saved to models/")
