"""Fill HCL's Project_Synopsis_Template.docx for P_137 (adapted from the RetailMax fill_synopsis.py).

Content comes from submission/docs/SYNOPSIS.md (section by section, parsed so the numbers are never retyped).
Identity (name, roll number, college, mentor, date, repository URL, project title/number) comes from identity.json.
The template is copied, never modified. HCL's formatting (Arial, purple Heading 2, header table, last line) is kept;
only the orange italic instruction paragraphs are replaced.

Run:  S:\\retailmax-crm\\.venv\\Scripts\\python.exe submission\\build\\fill_synopsis.py [--fig-dir DIR]
Output: submission/final/Project_Synopsis_<tag>.docx and UPLOAD/Project_Synopsis_<tag>.pdf (4 pages, US Letter)
Needs submission/figures/arch/dfd_level0.png and block_diagram.png (diagrams agent).
"""
from __future__ import annotations

import copy
import re
import shutil
import sys
import time
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.text.paragraph import Paragraph
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import small_common as C  # noqa: E402

TEMPLATE_LOCAL = C.BUILD / "Project_Synopsis_Template.docx"            # copy of HCL's template
TEMPLATE_SRC = Path(r"S:\retailmax-crm\docs\hcl\Project_Synopsis_Template.docx")
SYNOPSIS_MD = C.DOCS / "SYNOPSIS.md"
JMLR_URL = "https://jmlr.org/papers/v12/pedregosa11a.html"
DEMO_LINE = "Runs locally; demo through Swagger UI at http://127.0.0.1:8000/docs"

FONT = "Arial"
SIZE = 10
MAX_FIG_H_IN = 3.9            # keeps both figures and captions on one US Letter page


# --------------------------------------------------------------------------- markdown source
def read_sections() -> dict[str, list[str]]:
    """Split SYNOPSIS.md into {heading text: lines}. The leading block is stored under ''."""
    sections: dict[str, list[str]] = {"": []}
    cur = ""
    in_code = False
    for line in SYNOPSIS_MD.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.startswith("## "):
            cur = line[3:].strip()
            sections[cur] = []
        else:
            sections[cur].append(line)
    return sections


def paragraphs_of(lines: list[str]) -> list[str]:
    """Blank-line separated prose paragraphs, dropping the [FILL IN ...] note lines."""
    out, buf = [], []
    for ln in lines + [""]:
        if ln.lstrip().startswith("|"):
            continue  # markdown table rows are handled by table_rows()
        if ln.strip():
            buf.append(ln.strip())
        elif buf:
            out.append(" ".join(buf))
            buf = []
    return [p for p in out if not p.startswith("*[FILL IN")]


def table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for ln in lines:
        if ln.startswith("|") and not re.match(r"^\|\s*-", ln):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows.append(cells)
    return rows[1:]  # drop the header row


def bullets_of(lines: list[str]) -> list[str]:
    return [ln[2:].strip() for ln in lines if ln.startswith("- ")]


def numbered_of(lines: list[str]) -> list[str]:
    return [re.sub(r"^\d+\.\s*", "", ln).strip() for ln in lines if re.match(r"^\d+\.\s", ln)]


# --------------------------------------------------------------------------- docx helpers
def style_run(run, bold=False, italic=False, size=SIZE, color: str | None = None, font=FONT):
    run.font.name = font
    run.font.size = Pt(size)
    if bold:
        run.bold = True
    if italic:
        run.italic = True
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\*[^*]+?\*)")


def rich(par: Paragraph, text: str, size=SIZE, base_bold=False, base_italic=False):
    """Add text to a paragraph, honouring **bold**, *italic* and `code` from the markdown source."""
    for tok in TOKEN.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            style_run(par.add_run(tok[2:-2]), bold=True, italic=base_italic, size=size)
        elif tok.startswith("`") and tok.endswith("`"):
            style_run(par.add_run(tok[1:-1]), bold=base_bold, italic=base_italic, size=size)
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            style_run(par.add_run(tok[1:-1]), bold=base_bold, italic=True, size=size)
        else:
            style_run(par.add_run(tok), bold=base_bold, italic=base_italic, size=size)


def add_hyperlink(par: Paragraph, url: str, text: str | None = None, size=SIZE):
    r_id = par.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), FONT)
    fonts.set(qn("w:hAnsi"), FONT)
    rpr.append(fonts)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    rpr.append(color)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(size * 2))
    rpr.append(sz)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rpr.append(u)
    run.append(rpr)
    t = OxmlElement("w:t")
    t.text = text or url
    run.append(t)
    link.append(run)
    par._p.append(link)


