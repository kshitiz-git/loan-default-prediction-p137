"""Shared helpers for the small-document builders (declaration, synopsis, EDA, screenshots, source code).

Reads identity.json at run time, builds the file-name tag, and exports docx -> PDF through Word.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ROOT = BUILD.parents[1]
FINAL = ROOT / "submission" / "final"
UPLOAD = FINAL / "UPLOAD"
FIG = ROOT / "submission" / "figures"
DOCS = ROOT / "submission" / "docs"
EXPORT_PS1 = BUILD / "export_pdf.ps1"


def identity() -> dict:
    return json.loads((BUILD / "identity.json").read_text(encoding="utf-8"))


def tag(idn: dict | None = None) -> str:
    idn = idn or identity()
    return idn["learner_name"].replace(" ", "") + "_" + re.sub(r"[^A-Za-z0-9]", "", idn["roll_number"])


def export_pdf(docx: Path, pdf: Path, tries: int = 5) -> int:
    """Word COM export via export_pdf.ps1. Returns the page count Word reports."""
    pdf.parent.mkdir(parents=True, exist_ok=True)
    last = ""
    for i in range(tries):
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(EXPORT_PS1),
             "-Docx", str(docx), "-Pdf", str(pdf)],
            capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"PAGES=(\d+)", out)
        if r.returncode == 0 and m and pdf.exists():
            return int(m.group(1))
        last = out.strip()
        time.sleep(20)
    raise RuntimeError(f"PDF export failed after {tries} tries: {last[:500]}")
