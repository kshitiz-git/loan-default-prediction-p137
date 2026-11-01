"""Build two short companion documents for P_137 (adapted from the RetailMax build_extras.py):

- <file_prefix>_Output_Screenshots.docx/.pdf: every captured screen with its caption, grouped in the order of
  submission/figures/app/captions.json (list of {file, group, title, caption}).
- <file_prefix>_Source_Code_and_Deployment.docx/.pdf: repository, how to run, folder layout (one A4 page).

Identity, titles, repo URL and dates come from identity.json at run time.

Run:  S:\\retailmax-crm\\.venv\\Scripts\\python.exe submission\\build\\build_extras.py [screenshots|source|all] [--wait MIN]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Inches, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import small_common as C  # noqa: E402

INK = RGBColor(0x1F, 0x29, 0x37)
APP_DIR = C.FIG / "app"
CAPTIONS = APP_DIR / "captions.json"
MAX_PIC_H_IN = 8.3          # keeps a tall screenshot plus its caption on one A4 page


def new_doc(idn: dict, subtitle: str) -> Document:
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(s, side, Cm(2.0))
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Calibri", Pt(11)
    for name, size in (("Heading 1", 16), ("Heading 2", 13)):
        h = doc.styles[name]
        h.font.name, h.font.size, h.font.color.rgb = "Calibri", Pt(size), INK
    p = doc.add_paragraph()
    r = p.add_run(idn["project_title_long"])
    r.bold, r.font.size, r.font.color.rgb = True, Pt(18), INK
    doc.add_paragraph(f"{idn['programme']} | III Year Industry Project | Project No. {idn['project_no']}").runs[0].font.size = Pt(10)
    p = doc.add_paragraph()
    r = p.add_run(subtitle)
    r.bold, r.font.size = True, Pt(13)
    cp = doc.core_properties
    cp.author = cp.last_modified_by = idn["learner_name"]
    cp.title = f"{idn['project_title']}: {subtitle}"
    cp.subject = f"{idn['programme']}, Project No. {idn['project_no']}"
    return doc


def wait_for_captions(minutes: float) -> None:
    deadline = time.time() + minutes * 60
    while not CAPTIONS.exists():
        if time.time() > deadline:
            raise SystemExit(f"captions.json not found at {CAPTIONS}")
        time.sleep(30)


def screenshots(idn: dict) -> Path:
    items = json.loads(CAPTIONS.read_text(encoding="utf-8"))
    groups: dict[str, list[dict]] = {}
    for it in items:                       # dict keeps first-appearance order of the groups
        groups.setdefault(it["group"], []).append(it)

    doc = new_doc(idn, "Output screenshots")
    doc.add_paragraph(
        f"Screens of the working system, captured on {idn['submission_date']} from the FastAPI service running locally "
        "at http://127.0.0.1:8000 (Swagger UI) and from the console runs of the pipeline, 1440 x 900 browser window."
    )
    n = 0
    for group, shots in groups.items():
        doc.add_heading(group, level=2)
        for it in shots:
            n += 1
            path = APP_DIR / Path(it["file"]).name
            doc.add_picture(str(path), width=Inches(6.6))
            pic = doc.inline_shapes[-1]
            if pic.height > Inches(MAX_PIC_H_IN):          # tall console shot: scale down, keep the ratio
                ratio = Inches(MAX_PIC_H_IN) / pic.height
                pic.width, pic.height = int(pic.width * ratio), int(pic.height * ratio)
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap = doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = cap.add_run(f"Screenshot {n}: {it['title']}. ")
            run.bold, run.font.size = True, Pt(9.5)
            cap.add_run(it["caption"]).font.size = Pt(9.5)
    path = C.FINAL / f"{idn['file_prefix']}_Output_Screenshots.docx"
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    print(f"saved {path} ({n} screenshots)")
    return path


def repo_dir_name(idn: dict) -> str:
    url = idn["repo_url"].strip().rstrip("/")
    if url.startswith("http"):
        return url.rsplit("/", 1)[-1].removesuffix(".git") + "/"
    return idn["file_prefix"].lower().replace("_", "-") + "/"


def source_code(idn: dict) -> Path:
    doc = new_doc(idn, "Source code and deployment")
    rows = [
        ("Source code (GitHub)", idn["repo_url"]),
        ("Run locally", "FastAPI + uvicorn on http://127.0.0.1:8000 (Swagger UI at /docs)"),
        ("Hosting", "Local Windows machine; no cloud deployment (out of scope)"),
        ("Model and API", "Python 3.13, scikit-learn 1.8, XGBoost 3.2, SHAP 0.51, FastAPI 0.141, Pydantic 2.13, SQLite"),
        ("Data and analysis", "pandas 3.0, matplotlib, seaborn, Evidently 0.7, Jupyter"),
        ("Server / database", "uvicorn ASGI server; SQLite file logs/predictions.db"),
    ]
    t = doc.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    for k, v in rows:
        c = t.add_row().cells
        c[0].text, c[1].text = k, v
        c[0].paragraphs[0].runs[0].bold = True
        c[0].width, c[1].width = Cm(4.5), Cm(12.5)

    def code(lines: list[str], gap: bool = True) -> None:
        for line in lines:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(line)
            r.font.name, r.font.size = "Consolas", Pt(9.5)
        if gap:
            doc.add_paragraph()

    doc.add_heading("Run the API", level=2)
    doc.add_paragraph("Requires Python 3.11 to 3.14 (3.13 recommended) on Windows. Save the Kaggle CSV as "
                      "data\\raw\\credit_risk_dataset.csv, then start the service and open http://127.0.0.1:8000/docs:")
    code(["py -3.13 -m venv .venv",
          ".\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt",
          ".\\.venv\\Scripts\\python.exe -m uvicorn src.api.main:app --port 8000"])
    doc.add_heading("Rerun the data and model pipeline", level=2)
    doc.add_paragraph("From the project folder, in this order (src.robustness takes about 1 minute):")
    code([".\\.venv\\Scripts\\python.exe -m src.data_prep     # clean + 70/15/15 split",
          ".\\.venv\\Scripts\\python.exe -m src.train         # 3 models, best on validation AUC",
          ".\\.venv\\Scripts\\python.exe -m src.evaluate      # test metrics, bands, NPA back-test",
          ".\\.venv\\Scripts\\python.exe -m src.robustness    # 5-fold CV + ablation",
          ".\\.venv\\Scripts\\python.exe -m src.explain       # SHAP importance + reasons",
          ".\\.venv\\Scripts\\python.exe -m src.drift         # PSI table + Evidently HTML report",
          ".\\.venv\\Scripts\\python.exe -m pytest -q tests   # 13 passed"])
    doc.add_heading("Repository layout", level=2)
    tree = [
        ("src/", "pipeline: data_prep, train, evaluate, robustness, explain, drift"),
        ("    api/", "FastAPI service: schemas.py, store.py (SQLite log), main.py"),
        ("scripts/", "simulate_traffic.py: sends normal and downturn traffic to the API"),
        ("tests/", "13 pytest tests for the data, the model and the API"),
        ("notebooks/", "01_eda.ipynb, the executed EDA notebook"),
        ("data/", "raw Kaggle CSV and the cleaned train/val/test split (git-ignored)"),
        ("models/", "model_v1.joblib and metadata_v1.json (candidates/ is git-ignored)"),
        ("reports/", "evaluation, robustness, SHAP and drift results; charts in eda/"),
        ("logs/", "predictions.db, written by the API (git-ignored)"),
        ("_evidence/", "console output of every pipeline, API and test run"),
        ("submission/", "HCL documents, figures and the scripts that build them"),
    ]
    lines = [repo_dir_name(idn)]
    for name, desc in tree:
        prefix = "│   └── " + name.strip() if name.startswith(" ") else "├── " + name
        lines.append(prefix.ljust(17) + desc)
    lines.append("└── BUILD_LOG.md  README.md  requirements.txt")
    code(lines, gap=False)
    path = C.FINAL / f"{idn['file_prefix']}_Source_Code_and_Deployment.docx"
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    print(f"saved {path}")
    return path


def main(argv: list[str]) -> None:
    idn = C.identity()
    what = next((a for a in argv if a in ("screenshots", "source", "all")), "all")
    wait = float(argv[argv.index("--wait") + 1]) if "--wait" in argv else 0
    jobs = []
    if what in ("source", "all"):
        jobs.append((source_code(idn), C.UPLOAD / f"{idn['file_prefix']}_Source_Code_and_Deployment.pdf", 1))
    if what in ("screenshots", "all"):
        if not CAPTIONS.exists():
            wait_for_captions(wait)
        jobs.append((screenshots(idn), C.UPLOAD / f"{idn['file_prefix']}_Output_Screenshots.pdf", 13))
    for docx, pdf, ref in jobs:
        pages = C.export_pdf(docx, pdf)
        print(f"PDF {pdf} pages={pages} (reference {ref})")


if __name__ == "__main__":
    main(sys.argv[1:])
