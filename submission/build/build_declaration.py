"""Build the one-page Ethical Compliance Declaration for P_137 (adapted from the RetailMax builder).

Identity, project title/number, programme and date are read from identity.json at run time.
Output: submission/final/Ethical_Compliance_Declaration_<tag>.docx and UPLOAD/...pdf

Run:  S:\\retailmax-crm\\.venv\\Scripts\\python.exe submission\\build\\build_declaration.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import small_common as C  # noqa: E402

FONT = "Calibri"
INK = RGBColor(0x1F, 0x1F, 0x1F)
ACCENT = RGBColor(0x3D, 0x1A, 0x6E)
GREY = RGBColor(0x55, 0x55, 0x55)

STATEMENTS = [
    (
        "All dataset usage complies with the source licence.",
        [
            "The only data is the public Kaggle \u201cCredit Risk Dataset\u201d by laotse. It is used unchanged in "
            "data/raw/credit_risk_dataset.csv; cleaning writes new files to data/processed/ and never edits the original.",
            "No other data was collected, scraped or bought. The records are simulated credit-bureau data, "
            "not a real lender\u2019s customers.",
        ],
    ),
    (
        "No personally identifiable information (PII) is stored without consent.",
        [
            "The 12 columns hold no names, ids, addresses, phone numbers or email. Only age, income, employment "
            "length, home ownership and the loan and credit-history fields are present.",
            "The API logs only the application fields it scores, plus the score, decision and timing, to a local "
            "SQLite file (logs/predictions.db). Nothing is sent to another server.",
        ],
    ),
    (
        "AI tools used for code/writing are disclosed in the Appendix.",
        [
            "Claude (Anthropic) was used as a coding assistant to write and run the Python pipeline, the API, the "
            "tests and the EDA notebook, and to draft the report, the synopsis and the README.",
            "Every number in the documents comes from a command run on this project\u2019s files (BUILD_LOG.md and "
            "_evidence/). The learner is responsible for understanding and explaining the code and the results.",
        ],
    ),
    (
        "This project complies with the DPDP Act 2023 where applicable.",
        [
            "The prototype collects no personal data: the training file has no identifiers and the API logs only the "
            "application fields it scores.",
            "A real deployment would need a notice and consent before scoring a person, purpose limitation (credit "
            "decision only), a retention period for the log and erasure on request. None of these is built here.",
            "RBI Fair Practices Code: a rejected applicant is owed the reasons. The API returns up to three SHAP-based "
            "plain-language reasons; the REVIEW band (PD 0.20 to 0.50) and the kill switch (SCORING_DISABLED=1) keep a person in the loop.",
        ],
    ),
]


def run(par, text, bold=False, italic=False, size=11, color=INK, font=FONT):
    r = par.add_run(text)
    r.font.name = font
    r._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    r.font.size = Pt(size)
    r.bold = bold or None
    r.italic = italic or None
    r.font.color.rgb = color
    return r


def fmt(par, before=0, after=0, left=None, first=None, align=None, line=1.08, keep_next=False):
    pf = par.paragraph_format
    pf.space_before, pf.space_after, pf.line_spacing = Pt(before), Pt(after), line
    if left is not None:
        pf.left_indent = Cm(left)
    if first is not None:
        pf.first_line_indent = Cm(first)
    if align is not None:
        par.alignment = align
    if keep_next:
        pf.keep_with_next = True


def bottom_rule(par, color="3D1A6E", size=12):
    ppr = par._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", str(size)), ("w:space", "4"), ("w:color", color)):
        b.set(qn(k), v)
    borders.append(b)
    ppr.append(borders)


def shade(cell, fill="ECE6F5"):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(shd)


def main() -> Path:
    idn = C.identity()
    tag = C.tag(idn)
    out = C.FINAL / f"Ethical_Compliance_Declaration_{tag}.docx"
    pdf = C.UPLOAD / f"Ethical_Compliance_Declaration_{tag}.pdf"

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin, sec.bottom_margin = Cm(1.6), Cm(1.4)

    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(11)

    # ---- heading block
    p = doc.add_paragraph()
    fmt(p, after=2, align=WD_ALIGN_PARAGRAPH.CENTER)
    run(p, "Ethical Compliance Declaration", bold=True, size=22, color=ACCENT)
    p = doc.add_paragraph()
    fmt(p, after=6, align=WD_ALIGN_PARAGRAPH.CENTER)
    run(p, idn["programme_line"], italic=True, size=10.5, color=GREY)
    bottom_rule(p)

    p = doc.add_paragraph()
    fmt(p, before=4, after=1)
    run(p, "Project title: ", bold=True)
    run(p, idn["project_title_long"])
    p = doc.add_paragraph()
    fmt(p, after=6)
    run(p, "Project No.: ", bold=True)
    run(p, idn["project_no"])

    # ---- learner fields (2 rows x 4 columns)
    rows = [
        [("Learner Name", True), (idn["learner_name"], False), ("Roll Number", True), (idn["roll_number"], False)],
        [("Admission Number", True), (idn["admission_number"], False), ("Department / Class", True),
         (idn["department_class_short"], False)],
    ]
    t = doc.add_table(rows=2, cols=4)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Cm(3.9), Cm(4.9), Cm(3.9), Cm(4.3)]
    for row, spec in zip(t.rows, rows):
        for cell, w, (txt, is_label) in zip(row.cells, widths, spec):
            cell.width = w
            cp = cell.paragraphs[0]
            fmt(cp, before=2, after=2)
            run(cp, txt, bold=is_label, size=10.5)
            if is_label:
                shade(cell)

    # ---- statements
    p = doc.add_paragraph()
    fmt(p, before=9, after=3, keep_next=True)
    run(p, "I confirm that:", bold=True, size=11.5)

    for stmt, lines in STATEMENTS:
        p = doc.add_paragraph()
        fmt(p, before=3, after=1, left=0.75, first=-0.75, keep_next=True)
        run(p, "\u2611", size=12, font="Segoe UI Symbol")
        run(p, "\t" + stmt, bold=True, size=11)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(0.75))
        for ln in lines:
            b = doc.add_paragraph()
            fmt(b, after=1, left=1.4, first=-0.4, line=1.05)
            b.paragraph_format.tab_stops.add_tab_stop(Cm(1.4))
            run(b, "\u2013\t", size=9.5, color=GREY)
            run(b, ln, size=10)

    p = doc.add_paragraph()
    fmt(p, before=6, after=0, line=1.05)
    run(p, "Scope note: ", bold=True, size=9.5, color=GREY)
    run(p, "this is a prototype. A real deployment would also need a privacy notice and consent before scoring, "
           "a log retention and erasure rule, access control on the API and a fairness audit across age and other "
           "groups (see the limitations in the README and the project report).",
        italic=True, size=9.5, color=GREY)

    # ---- signature block (typed name and date)
    p = doc.add_paragraph()
    fmt(p, before=38, after=0)
    run(p, "Learner Signature: ", bold=True)
    run(p, idn["learner_name"] + "      ")
    run(p, "Date: ", bold=True)
    run(p, idn["submission_date"])

    p = doc.add_paragraph()
    fmt(p, before=14, after=0, align=WD_ALIGN_PARAGRAPH.CENTER)
    run(p, f"{idn['programme']} 2025-26  |  {idn['project_title']}, Project No. {idn['project_no']}",
        italic=True, size=8.5, color=GREY)

    cp = doc.core_properties
    cp.author = cp.last_modified_by = idn["learner_name"]
    cp.title = f"{idn['project_title']}: Ethical Compliance Declaration"
    cp.subject = f"{idn['programme']}, Project No. {idn['project_no']}"

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    print("saved", out)
    pages = C.export_pdf(out, pdf)
    print(f"PDF {pdf} pages={pages}")
    return pdf


if __name__ == "__main__":
    main()
