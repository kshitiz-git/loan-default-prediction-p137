# Comments on this repository

Project P_137, **Loan Default Prediction System**, built on 1 November 2026 on Windows 11 with Python 3.13.14.
This file explains what is in the repository, where to find the submission files, how everything was produced, and
every place where the result differs from the project specification.

## 1. Where to find what

| You want | Open |
| --- | --- |
| The 9 files to upload (7 PDFs + `dataset.csv` + `data_dictionary.csv`) | [`submission/final/UPLOAD/`](submission/final/UPLOAD/) |
| Editable Word versions of the 7 documents | [`submission/final/`](submission/final/) (`.docx`) |
| How to install, run the pipeline, the API and the tests | [`README.md`](README.md) |
| Every phase with commands, real results and a plain explanation | [`BUILD_LOG.md`](BUILD_LOG.md) |
| Real console output of every command (the numbers in the documents come from here) | [`_evidence/`](_evidence/) |
| Source code | [`src/`](src/), [`src/api/`](src/api/), [`scripts/`](scripts/), [`tests/`](tests/) |
| EDA notebook (executed) | [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb) |
| Charts and JSON results | [`reports/`](reports/) (open `reports/drift_report_downturn.html` in a browser for the Evidently report) |
| Trained models | [`models/model_v1.joblib`](models/), `models/metadata_v1.json`, `models/candidates/` (all three pipelines) |
| Data | `data/raw/credit_risk_dataset.csv` (original Kaggle file), `data/processed/` (train/val/test splits) |
| Prediction log written by the API | `logs/predictions.db` (SQLite, 501 rows from the screenshot run) |
| Diagrams and screenshots used in the documents | [`submission/figures/`](submission/figures/) |
| Scripts that build the documents | [`submission/build/`](submission/build/), master script `build_all.ps1` |

## 2. Results in one table (test set of 4,862 loans)

| Objective | Target | Result |
| --- | --- | --- |
| ROC-AUC of the deployed XGBoost model | ≥ 0.85 | 0.9469 |
| NPA ratio vs the grade A–C rule at the same 85.5% approval rate | ≥ 30% lower | 54.3% lower (17.75% → 8.12%) |
| REVIEW/REJECT cases with plain-language reasons | 100% | 100% (1,201 of 1,201) |
| p95 latency of `POST /predict` | < 100 ms | 45.6 ms (500 requests) |
| Drift alert on a simulated downturn | alert raised | `loan_int_rate` PSI 1.178 + `decision_mix` |
| Standard deviation of 5-fold CV AUC | < 0.01 | 0.0024 |
| Automated tests | all pass | 13 passed |

## 3. Differences from the specification (read before the viva)

1. **XGBoost numbers differ slightly from the spec's reference build.** Test AUC is 0.9469 against 0.9478 (allowed gap
   0.002). Cause, measured: XGBoost's histogram sums depend on the number of CPU threads (`n_jobs=-1` = 16 here).
   Training with 1 to 16 threads gave test AUC 0.9465 to 0.9478. The code and parameters were not changed.
   Logistic regression, random forest and every data/cleaning/PSI number match the spec exactly.
2. **The dataset was downloaded by the build, not by hand.** The spec said the learner downloads it; the learner later
   asked for everything to be done automatically. It is the public Kaggle file `laotse/credit-risk-dataset`
   (licence CC0: Public Domain, checked through the Kaggle API on 1 November 2026), verified against the spec:
   32,581 rows, 12 columns, 7,108 defaults. It is committed unchanged.
3. **Latency under load.** One 500-request run made while other heavy processes were using the CPU gave p95 136.5 ms;
   repeated on a quieter machine it was 42.7 ms and 39.4 ms. The target holds when the API has the CPU to itself.
4. **`.gitignore` was widened on purpose.** The spec's `.gitignore` left out `data/`, `logs/`, `models/candidates/`
   and the HTML report. They are committed here so the repository is complete. Only `.venv/` (1.3 GB of installed
   libraries; rebuild it with `pip install -r requirements.txt`), Python caches and editor/tool folders are excluded.
5. **Page counts.** Report 54 pages (reference submission 51), SRS 27 (27), Synopsis 4 (4), Declaration 1 (1),
   Source Code 1 (1), Output Screenshots 11 (13), EDA Notebook 6 (14, because this notebook has 6 charts, the
   reference had 11).

## 4. Still to fill in before submitting

The learner's details are placeholders in square brackets, in the documents and in four file names:
`[SURNAME]`, `[ROLL NUMBER]`, `[ADMISSION NUMBER]`, `[CLASS]`, `[COLLEGE, CITY]`, `[MENTOR NAME]`, `[PROGRAM BATCH]`.

1. Edit [`submission/build/identity.json`](submission/build/identity.json) (also `file_name_tag`).
2. Run `powershell -ExecutionPolicy Bypass -File submission\build\build_all.ps1` (about 4 minutes; needs Microsoft
   Word for the PDF export and a Python with python-docx and matplotlib, see the `-DocPy` parameter).
3. Sign the Ethical Compliance Declaration by hand if the institute requires a real signature.

## 5. AI disclosure

Claude (Anthropic) was used as a coding assistant to write and run the pipeline, the API, the tests and the
notebook, to capture the screenshots and to draft the documents. Every number comes from a command run on this
project's files (see `_evidence/` and `BUILD_LOG.md`). The learner is responsible for understanding and explaining
the code and the results.
