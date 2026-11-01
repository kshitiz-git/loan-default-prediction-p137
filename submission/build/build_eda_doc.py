"""Render the EXECUTED notebook notebooks/01_eda.ipynb to a Word document that mirrors the reference EDA PDF.

Format (from the reference): A4, 1.8 cm margins, Calibri 10.5; bold 16 pt title line; 9.5 pt source line;
markdown cells -> paragraphs and headings; code cells -> Consolas 8.5 pt #1F2937, one paragraph per line,
indent 0.4 cm; text outputs -> Consolas 8 pt #374151; charts -> 6.4 in wide pictures.

The notebook runs headless (matplotlib Agg) and writes every chart to reports/eda/ instead of showing it,
so the notebook itself holds no images. A chart is placed after the code cell whose source saves it
(plt.savefig(EDA_DIR / "NN_name.png")), after that cell's text outputs, i.e. in cell order.
The notebook is only read, never modified.

Run:  S:\\retailmax-crm\\.venv\\Scripts\\python.exe submission\\build\\build_eda_doc.py
Output: submission/final/<file_prefix>_EDA_Notebook.docx and UPLOAD/<file_prefix>_EDA_Notebook.pdf
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: F401  (kept for readers extending the script)
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import small_common as C  # noqa: E402

NOTEBOOK = C.ROOT / "notebooks" / "01_eda.ipynb"
EDA_DIR = C.ROOT / "reports" / "eda"
CODE_COLOR = RGBColor(0x1F, 0x29, 0x37)
OUT_COLOR = RGBColor(0x37, 0x41, 0x51)
INDENT = Cm(0.4)                      # 227 twips
TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\*[^*\s][^*]*?\*)")
SAVEFIG = re.compile(r"savefig\(\s*EDA_DIR\s*/\s*[\"']([^\"']+\.png)[\"']")


def mono(par, text: str, size: float, color: RGBColor) -> None:
    r = par.add_run(text)
    r.font.name = "Consolas"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
    r.font.size = Pt(size)
    r.font.color.rgb = color
    pf = par.paragraph_format
    pf.left_indent = INDENT
    pf.space_before = pf.space_after = Pt(0)


def inline(par, text: str, base_size: float | None = None) -> None:
    """Markdown **bold**, *italic*, `code` inside one paragraph."""
    for tok in TOKEN.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            r = par.add_run(tok[2:-2])
            r.bold = True
        elif tok.startswith("`") and tok.endswith("`"):
            r = par.add_run(tok[1:-1])
            r.font.name = "Consolas"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
            r.font.size = Pt(9.5)
            continue
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = par.add_run(tok[1:-1])
            r.italic = True
        else:
            r = par.add_run(tok)
        if base_size:
            r.font.size = Pt(base_size)


def markdown(doc: Document, source: str) -> None:
    lines = source.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        i += 1
        if not ln.strip():
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            doc.add_heading(m.group(2).strip(), level=min(len(m.group(1)), 3))
        elif ln.lstrip().startswith("|"):                       # table: flatten to text lines, like the reference
            rows = [ln]
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(lines[i].rstrip())
                i += 1
            for row in rows:
                if re.match(r"^\|\s*:?-", row):
                    continue
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                inline(doc.add_paragraph(), "    ".join(cells))
        elif re.match(r"^\s*[-*]\s+", ln):
            inline(doc.add_paragraph(style="List Bullet"), re.sub(r"^\s*[-*]\s+", "", ln))
        else:                                                   # numbered items stay typed text, as in the reference
            inline(doc.add_paragraph(), ln.strip())


def text_of(value) -> str:
    return "".join(value) if isinstance(value, list) else str(value)


def main() -> Path:
    idn = C.identity()
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(s, side, Cm(1.8))
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")

    p = doc.add_paragraph()
    r = p.add_run(f"{idn['project_title']}: Exploratory Data Analysis (EDA notebook)")
    r.bold, r.font.size = True, Pt(16)
    p = doc.add_paragraph()
    p.add_run("Source notebook: notebooks/01_eda.ipynb (executed). Code, outputs and charts in cell order.").font.size = Pt(9.5)

    n_charts = n_code = 0
    for cell in nb["cells"]:
        src = text_of(cell.get("source", ""))
        if cell["cell_type"] == "markdown":
            markdown(doc, src)
            continue
        if cell["cell_type"] != "code":
            continue
        n_code += 1
        for line in src.splitlines():
            mono(doc.add_paragraph(), line, 8.5, CODE_COLOR)
        for out in cell.get("outputs", []):
            kind = out["output_type"]
            if kind == "stream":
                text = text_of(out.get("text", ""))
            elif kind in ("execute_result", "display_data") and "text/plain" in out.get("data", {}):
                text = text_of(out["data"]["text/plain"])     # df.head() HTML table -> its monospaced text form
            elif kind == "error":
                text = "\n".join(out.get("traceback", [])) or out.get("ename", "error")
            else:
                continue
            for line in text.rstrip("\n").splitlines():
                mono(doc.add_paragraph(), line, 8, OUT_COLOR)
        for png in SAVEFIG.findall(src):
            path = EDA_DIR / png
            if not path.exists():
                raise FileNotFoundError(path)
            doc.add_paragraph().add_run().add_picture(str(path), width=Inches(6.4))
            n_charts += 1
        doc.add_paragraph()                                    # blank paragraph between cells

    cp = doc.core_properties
    cp.author = cp.last_modified_by = idn["learner_name"]
    cp.title = f"{idn['project_title']}: EDA notebook"
    cp.subject = f"{idn['programme']}, Project No. {idn['project_no']}"

    out = C.FINAL / f"{idn['file_prefix']}_EDA_Notebook.docx"
    pdf = C.UPLOAD / f"{idn['file_prefix']}_EDA_Notebook.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    print(f"saved {out} ({n_code} code cells, {n_charts} charts)")
    pages = C.export_pdf(out, pdf)
    print(f"PDF {pdf} pages={pages} (reference 14)")
    return pdf


if __name__ == "__main__":
    main()