class Section:
    """Fills the template's instruction paragraph, then inserts further paragraphs after it."""

    def __init__(self, heading: Paragraph):
        nxt = heading._p.getnext()
        assert nxt is not None and nxt.tag == qn("w:p"), "expected the instruction paragraph after the heading"
        self.cur = Paragraph(nxt, heading._parent)
        for r in self.cur._p.findall(qn("w:r")):
            self.cur._p.remove(r)
        self.used = False

    def para(self, after=4, hanging: float | None = None, keep_next=False, align=None, before=0) -> Paragraph:
        if not self.used:
            p = self.cur
            self.used = True
        else:
            new = OxmlElement("w:p")
            self.cur._p.addnext(new)
            p = Paragraph(new, self.cur._parent)
            self.cur = p
        pf = p.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.keep_with_next = keep_next or None
        if hanging:
            pf.left_indent = Inches(hanging)
            pf.first_line_indent = Inches(-hanging)
            pf.tab_stops.add_tab_stop(Inches(hanging))
        if align is not None:
            p.alignment = align
        return p

    def finish(self):
        self.cur.paragraph_format.space_after = Pt(8)


def find_heading(doc: Document, prefix: str) -> Paragraph:
    for p in doc.paragraphs:
        if p.style.name == "Heading 2" and p.text.startswith(prefix):
            return p
    raise KeyError(prefix)


def set_cell_text(cell, text: str) -> None:
    """Replace the text of a template cell, keeping its first run's formatting."""
    par = cell.paragraphs[0]
    runs = par.runs
    runs[0].text = text
    for extra in runs[1:]:
        extra._r.getparent().remove(extra._r)


def fill_header_table(doc: Document, idn: dict) -> None:
    """Template table has 12 rows; the reference adds Admission Number and Department / Class (14 rows)."""
    table = doc.tables[0]
    values = {
        "Project Title": idn["project_title_long"], "Project No.": idn["project_no"], "Domain": idn["domain"],
        "Difficulty": idn["difficulty"], "Duration": idn["duration"], "Format": idn["format"],
        "Learner Name": idn["learner_name"], "Roll Number": idn["roll_number"],
        "College / Campus": idn["college"], "Mentor Name": idn["mentor"], "Submission Date": idn["submission_date"],
    }
    roll_row = next(r for r in table.rows if r.cells[0].text.strip() == "Roll Number")
    anchor = roll_row._tr
    for label, value in (("Admission Number", idn["admission_number"]), ("Department / Class", idn["department_class"])):
        new = copy.deepcopy(roll_row._tr)
        anchor.addnext(new)
        anchor = new
        values[label] = value
    order = ["Project Title", "Project No.", "Domain", "Difficulty", "Duration", "Format", "Learner Name",
             "Roll Number", "Admission Number", "Department / Class", "College / Campus", "Mentor Name", "Submission Date"]
    assert len(table.rows) == 14, len(table.rows)
    for row, label in zip(table.rows[1:], order):
        set_cell_text(row.cells[0], label)
        set_cell_text(row.cells[1], values[label])


