# Shared brief for every document-builder agent (P_137 submission)

## Goal
Produce a student submission for project P_137 "Loan Default Prediction System" whose deliverables match, file for file
and section for section, the reference submission in `S:\retailmax-crm\submission\final\UPLOAD` (a different project,
"RetailMax CRM"). Same page sizes, fonts, colours, heading structure, cover fields, table styles, caption styles,
header/footer, and roughly the same page budget, but with OUR project's content and OUR real numbers.

## Read first
1. Format spec of the reference (exact headings, styles, page budget): 
   `C:\Users\worki\AppData\Local\Temp\claude\C--Users-worki-Downloads-Mobile-Devices\71037cbd-0d84-4abe-95f8-1c64f2af350c\scratchpad\reference_format.md`
2. Reference generator scripts to ADAPT (copy into our folder and change; never modify the originals):
   `S:\retailmax-crm\docs\build\` (build_report_docx.py, build_srs.py, build_extras.py, fill_synopsis.py,
   build_declaration.py, make_diagrams.py). Reference markdown sources: `S:\retailmax-crm\docs\PROJECT_REPORT.md`,
   `S:\retailmax-crm\docs\SYNOPSIS.md`. Reference PDFs/DOCX: `S:\retailmax-crm\submission\final\`.
3. Our project (root `C:\Users\worki\Downloads\Mobile Devices\lakshay`, call it ROOT):
   - `ROOT\README.md`, `ROOT\BUILD_LOG.md`: every result, in plain words. THE source of numbers.
   - `ROOT\reports\evaluation.json`, `robustness.json`, `shap_importance.json`, `drift_summary.csv`, `ROOT\models\metadata_v1.json`
   - `ROOT\_evidence\*.txt`: real console output of every command (pipeline, live API checks, kill switch, pytest).
   - Code: `ROOT\src\*.py`, `ROOT\src\api\*.py`, `ROOT\scripts\simulate_traffic.py`, `ROOT\tests\*.py`, `ROOT\notebooks\01_eda.ipynb` (executed).
   - Charts: `ROOT\reports\eda\01..06_*.png`, `ROOT\reports\roc_curves.png`, `npa_vs_approval.png`, `shap_importance_bar.png`, `shap_beeswarm.png`.
   - Diagrams (made by the diagrams agent, may appear while you work): `ROOT\submission\figures\arch\dfd_level0.png`, `dfd_level1.png`, `block_diagram.png`; `ROOT\submission\figures\srs\use_case.png`, `er_diagram.png`, `sequence_predict.png`.
   - App screenshots (made by the main session, may appear while you work): `ROOT\submission\figures\app\NN-*.png` with
     titles + captions in `ROOT\submission\figures\app\captions.json` (list of {file, group, title, caption}). Build the
     final docx only after captions.json exists; poll for it (sleep 30 s between checks, up to 40 min) if it is missing.
4. Student identity: `ROOT\submission\build\identity.json`. ALWAYS read identity, project title/number, programme line,
   repo URL and dates from this file at build time; never hard-code them. Some values are placeholders in square
   brackets (e.g. "[ROLL NUMBER]") because the learner has not supplied them yet: print them as they are. The learner
   will fill the JSON and the main session will re-run your script, so the script must be re-runnable.

## Facts about P_137 that are fixed
- Dataset: Kaggle "Credit Risk Dataset" by laotse (public), 32,581 rows x 12 columns raw; 32,409 after cleaning;
  21.8% default raw. No personal identifiers (no names, ids, addresses). The data are simulated credit-bureau records.
- System: Python pipeline (pandas, scikit-learn, XGBoost) -> SHAP reasons -> FastAPI scoring API (`/health`,
  `/model/info`, `POST /predict`, `/monitoring/drift`, Swagger at `/docs`) -> SQLite prediction log -> PSI drift
  monitoring + Evidently HTML report; kill switch env var `SCORING_DISABLED=1`. Runs locally on Windows; no cloud,
  no web front end (Swagger UI is the demo), no login. 13 pytest tests pass.
- Decision policy: APPROVE PD < 0.20, REVIEW 0.20-0.50, REJECT PD >= 0.50.
- XGBoost numbers differ from the spec's reference build by < 0.001 AUC because XGBoost's result depends on CPU
  thread count (measured; see BUILD_LOG.md). Use OUR numbers (BUILD_LOG.md / evaluation.json), never the spec's.
- AI disclosure: Claude (Anthropic) was used as a coding assistant to write and run the pipeline, API, tests and to
  draft the documents; the learner is responsible for understanding and explaining them.
- Ethics angle for P_137 (replaces RetailMax's DPDP consent/loyalty content): public licensed dataset, no PII,
  explainable adverse-action reasons, human REVIEW band and kill switch, prediction log for audit, drift monitoring,
  RBI Fair Practices Code (reasons for rejection), DPDP Act 2023 for a real deployment, no fairness audit yet (limitation).

## Rules
- Every number you write must come from the files above. If you need a number that is not there, compute it with
  `ROOT\.venv\Scripts\python.exe` from ROOT (read-only use) or write "not measured". Never invent numbers, references
  with fake details, or features the system does not have.
- Python for building documents: `S:\retailmax-crm\.venv\Scripts\python.exe` (has python-docx 1.2, matplotlib 3.11,
  pandas, Pillow). Use it read-only; do not pip install anything anywhere.
- Write only inside `ROOT\submission\` (your builder scripts in `ROOT\submission\build\`, your markdown sources in
  `ROOT\submission\docs\`, docx output in `ROOT\submission\final\`). Never edit ROOT\src, tests, models, reports,
  notebooks, README.md, BUILD_LOG.md, or anything under S:\retailmax-crm.
- PDF: export with `powershell -NoProfile -ExecutionPolicy Bypass -File ROOT\submission\build\export_pdf.ps1 -Docx <abs docx> -Pdf <abs pdf>`
  (prints PAGES=N). Word may be busy with another agent's export: on failure wait 20 s and retry, up to 5 times.
  Put PDFs in `ROOT\submission\final\UPLOAD\`. Open the PDF text (pypdf via `py -3.13 -I`) to check there is no
  leftover RetailMax / Kshitiz / kshitiz-git / "Project No. 27" text, and no `[FILL IN`.
- English, plain and direct. No marketing words (no "robust", "seamless", "leverage", "comprehensive", "cutting-edge").
- File encoding UTF-8 for every text file you read or write.
- Final reply to the main session: file paths created, page count of each PDF vs the reference's page count, and a
  list of anything you could not do or any number you could not source.
