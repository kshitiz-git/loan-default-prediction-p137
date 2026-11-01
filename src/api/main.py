"""Phase 7: real-time scoring API.
Run from the project folder:  .venv\\Scripts\\python.exe -m uvicorn src.api.main:app --port 8000
Then open http://127.0.0.1:8000/docs
"""
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from src.config import MODELS, PROCESSED, FEATURES, MODEL_VERSION, APPROVE_BELOW, REJECT_FROM
from src.explain import Explainer
from src.drift import drift_table                      # Phase 8
from src.api.schemas import LoanApplication, ScoreResponse
from src.api import store

KILL_SWITCH = os.getenv("SCORING_DISABLED") == "1"    # 1 = every application goes to a person (REVIEW)
state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):                      # load once at startup, not on every request
    state["model"] = joblib.load(MODELS / f"model_{MODEL_VERSION}.joblib")
    state["meta"] = json.loads((MODELS / f"metadata_{MODEL_VERSION}.json").read_text(encoding="utf-8"))
    state["explainer"] = Explainer(state["model"])
    state["reference"] = pd.read_csv(PROCESSED / "train.csv")                                 # Phase 8
    val = pd.read_csv(PROCESSED / "val.csv")                                                    # Phase 8
    state["approve_baseline"] = float((state["model"].predict_proba(val[FEATURES])[:, 1] < APPROVE_BELOW).mean())  # Phase 8
    store.init_db()
    yield


app = FastAPI(title="Loan Default Prediction API (P_137)", version=MODEL_VERSION, lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "model_version": MODEL_VERSION, "kill_switch": KILL_SWITCH}


@app.get("/model/info")
def model_info():
    return {**state["meta"], "policy": {"approve_below": APPROVE_BELOW, "reject_from": REJECT_FROM}}


@app.post("/predict", response_model=ScoreResponse)
def predict(application: LoanApplication):
    start = time.perf_counter()
    row = application.model_dump()
    row["loan_percent_income"] = round(row["loan_amnt"] / row["person_income"], 2)   # computed here, never sent
    X = pd.DataFrame([row])[FEATURES]
    pd_hat = float(state["model"].predict_proba(X)[0, 1])
    band, decision = (("low", "APPROVE") if pd_hat < APPROVE_BELOW else
                      ("medium", "REVIEW") if pd_hat < REJECT_FROM else ("high", "REJECT"))
    if KILL_SWITCH:                                      # model still scores and logs; a person decides
        decision = "REVIEW"
    out = {"application_id": str(uuid.uuid4()), "probability_of_default": round(pd_hat, 4), "risk_band": band,
           "decision": decision, "top_reasons": state["explainer"].reasons(X), "model_version": MODEL_VERSION,
           "latency_ms": round((time.perf_counter() - start) * 1000, 2)}
    store.log_prediction({**row, "application_id": out["application_id"], "model_version": MODEL_VERSION,
                          "pd": out["probability_of_default"], "decision": decision, "latency_ms": out["latency_ms"]})
    return out


# ---- Phase 8: everything below this line ----
@app.get("/monitoring/drift")
def monitoring_drift(last_n: int = 500):
    logs = store.recent(last_n)
    if len(logs) < 100:
        raise HTTPException(status_code=409, detail=f"Need at least 100 logged predictions, have {len(logs)}")
    table = drift_table(state["reference"], logs, state["model"])
    alerts = table[table.status == "alert"].feature.tolist()
    mix = logs["decision"].value_counts(normalize=True).round(3).to_dict()
    if abs(mix.get("APPROVE", 0.0) - state["approve_baseline"]) > 0.10:   # approvals moved more than 10 points
        alerts.append("decision_mix")
    return {"window_size": len(logs), "alerts": alerts, "decision_mix": mix,
            "approve_baseline": round(state["approve_baseline"], 3), "features": table.to_dict(orient="records")}
