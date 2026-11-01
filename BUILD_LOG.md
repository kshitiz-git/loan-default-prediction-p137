# Build log — P_137

Machine: Windows 11, 16 logical CPUs, Python 3.13.14 (`.venv`), packages exactly as in `requirements.txt`.
All ten phases were built and checked on 2026-11-01.

## Phase 1 — Environment and dataset check — 2026-11-01
- Files: `requirements.txt`, `.gitignore`, `BUILD_LOG.md`, `src/__init__.py`, `src/api/__init__.py`, `scripts/__init__.py`
- Commands: `py -3.13 -m venv .venv`; `pip install --upgrade pip`; `pip install -r requirements.txt`; the Phase 1 import check
- Results: `Python 3.13.14`; `(32581, 12) 3.0.2 1.8.0 3.2.0 0.51.0 0.7.23 0.141.1`
- Matches spec: yes. The CSV is the public Kaggle file `laotse/credit-risk-dataset` (32,581 rows, 7,108 defaults), unchanged.
- In plain words: A virtual environment keeps this project's exact library versions separate from anything else on the laptop, so results are repeatable. The check proves every library imports and the raw dataset has the expected 32,581 rows and 12 columns.

## Phase 2 — Exploratory data analysis notebook — 2026-11-01
- Files: `notebooks/01_eda.ipynb`, six PNGs in `reports/eda/`
- Commands: `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda.ipynb`
- Results: counts {0: 25473, 1: 7108}, default rate 0.218; missing emp_length 895, int_rate 3116; duplicates 165, age > 100: 5, employment > 60: 2; default % by grade A 10.0 … G 98.4; by intent VENTURE 14.8 … DEBTCONSOLIDATION 28.6; correlation with loan_status: loan_percent_income 0.38, loan_int_rate 0.34, person_income -0.14, loan_amnt 0.11, person_emp_length -0.08
- Matches spec: yes, every number.
- In plain words: EDA shows what the data looks like before any modelling. About one loan in five defaulted, two columns have gaps, and a few rows are impossible (age 144). Risk rises sharply from grade C to D, and the loan-to-income ratio is the strongest single signal.

## Phase 3 — Clean and split — 2026-11-01
- Files: `src/config.py`, `src/data_prep.py`, `data/processed/{train,val,test}.csv`
- Commands: `python -m src.data_prep`
- Results: `Cleaning: 32581 rows -> 32409 rows`; train 22686 / val 4861 / test 4862 rows, default rate 0.219 each
- Matches spec: yes.
- In plain words: Three fixed rules remove duplicates and impossible ages or job lengths; missing values are kept and filled later inside the model pipeline. The data is split 70/15/15, stratified so each part has the same 21.9% default rate. The test part is not touched until the final evaluation.

## Phase 4 — Train three models — 2026-11-01
- Files: `src/train.py`, `models/model_v1.joblib`, `models/metadata_v1.json`, `models/candidates/*.joblib`
- Commands: `python -m src.train`
- Results (validation): LR AUC 0.8789; RF AUC 0.9368; XGBoost AUC 0.9511, gini 0.9022, pr_auc 0.9102, ks 0.7724, brier 0.0507. Best model: xgboost.
- Matches spec: yes, within tolerance. LR and RF match to 4 decimals. XGBoost AUC 0.9511 vs 0.9513 (difference 0.0002, limit 0.002).
  Root cause, measured: XGBoost's histogram sums depend on how many CPU threads build them (`n_jobs=-1` = all 16 here). Re-training with 1–16 threads gave validation AUC 0.9506–0.9523 and test AUC 0.9465–0.9478. The spec's code and parameters were kept unchanged.
- In plain words: Three models of increasing power are trained on the same data, each inside one Pipeline that also does the imputing and encoding, so the API can never preprocess differently. No resampling is used because synthetic rows distort probabilities. XGBoost wins on validation AUC, and only then is the test set used.

## Phase 5 — Test-set evaluation, NPA back-test and robustness — 2026-11-01
- Files: `src/evaluate.py`, `src/robustness.py`, `reports/evaluation.json`, `reports/roc_curves.png`, `reports/npa_vs_approval.png`, `reports/robustness.json`
- Commands: `python -m src.evaluate`; `python -m src.robustness`
- Results: test AUC LR 0.8614, RF 0.9291, XGBoost 0.9469. Bands: APPROVE 75.3% (default 5.0%), REVIEW 8.3% (26.1%), REJECT 16.4% (97.0%).
  NPA back-test at the A–C approval rate (85.5%): rule 17.75% → model 8.12%, **54.3% lower** (A only 95.3%, A-B 78.3%, A-D 9.2%).
  Policies: approve all 24.93% NPA; APPROVE only 75.3% approved, 4.87% NPA; APPROVE + REVIEW 83.6%, 6.59% NPA.
  5-fold CV AUC: LR 0.8707 ± 0.0059, RF 0.9336 ± 0.0021, XGBoost 0.9497 ± 0.0024. Ablation without grade and rate: 0.9020.
- Matches spec: yes, within tolerance. XGBoost test AUC 0.9469 vs 0.9478 (0.0009 < 0.002); A–C NPA 8.12% vs 8.11% (0.01 pp < 0.3 pp); headline cut identical (54.3%). LR, RF and the grade-rule NPA ratios match exactly. Same thread-count cause as Phase 4.
- In plain words: On data the model has never seen, it ranks defaulters well (AUC 0.947). If the bank approved the same 85.5% of applicants as its grade A–C rule but chose them by the model's PD, the defaulted share of the money lent would fall from 17.75% to 8.12%. Cross-validation shows the AUC barely moves between folds, so the result is stable.

