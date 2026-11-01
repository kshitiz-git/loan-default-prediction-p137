"""Phase 6: SHAP explanations - global importance plots and plain-language top-3 reasons for one applicant."""
import json
import math
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from src.config import PROCESSED, MODELS, REPORTS, FEATURES, MODEL_VERSION

REASON_TEXT = {                        # words a loan officer can read out to the applicant
    "person_income": "Income is low for the amount requested",
    "loan_grade": "Weak credit grade",
    "loan_percent_income": "Loan is large compared with income",
    "person_home_ownership": "Home ownership status",
    "loan_intent": "Purpose of the loan",
    "loan_int_rate": "High interest rate on the loan",
    "loan_amnt": "Large loan amount",
    "person_emp_length": "Short time in current job",
    "person_age": "Age profile",
    "cb_person_cred_hist_length": "Short credit history",
    "cb_person_default_on_file": "Past default on credit file",
}


def plain(value):
    """numpy scalar -> Python value; NaN -> None (JSON cannot carry NaN)."""
    if isinstance(value, np.generic):
        value = value.item()
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return value


class Explainer:
    """SHAP on the XGBoost step, fed by the pipeline's own preprocessing (one column per original feature)."""

    def __init__(self, pipeline):
        self.prep = pipeline.named_steps["prep"]
        self.tree = shap.TreeExplainer(pipeline.named_steps["model"])
        self.names = list(self.prep.get_feature_names_out())

    def shap_values(self, X: pd.DataFrame) -> np.ndarray:
        return self.tree.shap_values(self.prep.transform(X[FEATURES]))     # log-odds units

    def base_value(self) -> float:
        """Read only AFTER shap_values() has run once: SHAP fills expected_value in lazily."""
        return float(np.atleast_1d(self.tree.expected_value)[0])

    def reasons(self, applicant: pd.DataFrame, top_k: int = 3) -> list[dict]:
        """Up to top_k features that pushed THIS applicant's risk up (positive SHAP = towards default)."""
        values = self.shap_values(applicant)[0]
        order = np.argsort(values)[::-1][:top_k]
        return [{"feature": self.names[i], "value": plain(applicant.iloc[0][self.names[i]]),
                 "impact": round(float(values[i]), 3), "text": REASON_TEXT[self.names[i]]}
                for i in order if values[i] > 0]


if __name__ == "__main__":
    pipe = joblib.load(MODELS / f"model_{MODEL_VERSION}.joblib")
    test = pd.read_csv(PROCESSED / "test.csv")
    ex = Explainer(pipe)
    sv = ex.shap_values(test)
    Xt = pd.DataFrame(ex.prep.transform(test[FEATURES]), columns=ex.names)

    importance = pd.Series(np.abs(sv).mean(axis=0), index=ex.names).sort_values(ascending=False)
    print("Mean |SHAP| (log-odds):\n" + importance.round(3).to_string())
    margin = pipe.named_steps["model"].predict(ex.prep.transform(test[FEATURES]), output_margin=True)
    print(f"Base value {ex.base_value():.3f} | max additivity error "
          f"{float(np.max(np.abs(ex.base_value() + sv.sum(axis=1) - margin))):.2e}")

    REPORTS.mkdir(exist_ok=True)
    shap.summary_plot(sv, Xt, plot_type="bar", show=False); plt.tight_layout()
    plt.savefig(REPORTS / "shap_importance_bar.png", dpi=150); plt.close()
    shap.summary_plot(sv, Xt, show=False); plt.tight_layout()
    plt.savefig(REPORTS / "shap_beeswarm.png", dpi=150); plt.close()
    (REPORTS / "shap_importance.json").write_text(importance.round(4).to_json(indent=2), encoding="utf-8")

    riskiest = test.iloc[[int(np.argmax(pipe.predict_proba(test[FEATURES])[:, 1]))]]
    print("Riskiest test applicant:", json.dumps(ex.reasons(riskiest)))
