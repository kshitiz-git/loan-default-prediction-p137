import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from src.config import MODELS, PROCESSED, FEATURES, TARGET, MODEL_VERSION
from src.explain import Explainer

MODEL = joblib.load(MODELS / f"model_{MODEL_VERSION}.joblib")
TEST = pd.read_csv(PROCESSED / "test.csv")


def test_auc_meets_target():
    assert roc_auc_score(TEST[TARGET], MODEL.predict_proba(TEST[FEATURES])[:, 1]) >= 0.85


def test_shap_values_add_up_to_the_score():
    ex = Explainer(MODEL)
    sample = TEST.head(200)
    values = ex.shap_values(sample)                              # compute first ...
    margin = MODEL.named_steps["model"].predict(ex.prep.transform(sample[FEATURES]), output_margin=True)
    assert np.max(np.abs(ex.base_value() + values.sum(axis=1) - margin)) < 1e-3   # ... then read the base value


def test_probabilities_are_calibrated_by_decile():
    df = pd.DataFrame({"p": MODEL.predict_proba(TEST[FEATURES])[:, 1], "y": TEST[TARGET]})
    df["decile"] = pd.qcut(df["p"], 10, labels=False, duplicates="drop")
    by = df.groupby("decile").agg(pred=("p", "mean"), actual=("y", "mean"))
    assert (by["pred"] - by["actual"]).abs().max() <= 0.05