## Phase 6 — SHAP explanations — 2026-11-01
- Files: `src/explain.py`, `reports/shap_importance_bar.png`, `reports/shap_beeswarm.png`, `reports/shap_importance.json`
- Commands: `python -m src.explain`
- Results: top features person_income 0.923, loan_grade 0.892, loan_percent_income 0.827, person_home_ownership 0.687, loan_intent 0.558. Base value -1.289, max additivity error 1.34e-05. Riskiest applicant: loan_percent_income 0.56 (+4.712), person_income 14400 (+4.309), loan_intent HOMEIMPROVEMENT (+2.137).
- Matches spec: yes. Same feature order, same riskiest applicant and same three reasons; values differ by ≤ 0.13 because of the Phase 4 thread effect; additivity error is far below 0.001.
- In plain words: SHAP splits each prediction into one contribution per feature, and the contributions add up exactly to the model's score. The three largest risk-raising contributions are turned into fixed plain-language reasons that a loan officer can read out.

## Phase 7 — Scoring API — 2026-11-01
- Files: `src/api/schemas.py`, `src/api/store.py`, `src/api/main.py`
- Commands: started uvicorn on port 8000 in the background, called the endpoints with the section 8 helpers, stopped the server
- Results: `/health` ok, kill_switch false. `$good` → PD 0.0953, low, APPROVE; reasons RENT +0.267, income 42000 +0.099, MEDICAL +0.051. `$risky` → PD 1.0, high, REJECT; reasons loan_percent_income 0.5 +4.2, income 18000 +3.686, RENT +1.625. Age 7 → HTTP 422. latency_ms 24–34.
- Matches spec: decisions, bands, reasons and their order match. `$good` PD 0.0953 vs 0.105: across 1–16 threads this one applicant's PD ranges 0.074–0.101, so the exact reference value cannot be reproduced on this CPU; the decision (APPROVE) is the same.
- In plain words: The API loads the saved pipeline once at start-up, validates every request with Pydantic (bad input gets HTTP 422), computes loan_percent_income itself, and returns PD, decision and up to three reasons in well under 100 ms. Every scored application is written to SQLite for monitoring.

## Phase 8 — Drift monitoring — 2026-11-01
- Files: `src/drift.py`, `/monitoring/drift` in `src/api/main.py`, `scripts/simulate_traffic.py`, `reports/drift_summary.csv`, `reports/drift_report_downturn.html`
- Commands: `python -m src.drift`; live check B (fresh log → 409 → 500 normal → drift → 500 downturn → drift)
- Results offline: all 11 feature PSIs match the spec exactly (loan_int_rate downturn 1.1231 alert, person_income 0.1875 watch, loan_percent_income 0.1114 watch); model_score_PD 0.0040 → 0.1672 (watch).
  Live: empty log → HTTP 409. Normal traffic: p95 45.6 ms, {APPROVE 0.718, REJECT 0.184, REVIEW 0.098}, alerts []. Downturn: p95 44.9 ms, {APPROVE 0.572, REJECT 0.274, REVIEW 0.154}, alerts ['loan_int_rate', 'decision_mix']. PSI normal → downturn: loan_int_rate 0.012 → 1.178, person_income 0.019 → 0.203, loan_percent_income 0.013 → 0.123, model_score_PD 0.026 → 0.237. approve_baseline 0.75.
- Matches spec: yes. Same alerts, feature PSIs match; PD-score PSI and decision mix within the thread-effect margin.
- Latency note (measured 2026-11-01 while recording the screenshots): one 500-request normal run made while four document-building processes and a browser were using the CPU gave p95 136.5 ms (p50 44.0 ms), above the 100 ms target. Repeated on the less loaded machine: 42.7 ms (normal) and 39.4 ms (downturn). The target holds when the API has the CPU to itself; a production deployment would run the API on its own machine or container.
- In plain words: PSI measures how far the recent applicants' distribution has moved from the training data. A simulated downturn (incomes -20%, rates +2 points) pushes the interest-rate PSI far past the 0.25 alert line and drops approvals by more than 10 points, so both alerts fire, while normal traffic raises none.

## Phase 9 — Automated tests — 2026-11-01
- Files: `tests/conftest.py`, `tests/test_data.py`, `tests/test_model.py`, `tests/test_api.py`
- Commands: `python -m pytest -q tests`
- Results: `13 passed, 1 warning in 18.70s` (the warning is the harmless StarletteDeprecationWarning about httpx)
- Matches spec: yes.
- In plain words: Thirteen automatic tests check the cleaning counts, the splits, the AUC target, SHAP additivity, calibration by decile, input validation, the kill switch and the drift alert. Tests write to a temporary database, so they never touch the real log.

## Phase 10 — README, demo rehearsal and final check — 2026-11-01
- Files: `README.md`
- Commands: kill-switch run with `SCORING_DISABLED=1`; full pipeline re-run; pytest
- Results: kill switch → `$good` decision REVIEW (PD 0.0953 still scored and logged), `/health` kill_switch true.
- Matches spec: yes.

## Final summary
| Objective | Target | Result |
| --- | --- | --- |
| Test ROC-AUC | ≥ 0.85 | 0.9469 (XGBoost) ✅ |
| NPA cut vs grade A–C rule | ≥ 30% | 54.3% lower (17.75% → 8.12%) ✅ |
| Reasons on REVIEW/REJECT | 100% | 100% — 1,201 of 1,201 test-set REVIEW/REJECT cases have ≥ 1 risk-raising reason ✅ |
| p95 latency of POST /predict | < 100 ms | 45.6 ms (500 requests) ✅ |
| Drift alert on downturn | alert raised | loan_int_rate PSI 1.178 + decision_mix ✅ |
| 5-fold CV AUC sd | < 0.01 | 0.0024 ✅ |
| pytest | 13 passed | 13 passed ✅ |
