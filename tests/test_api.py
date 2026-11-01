import pandas as pd
from fastapi.testclient import TestClient
from src.api.main import app
from src.config import PROCESSED, FEATURES
from src.drift import stress

GOOD = {"person_age": 28, "person_income": 42000, "person_home_ownership": "RENT", "person_emp_length": 3,
        "loan_intent": "MEDICAL", "loan_grade": "C", "loan_amnt": 12000, "loan_int_rate": 13.5,
        "cb_person_default_on_file": "N", "cb_person_cred_hist_length": 4}


def test_health():
    with TestClient(app) as c:
        assert c.get("/health").json()["status"] == "ok"


def test_predict_valid():
    with TestClient(app) as c:
        body = c.post("/predict", json=GOOD).json()
        assert 0 <= body["probability_of_default"] <= 1
        assert body["decision"] in {"APPROVE", "REVIEW", "REJECT"}
        assert len(body["top_reasons"]) <= 3


def test_rejects_bad_age():
    with TestClient(app) as c:
        assert c.post("/predict", json={**GOOD, "person_age": 7}).status_code == 422


def test_rejects_unknown_grade():
    with TestClient(app) as c:
        assert c.post("/predict", json={**GOOD, "loan_grade": "Z"}).status_code == 422


def test_missing_field():
    with TestClient(app) as c:
        bad = {k: v for k, v in GOOD.items() if k != "loan_amnt"}
        assert c.post("/predict", json=bad).status_code == 422


def test_nullable_fields_accepted():
    with TestClient(app) as c:
        assert c.post("/predict", json={**GOOD, "person_emp_length": None, "loan_int_rate": None}).status_code == 200


def test_kill_switch_sends_everything_to_review(monkeypatch):
    import src.api.main as api
    monkeypatch.setattr(api, "KILL_SWITCH", True)
    with TestClient(app) as c:
        assert c.post("/predict", json=GOOD).json()["decision"] == "REVIEW"


def test_drift_endpoint_flags_a_downturn():
    rows = stress(pd.read_csv(PROCESSED / "test.csv").sample(300, random_state=3))
    fields = [f for f in FEATURES if f != "loan_percent_income"]
    payloads = rows[fields].astype(object).where(rows[fields].notna(), None).to_dict("records")
    with TestClient(app) as c:
        for p in payloads:
            assert c.post("/predict", json=p).status_code == 200
        body = c.get("/monitoring/drift?last_n=300").json()
        assert "loan_int_rate" in body["alerts"]