# --------------------------------------------------------------------------- build
def main(fig_dir: Path | None = None) -> Path:
    idn = C.identity()
    tag = C.tag(idn)
    fig_dir = fig_dir or (C.FIG / "arch")
    out = C.FINAL / f"Project_Synopsis_{tag}.docx"
    pdf = C.UPLOAD / f"Project_Synopsis_{tag}.pdf"
    template = TEMPLATE_LOCAL if TEMPLATE_LOCAL.exists() else TEMPLATE_SRC

    secs = read_sections()
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, out)
    doc = Document(out)

    # ---- header table (14 rows)
    fill_header_table(doc, idn)

    # ---- 1. Problem statement (5W1H, one paragraph per W, text verbatim from SYNOPSIS.md)
    s = Section(find_heading(doc, "1. Problem Statement"))
    text = " ".join(paragraphs_of(secs["1. Problem Statement"]))
    parts = re.split(r"(?=\*\*(?:Who|What|When / where|Why it matters|How):\*\*)", text)
    for part in [p.strip() for p in parts if p.strip()]:
        rich(s.para(after=3), part)
    s.finish()

    # ---- 2. Proposed solution
    s = Section(find_heading(doc, "2. Proposed Solution"))
    for ptxt in paragraphs_of(secs["2. Proposed Solution and Approach"]):
        rich(s.para(after=6), ptxt)
    p = s.para(after=2)
    style_run(p.add_run("Demo: "), bold=True)
    style_run(p.add_run(DEMO_LINE))
    p = s.para(after=2)
    style_run(p.add_run("GitHub repository: "), bold=True)
    if idn["repo_url"].startswith("http"):
        add_hyperlink(p, idn["repo_url"])
    else:
        style_run(p.add_run(idn["repo_url"]))
    s.finish()

    # ---- 3. System architecture (two figures)
    s = Section(find_heading(doc, "3. System Architecture"))

    def figure(path: Path, width_in: float, caption: str):
        with Image.open(path) as im:
            w, h = im.size
        width_in = min(width_in, MAX_FIG_H_IN * w / h)
        p = s.para(after=2, keep_next=True, align=WD_ALIGN_PARAGRAPH.CENTER, before=4)
        p.add_run().add_picture(str(path), width=Inches(width_in))
        c = s.para(after=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        style_run(c.add_run(caption), italic=True, size=9, color="404040")

    figure(fig_dir / "dfd_level0.png", 5.6,
           f"Figure 1: Data flow diagram, level 0 ({idn['project_title']} and its external entities).")
    figure(fig_dir / "block_diagram.png", 5.9,
           "Figure 2: System block diagram (offline Python pipeline and the FastAPI scoring service).")
    s.finish()

    # ---- 4. Technology stack (label, tab, value; wrapped lines align under the value)
    s = Section(find_heading(doc, "4. Technology Stack"))
    rows4 = table_rows(secs["4. Technology Stack"])
    for i, (layer, tech) in enumerate(rows4):
        p = s.para(after=3, hanging=1.55, keep_next=i < len(rows4) - 1)   # keep the block on one page
        style_run(p.add_run(layer + ":\t"), bold=True)
        rich(p, tech)
    s.finish()

    # ---- 5. Dataset used
    s = Section(find_heading(doc, "5. Dataset Used"))
    labels = {"Key columns": "Key columns (list 5)", "Any additional data collected": "Any additional data collected"}
    for item, detail in table_rows(secs["5. Dataset Used"]):
        p = s.para(after=3, hanging=2.1)
        style_run(p.add_run(labels.get(item, item) + ":\t"), bold=True)
        rich(p, detail)
    for ptxt in paragraphs_of(secs["5. Dataset Used"]):
        rich(s.para(after=3, before=3), ptxt)
    s.finish()

    # ---- 6. Key results and metrics
    s = Section(find_heading(doc, "6. Key Results"))
    lines = secs["6. Key Results and Metrics"]
    for ptxt in paragraphs_of([ln for ln in lines if not ln.startswith("- ")]):
        rich(s.para(after=4), ptxt, base_italic=False)
    for b in bullets_of(lines):
        rich(s.para(after=3), b)
    s.finish()

    # ---- 7. Challenges
    s = Section(find_heading(doc, "7. Challenges"))
    for b in bullets_of(secs["7. Challenges Faced and How Resolved"]):
        m = re.match(r"\*\*(Challenge \d+):\*\*\s*(.*?)\s*\*\*Resolution:\*\*\s*(.*)$", b)
        assert m, b
        p = s.para(after=5)
        style_run(p.add_run(m.group(1) + ": "), bold=True)
        rich(p, m.group(2))
        p.add_run().add_break()
        style_run(p.add_run("\u2192 Resolution: "), bold=True)
        rich(p, m.group(3))
    s.finish()

    # ---- 8. References
    s = Section(find_heading(doc, "8. References"))
    for i, ref in enumerate(numbered_of(secs["8. References"]), 1):
        p = s.para(after=3, hanging=0.3)
        style_run(p.add_run(f"{i}.\t"))
        rich(p, ref)
        if "Scikit-learn" in ref:
            p.add_run(" ")
            add_hyperlink(p, JMLR_URL)
    s.finish()

    # ---- 9. Ethical compliance declaration: tick the four boxes, disclose the AI tool, type the signature
    decl = doc.paragraphs[[q.text.startswith("I confirm that:") for q in doc.paragraphs].index(True)]
    ticked = signed = 0
    for t in decl._p.iter(qn("w:t")):
        if "\u2610" in t.text:
            t.text = t.text.replace("\u2610", "\u2611")
            ticked += 1
        if t.text.strip().startswith("\u2611  AI tools used"):
            t.text = t.text.rstrip().rstrip(".") + " (Claude by Anthropic)."
        if t.text.startswith("Learner Signature:"):
            t.text = f"Learner Signature: {idn['learner_name']}    Date: {idn['submission_date']}"
            signed += 1
    assert ticked == 4 and signed == 1, (ticked, signed)

    cp = doc.core_properties
    cp.author = cp.last_modified_by = idn["learner_name"]
    cp.title = f"{idn['project_title']}: Project Synopsis"
    cp.subject = f"{idn['programme']}, Project No. {idn['project_no']}"

    doc.save(out)
    print("saved", out)
    pages = C.export_pdf(out, pdf)
    print(f"PDF {pdf} pages={pages} (reference 4)")
    return pdf


if __name__ == "__main__":
    args = sys.argv[1:]
    fd = Path(args[args.index("--fig-dir") + 1]) if "--fig-dir" in args else None
    if fd is None:                       # wait up to 40 min for the diagrams agent
        need = [C.FIG / "arch" / "dfd_level0.png", C.FIG / "arch" / "block_diagram.png"]
        t_end = time.time() + 40 * 60 if "--wait" in args else 0
        while not all(p.exists() for p in need):
            if time.time() > t_end:
                raise SystemExit("missing: " + ", ".join(str(p) for p in need if not p.exists()))
            time.sleep(30)
    main(fd)
