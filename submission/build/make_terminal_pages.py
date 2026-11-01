"""Renders the saved console output in _evidence/ as terminal-style HTML pages, so they can be screenshotted.
Run from the project root: .\\.venv\\Scripts\\python.exe -m submission.build.make_terminal_pages"""
import html
from src.config import ROOT

EVIDENCE = ROOT / "_evidence"
OUT = ROOT / "submission" / "figures" / "_term"

PAGES = {   # page name -> evidence files shown one after another, as in one PowerShell window
    "12-console-data-prep-train": ["src.data_prep.txt", "src.train.txt"],
    "13-console-evaluate": ["src.evaluate.txt"],
    "14-console-robustness": ["src.robustness.txt"],
    "15-console-explain": ["src.explain.txt"],
    "16-console-drift": ["src.drift.txt"],
    "17-console-traffic": ["traffic_normal.txt", "traffic_downturn.txt"],
    "18-console-pytest": ["pytest.txt"],
    "19-console-prediction-log": ["sqlite_log.txt"],
}

CSS = """body{margin:0;background:#0c0c0c;font-family:'Cascadia Mono','Consolas',monospace}
.win{display:block;width:1300px;background:#0c0c0c}
.bar{background:#1f1f1f;color:#ccc;font:13px 'Segoe UI',sans-serif;padding:7px 12px}
pre{margin:0;padding:12px 16px 16px;color:#cccccc;font-size:14px;line-height:1.35;white-space:pre-wrap;word-break:break-word}
.cmd{color:#f9f1a5}"""


def page(files: list[str]) -> str:
    lines = []
    for name in files:
        for line in (EVIDENCE / name).read_text(encoding="utf-8").splitlines():
            if line.startswith("PS> "):
                line = line.replace("PS> ", "PS C:\\Users\\worki\\Downloads\\Mobile Devices\\lakshay> ", 1)
                lines.append(f'<span class="cmd">{html.escape(line)}</span>')
            else:
                lines.append(html.escape(line))
        lines.append("")
    return (f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>"
            f"<div class='win' id='term'><div class='bar'>Windows PowerShell</div><pre>{chr(10).join(lines)}</pre></div>")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, files in PAGES.items():
        (OUT / f"{name}.html").write_text(page(files), encoding="utf-8")
    print("written", len(PAGES))
