# Loan Default Prediction System (P_137)

A machine-learning system that predicts each loan applicant's probability of default (PD) at application time and turns it into **APPROVE**, **REVIEW** or **REJECT** with up to three plain-language reasons (SHAP). A FastAPI service scores applications in real time, logs every prediction to SQLite, and raises drift alerts (PSI) when new applicants stop looking like the training data.

Dataset: *Credit Risk Dataset* by laotse on Kaggle — https://www.kaggle.com/datasets/laotse/credit-risk-dataset (32,581 loans, 12 columns, 21.8% defaulted).

## 1. Results (test set of 4,862 loans, built 2026-11-01)

| Model | Test ROC-AUC | Gini | PR-AUC | KS | Brier | 5-fold CV AUC (mean ± sd) |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression | 0.8614 | 0.7229 | 0.6946 | 0.5884 | 0.1432 | 0.8707 ± 0.0059 |
| Random Forest | 0.9291 | 0.8582 | 0.8792 | 0.7227 | 0.0625 | 0.9336 ± 0.0021 |
| **XGBoost (deployed)** | **0.9469** | 0.8938 | 0.9028 | 0.7525 | 0.0529 | 0.9497 ± 0.0024 |

- **NPA back-test.** The lender's grade A–C rule approves 85.5% of applicants with an NPA ratio by amount of **17.75%**. Approving the same 85.5% by lowest model PD gives **8.12%**, which is **54.3% lower**.
- **Decision bands:** APPROVE (PD < 0.20) covers 75.3% of applicants and 5.0% of them default; REVIEW (0.20–0.50) covers 8.3% (26.1%); REJECT (≥ 0.50) covers 16.4% (97.0%).
- **Latency:** the 95th-percentile round trip of `POST /predict` was 45.6 ms over 500 requests.
- **Drift demo:** normal traffic raises no alert. Downturn traffic (incomes −20%, rates +2 points) raises `loan_int_rate` (PSI 1.178) and `decision_mix` (approvals 57.2% vs 75.0% baseline).
- **Ablation:** without `loan_grade` and `loan_int_rate` the model still reaches test AUC 0.9020.

## 2. Setup on Windows

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download the CSV from Kaggle and save it as `data\raw\credit_risk_dataset.csv`. Python 3.11–3.14 works; 3.13 is recommended.

## 3. Run the pipeline (from the project folder, in this order)

```powershell
.\.venv\Scripts\python.exe -m src.data_prep     # clean + 70/15/15 split -> data/processed/
.\.venv\Scripts\python.exe -m src.train         # 3 models, best on validation AUC -> models/
.\.venv\Scripts\python.exe -m src.evaluate      # test metrics, bands, NPA back-test -> reports/
.\.venv\Scripts\python.exe -m src.robustness    # 5-fold CV + ablation (about 1 minute)
.\.venv\Scripts\python.exe -m src.explain       # SHAP importance + reasons
.\.venv\Scripts\python.exe -m src.drift         # PSI table + Evidently HTML report
```

EDA notebook: `.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda.ipynb` (charts go to `reports/eda/`).

## 4. Run the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs. Example request:

```powershell
$good = @{ person_age = 28; person_income = 42000; person_home_ownership = "RENT"; person_emp_length = 3; loan_intent = "MEDICAL"; loan_grade = "C"; loan_amnt = 12000; loan_int_rate = 13.5; cb_person_default_on_file = "N"; cb_person_cred_hist_length = 4 }
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/predict" -ContentType "application/json" -Body ($good | ConvertTo-Json) | ConvertTo-Json -Depth 5
```

Response (shortened):

```json
{ "probability_of_default": 0.0953, "risk_band": "low", "decision": "APPROVE",
  "top_reasons": [ {"feature": "person_home_ownership", "value": "RENT", "impact": 0.267, "text": "Home ownership status"},
                   {"feature": "person_income", "value": 42000.0, "impact": 0.099, "text": "Income is low for the amount requested"},
                   {"feature": "loan_intent", "value": "MEDICAL", "impact": 0.051, "text": "Purpose of the loan"} ],
  "model_version": "v1", "latency_ms": 34.19 }
```

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | status, model version, kill-switch state |
| GET | `/model/info` | training metadata + policy cut-offs |
| POST | `/predict` | PD, band, decision, up to 3 reasons, latency; logs one row |
| GET | `/monitoring/drift?last_n=500` | PSI per feature and on the score, alerts (HTTP 409 below 100 logged rows) |

The client never sends `loan_percent_income`; the server computes it. Invalid input gets HTTP 422.

## 5. Monitoring demo

```powershell
.\.venv\Scripts\python.exe -m scripts.simulate_traffic --n 500              # normal applicants
Invoke-RestMethod "http://127.0.0.1:8000/monitoring/drift?last_n=500"        # alerts: []
.\.venv\Scripts\python.exe -m scripts.simulate_traffic --n 500 --downturn   # simulated recession
Invoke-RestMethod "http://127.0.0.1:8000/monitoring/drift?last_n=500"        # alerts: loan_int_rate, decision_mix
```

**Kill switch:** start the server with `$env:SCORING_DISABLED = "1"`. Every decision becomes REVIEW, but applications are still scored and logged, and `/health` shows `kill_switch: true`.

## 6. Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests      # 13 passed
```

## 7. Project structure

```text
├── BUILD_LOG.md  README.md  requirements.txt  .gitignore
├── data/raw/credit_risk_dataset.csv     data/processed/{train,val,test}.csv
├── models/model_v1.joblib  metadata_v1.json  candidates/
├── logs/predictions.db                  (created by the API)
├── reports/eda/ (6 charts)  evaluation.json  roc_curves.png  npa_vs_approval.png  robustness.json
│           shap_importance_bar.png  shap_beeswarm.png  shap_importance.json  drift_summary.csv  drift_report_downturn.html
├── notebooks/01_eda.ipynb
├── src/config.py  data_prep.py  train.py  evaluate.py  robustness.py  explain.py  drift.py
│   └── api/schemas.py  store.py  main.py
├── scripts/simulate_traffic.py
└── tests/conftest.py  test_data.py  test_model.py  test_api.py
```

## 8. Limitations

- The Kaggle data simulates credit-bureau data; it is not a real lender's book.
- Its 21.8% default rate is far above the roughly 1.8% gross NPA ratio of Indian banks, so absolute NPA numbers do not transfer; the relative gain is the useful result.
- The back-test only sees loans that were granted (no reject inference).
- The data has no dates, so drift is simulated rather than observed over time.
- PSI thresholds (0.10 / 0.25) are industry rules of thumb, not statistical tests.
- There is no fairness audit across age or other groups.
- XGBoost results vary slightly with the CPU thread count (test AUC 0.9465–0.9478 across 1–16 threads on this machine).
