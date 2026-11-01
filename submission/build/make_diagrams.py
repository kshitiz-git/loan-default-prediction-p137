"""Draw the six diagrams of the P_137 submission (Loan Default Prediction System) as PNG files.

Style and helper classes are copied from the RetailMax CRM reference build
(S:\\retailmax-crm\\docs\\build\\make_diagrams.py and build_srs.py): matplotlib only, Arial with a
DejaVu Sans fallback, entity fill #F2F2F2 / edge #444444, process fill #EDE3F7 / edge #5B2A86,
data store fill #FFF6DC / edge #8A6A00, ink #222222, 200 dpi, automatic text-overlap check.

Every box and arrow comes from our code: src/*.py, src/api/*.py, scripts/simulate_traffic.py.

Run:  S:\\retailmax-crm\\.venv\\Scripts\\python.exe -I submission\\build\\make_diagrams.py [l0 l1 block uc er seq]
Output: submission/figures/arch/dfd_level0.png, dfd_level1.png, block_diagram.png
        submission/figures/srs/use_case.png, er_diagram.png, sequence_predict.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Rectangle

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT_ARCH = ROOT / "submission" / "figures" / "arch"
OUT_SRS = ROOT / "submission" / "figures" / "srs"
DPI = 200

_names = {f.name for f in font_manager.fontManager.ttflist}
FONT = "Arial" if "Arial" in _names else "DejaVu Sans"
plt.rcParams["font.family"] = FONT

INK = "#222222"
LINE = "#333333"
ENT_FILL, ENT_EDGE = "#F2F2F2", "#444444"
PROC_FILL, PROC_EDGE = "#EDE3F7", "#5B2A86"
STORE_FILL, STORE_EDGE = "#FFF6DC", "#8A6A00"
GROUP_EDGE = "#7A7A7A"
HEAD_GREY = "#666666"
GREY = "#6B6B6B"


# ====================================================================================
#  Diagram class (DFD and block diagram) - copied from the reference make_diagrams.py
# ====================================================================================
class Diagram:
    def __init__(self, width: float, height: float):
        self.w, self.h = width, height
        self.fig = plt.figure(figsize=(width, height), dpi=DPI, facecolor="white")
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.boxes: list[tuple[str, tuple[float, float, float, float]]] = []
        self.node_texts: list[tuple[str, object, str]] = []
        self.label_texts: list[tuple[str, object]] = []
        self.segments: list[tuple[str, tuple[float, float], tuple[float, float]]] = []
        self.circles: dict[str, tuple[float, float, float]] = {}

    # ------------------------------------------------------------------ nodes
    def _text_block(self, owner, cx, cy, lines, box):
        """lines: list of (text, size, weight, style, colour). Stacked and centred on (cx, cy)."""
        gaps = [s / 72 * 1.28 for (_, s, *_rest) in lines]
        total = sum(gaps)
        y = cy + total / 2
        for (txt, size, weight, style, colour), g in zip(lines, gaps):
            y -= g / 2
            t = self.ax.text(cx, y, txt, ha="center", va="center", fontsize=size,
                             fontweight=weight, fontstyle=style, color=colour, zorder=6)
            self.node_texts.append((owner, t, box))
            y -= g / 2

    def entity(self, name, cx, cy, w, h, lines):
        x0, y0 = cx - w / 2, cy - h / 2
        self.ax.add_patch(Rectangle((x0, y0), w, h, fc=ENT_FILL, ec=ENT_EDGE, lw=1.8, zorder=3))
        self.boxes.append((name, (x0, y0, x0 + w, y0 + h)))
        self._text_block(name, cx, cy, lines, (x0, y0, x0 + w, y0 + h))

    def process_box(self, name, cx, cy, w, h, lines):
        x0, y0 = cx - w / 2, cy - h / 2
        self.ax.add_patch(FancyBboxPatch((x0 + 0.08, y0 + 0.08), w - 0.16, h - 0.16,
                                         boxstyle="round,pad=0.08,rounding_size=0.18",
                                         fc=PROC_FILL, ec=PROC_EDGE, lw=1.8, zorder=3))
        self.boxes.append((name, (x0, y0, x0 + w, y0 + h)))
        self._text_block(name, cx, cy, lines, (x0, y0, x0 + w, y0 + h))

    def process_circle(self, name, cx, cy, r, lines):
        self.ax.add_patch(Circle((cx, cy), r, fc=PROC_FILL, ec=PROC_EDGE, lw=2.2, zorder=3))
        self.boxes.append((name, (cx - r, cy - r, cx + r, cy + r)))
        self.circles[name] = (cx, cy, r)
        self._text_block(name, cx, cy, lines, (cx - r * 0.82, cy - r * 0.82, cx + r * 0.82, cy + r * 0.82))

    def store(self, name, cx, cy, w, h, ident, lines, id_w=0.55):
        """Open-ended data store: closed on the left, open on the right, ID cell on the left."""
        x0, y0 = cx - w / 2, cy - h / 2
        x1, y1 = x0 + w, y0 + h
        self.ax.add_patch(Rectangle((x0, y0), w, h, fc=STORE_FILL, ec="none", zorder=3))
        for (a, b, c, d) in [(x0, y1, x1, y1), (x0, y0, x1, y0), (x0, y0, x0, y1), (x0 + id_w, y0, x0 + id_w, y1)]:
            self.ax.plot([a, c], [b, d], color=STORE_EDGE, lw=1.8, solid_capstyle="butt", zorder=4)
        self.boxes.append((name, (x0, y0, x1, y1)))
        self._text_block(name + ".id", x0 + id_w / 2, cy, [(ident, 11, "bold", "normal", INK)],
                         (x0, y0, x0 + id_w, y1))
        self._text_block(name, x0 + id_w + (w - id_w) / 2, cy, lines, (x0 + id_w, y0, x1, y1))

    def cylinder(self, name, cx, cy, w, h, lines):
        x0, y0 = cx - w / 2, cy - h / 2
        cap = 0.17
        t = np.linspace(np.pi, 2 * np.pi, 60)
        bx, by = cx + (w / 2) * np.cos(t), (y0 + cap) + cap * np.sin(t)
        poly = np.column_stack([np.r_[x0, bx, x0 + w], np.r_[y0 + h - cap, by, y0 + h - cap]])
        self.ax.add_patch(plt.Polygon(poly, closed=True, fc=STORE_FILL, ec="none", zorder=3))
        self.ax.plot(bx, by, color=STORE_EDGE, lw=1.8, zorder=4)
        self.ax.plot([x0, x0], [y0 + cap, y0 + h - cap], color=STORE_EDGE, lw=1.8, zorder=4)
        self.ax.plot([x0 + w, x0 + w], [y0 + cap, y0 + h - cap], color=STORE_EDGE, lw=1.8, zorder=4)
        self.ax.add_patch(Ellipse((cx, y0 + h - cap), w, 2 * cap, fc="#FFFBEE", ec=STORE_EDGE, lw=1.8, zorder=4))
        self.boxes.append((name, (x0, y0, x0 + w, y0 + h)))
        self._text_block(name, cx, y0 + (cap + h - 2 * cap) / 2, lines, (x0, y0 + cap, x0 + w, y0 + h - 2 * cap))

    def group(self, name, x0, y0, x1, y1, title, title_xy=None, ha="left", va="top"):
        self.ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.15",
                                         fc="#FAFAFA", ec=GROUP_EDGE, lw=1.5, ls=(0, (5, 3)), zorder=1))
        if title:
            tx, ty = title_xy if title_xy else (x0 + 0.18, y1 - 0.14)
            t = self.ax.text(tx, ty, title, ha=ha, va=va, fontsize=11, fontweight="bold", color="#444444", zorder=6)
            self.label_texts.append((name + ".title", t))

    # ------------------------------------------------------------------ edges
    def arrow(self, owner, pts, both=False, lw=1.7, z=2.0):
        """Polyline with an arrow head on the last segment (and on the first when both)."""
        xs, ys = zip(*pts)
        self.ax.plot(xs, ys, color=LINE, lw=lw, solid_capstyle="butt", solid_joinstyle="miter", zorder=z)

        def head(tail, tip):
            dx, dy = tip[0] - tail[0], tip[1] - tail[1]
            n = float(np.hypot(dx, dy))
            k = min(0.22, n) / n
            start = (tip[0] - dx * k, tip[1] - dy * k)
            self.ax.add_patch(FancyArrowPatch(start, tip, arrowstyle="-|>", mutation_scale=17, lw=lw,
                                              color=LINE, shrinkA=0, shrinkB=0, zorder=5))

        head(pts[-2], pts[-1])
        if both:
            head(pts[1], pts[0])
        for a_, b_ in zip(pts[:-1], pts[1:]):
            self.segments.append((owner, a_, b_))

    def bridge(self, x, y, vertical_under=True):
        """Break the line that runs underneath at a crossing: white patch under the over-line."""
        if vertical_under:
            self.ax.add_patch(Rectangle((x - 0.06, y - 0.075), 0.12, 0.15, fc="white", ec="none", zorder=2.3))
        else:
            self.ax.add_patch(Rectangle((x - 0.075, y - 0.06), 0.15, 0.12, fc="white", ec="none", zorder=2.3))

    def label(self, owner, x, y, text, ha="center", va="center", size=10, style="normal", weight="normal",
              color=INK):
        t = self.ax.text(x, y, text, ha=ha, va=va, fontsize=size, fontstyle=style, fontweight=weight,
                         color=color, zorder=7, linespacing=1.18)
        self.label_texts.append((owner, t))
        return t

    # ------------------------------------------------------------------ checks
    def _bbox(self, t):
        r = self.fig.canvas.get_renderer()
        bb = t.get_window_extent(r)
        inv = self.ax.transData.inverted()
        (x0, y0), (x1, y1) = inv.transform((bb.x0, bb.y0)), inv.transform((bb.x1, bb.y1))
        return x0, y0, x1, y1

    @staticmethod
    def _rect_hit(a, b, pad=0.0):
        return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])

    @staticmethod
    def _seg_hits_rect(p, q, r, pad=0.03):
        x0, y0, x1, y1 = r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad
        dx, dy = q[0] - p[0], q[1] - p[1]
        t0, t1 = 0.0, 1.0
        for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
            if pp == 0:
                if qq < 0:
                    return False
            else:
                t = qq / pp
                if pp < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
        return t0 <= t1

    def check(self, label):
        self.fig.canvas.draw()
        problems = []
        labels = [(o, t, self._bbox(t)) for o, t in self.label_texts]
        for i, (o1, t1, b1) in enumerate(labels):
            for (o2, t2, b2) in labels[i + 1:]:
                if self._rect_hit(b1, b2, pad=0.02):
                    problems.append(f"label/label overlap: {t1.get_text()!r} x {t2.get_text()!r}")
            for (o, seg_a, seg_b) in self.segments:
                if self._seg_hits_rect(seg_a, seg_b, b1):
                    problems.append(f"arrow {o} touches label {t1.get_text()!r}")
            for (name, bx) in self.boxes:
                if name in self.circles:
                    cx, cy, r = self.circles[name]
                    nx, ny = min(max(cx, b1[0]), b1[2]), min(max(cy, b1[1]), b1[3])
                    hit = (nx - cx) ** 2 + (ny - cy) ** 2 < (r + 0.03) ** 2
                else:
                    hit = self._rect_hit(b1, bx, pad=0.0)
                if hit:
                    problems.append(f"label {t1.get_text()!r} overlaps node {name}")
            if b1[0] < 0.03 or b1[1] < 0.03 or b1[2] > self.w - 0.03 or b1[3] > self.h - 0.03:
                problems.append(f"label {t1.get_text()!r} leaves the canvas")
        for owner, t, box in self.node_texts:
            b = self._bbox(t)
            if b[0] < box[0] + 0.04 or b[2] > box[2] - 0.04 or b[1] < box[1] + 0.02 or b[3] > box[3] - 0.02:
                problems.append(f"node text {t.get_text()!r} not inside {owner}")
            for (o, seg_a, seg_b) in self.segments:
                if self._seg_hits_rect(seg_a, seg_b, b, pad=0.0):
                    problems.append(f"arrow {o} crosses node text {t.get_text()!r}")
        print(f"[{label}] layout problems: {len(problems)}")
        for p in problems:
            print("   -", p)
        return problems

    def save(self, path: Path, dpi: int = DPI):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path, dpi=dpi, facecolor="white", bbox_inches="tight", pad_inches=0.12)
        plt.close(self.fig)
        print("   saved", path)


def L(text, size=10.5, weight="normal", style="normal", color=INK):
    return (text, size, weight, style, color)


def HDR(text="External entity"):
    return L(text, 9.5, "normal", "italic", HEAD_GREY)


# ====================================================================================
#  DFD level 0
# ====================================================================================
def dfd_level0():
    W, H = 11.6, 6.9
    d = Diagram(W, H)
    sx, sy, r = 5.8, 3.45, 1.3
    d.process_circle("SYS", sx, sy, r, [
        L("0", 12, "bold"), L("Loan Default", 12, "bold"), L("Prediction System", 12, "bold"),
        L("Python pipeline +", 10), L("FastAPI service", 10)])
    d.entity("APP", 1.45, sy, 2.5, 1.5, [HDR(), L("Loan applicant /", 11, "bold"), L("lending app", 11, "bold"),
                                         L("(or simulate_traffic.py)", 9.5)])
    d.entity("RISK", 10.15, sy, 2.5, 1.5, [HDR(), L("Risk / model", 11, "bold"), L("monitoring team", 11, "bold")])
    d.entity("KAG", sx, 6.1, 3.2, 1.1, [HDR(), L("Kaggle dataset", 11.5, "bold"), L("Credit Risk Dataset (public)", 10)])
    d.entity("OFF", sx, 0.75, 3.2, 1.3, [HDR(), L("Loan officer /", 11, "bold"), L("credit analyst", 11, "bold"),
                                         L("(or administrator)", 9.5)])

    def xr(dy):
        return float(np.sqrt(r * r - dy * dy))

    ya, yb = sy + 0.3, sy - 0.3
    # applicant <-> system
    d.arrow("APP>SYS", [(2.7, ya), (sx - xr(0.3), ya)])
    d.label("APP>SYS", (2.7 + sx - xr(0.3)) / 2, ya + 0.1, "loan application\n(10 fields)", va="bottom")
    d.arrow("SYS>APP", [(sx - xr(0.3), yb), (2.7, yb)])
    d.label("SYS>APP", (2.7 + sx - xr(0.3)) / 2, yb - 0.1, "PD, risk band,\ndecision, reasons", va="top")
    # risk team <-> system
    d.arrow("RISK>SYS", [(8.9, ya), (sx + xr(0.3), ya)])
    d.label("RISK>SYS", (8.9 + sx + xr(0.3)) / 2, ya + 0.1, "drift check\nrequest", va="bottom")
    d.arrow("SYS>RISK", [(sx + xr(0.3), yb), (8.9, yb)])
    d.label("SYS>RISK", (8.9 + sx + xr(0.3)) / 2, yb - 0.1, "drift report, alerts,\ndecision mix", va="top")
    # Kaggle -> system
    d.arrow("KAG>SYS", [(sx, 5.55), (sx, sy + r)])
    d.label("KAG>SYS", sx + 0.15, 5.12, "historic loans, 32,581 rows\n(read once for training)", ha="left")
    # officer <-> system
    xl = sx - 0.55
    xr_ = sx + 0.55
    yc = sy - float(np.sqrt(r * r - 0.55 * 0.55))
    d.arrow("OFF>SYS", [(xl, 1.4), (xl, yc)])
    d.label("OFF>SYS", xl - 0.12, 1.85, "kill switch\n(SCORING_DISABLED=1)", ha="right")
    d.arrow("SYS>OFF", [(xr_, yc), (xr_, 1.4)])
    d.label("SYS>OFF", xr_ + 0.12, 1.85, "REVIEW cases,\nPD and reasons", ha="left")
    d.check("dfd level 0")
    d.save(OUT_ARCH / "dfd_level0.png", dpi=240)


# ====================================================================================
#  DFD level 1
# ====================================================================================
def dfd_level1():
    W, H = 12.8, 13.7
    d = Diagram(W, H)
    c0, c1, c2, c3 = 1.4, 4.6, 7.7, 10.8
    t2, t, m, n, o, p = 12.2, 10.5, 8.5, 6.3, 4.2, 2.0
    SW, SH = 2.8, 0.95       # store size

    def P(name, cx, cy, w, h, lines):
        d.process_box(name, cx, cy, w, h, [L(lines[0], 11.5, "bold")] + [L(x, 10.2 if i == 0 else 9.5, "bold" if i == 0 else "normal")
                                                                      for i, x in enumerate(lines[1:])])

    def S(name, cx, cy, ident, l1, l2, h=SH, w=SW):
        d.store(name, cx, cy, w, h, ident, [L(l1, 10, "bold")] + [L(x, 9.3) for x in l2])

    # ---- nodes
    d.entity("K", c2, t2, 2.3, 0.95, [HDR(), L("Kaggle dataset", 11, "bold")])
    S("D1", c2, t, "D1", "raw CSV", ["credit_risk_dataset.csv"])
    P("P1", c1, t, 2.3, 1.0, ["1.0", "Clean and split", "(data_prep)"])
    S("D2", c1, m, "D2", "processed CSV", ["train.csv, val.csv, test.csv"])
    P("P2", c0, m, 2.3, 1.0, ["2.0", "Train and select model", "(train)"])
    P("P3", c2, m, 2.3, 1.2, ["3.0", "Evaluate and back-test", "(evaluate, robustness)"])
    S("D3", c3, m, "D3", "model_v1.joblib", ["metadata_v1.json, candidates/"], w=3.0)
    d.entity("R", 1.05, n, 1.75, 0.95, [HDR(), L("Risk / model", 10.5, "bold"), L("monitoring team", 10.5, "bold")])
    P("P6", c1, n, 2.3, 1.2, ["6.0", "Monitor drift", "(PSI, decision mix,", "Evidently)"])
    S("D5", c2, n, "D5", "reports/", ["evaluation, robustness,", "SHAP and drift files"], h=1.05)
    P("P5", c3, n, 2.0, 1.0, ["5.0", "Explain", "(SHAP top-3 reasons)"])
    S("D4", c1, o, "D4", "predictions.db (SQLite)", ["one row per scored application"])
    P("P4", c3, o, 3.0, 1.6, ["4.0", "Score application", "(API /predict): validate,", "loan_percent_income, PD,",
                              "band, decision"])
    d.entity("O", c2 + 0.3, p, 2.1, 1.2, [HDR(), L("Loan officer /", 10.5, "bold"), L("credit analyst", 10.5, "bold"),
                                          L("(or administrator)", 9)])
    d.entity("A", c3, p, 2.3, 1.2, [HDR(), L("Loan applicant /", 10.5, "bold"), L("lending app", 10.5, "bold"),
                                    L("(or simulate_traffic.py)", 9)])

    # ---- offline chain
    d.arrow("K>D1", [(c2, t2 - 0.475), (c2, t + 0.475)])
    d.label("K>D1", c2 + 0.15, (t2 - 0.475 + t + 0.475) / 2, "downloaded once", ha="left")
    d.arrow("D1>P1", [(c2 - SW / 2, t), (c1 + 1.15, t)])
    d.arrow("D1>P3", [(c2, t - 0.475), (c2, m + 0.6)])
    d.label("D1>P3", c2 + 0.15, (t - 0.475 + m + 0.6) / 2, "raw rows\n(5-fold CV)", ha="left")
    d.arrow("P1>D2", [(c1, t - 0.5), (c1, m + 0.475)])
    d.label("P1>D2", c1 + 0.15, (t - 0.5 + m + 0.475) / 2, "train, val,\ntest CSV", ha="left")
    d.arrow("D2>P2", [(c1 - SW / 2, m), (c0 + 1.15, m)])
    d.arrow("D2>P3", [(c1 + SW / 2, m), (c2 - 1.15, m)])
    d.arrow("D3>P3", [(c3 - 1.5, m), (c2 + 1.15, m)])
    # P2 -> D3 over the top
    ya = 13.0
    d.arrow("P2>D3", [(c0, m + 0.5), (c0, ya), (c3 - 0.6, ya), (c3 - 0.6, m + 0.475)])
    d.label("P2>D3", (c0 + c3 - 0.6) / 2, ya + 0.1, "fitted pipeline and metadata (best model by validation AUC)", va="bottom")
    # P3 -> D5, D3 -> P5, P5 -> D5, P6 -> D5, D2 -> P6
    d.arrow("P3>D5", [(c2, m - 0.6), (c2, n + 0.525)])
    d.arrow("D3>P5", [(c3 - 0.4, m - 0.475), (c3 - 0.4, n + 0.5)])
    d.arrow("P5>D5", [(c3 - 1.0, n), (c2 + SW / 2, n)])
    d.arrow("P6>D5", [(c1 + 1.15, n), (c2 - SW / 2, n)])
    d.arrow("D2>P6", [(c1, m - 0.475), (c1, n + 0.6)])
    # risk team <-> P6
    d.arrow("R>P6", [(1.95, n + 0.2), (c1 - 1.15, n + 0.2)])
    d.label("R>P6", (1.95 + c1 - 1.15) / 2, n + 0.3, "drift check\nrequest", va="bottom")
    d.arrow("P6>R", [(c1 - 1.15, n - 0.2), (1.95, n - 0.2)])
    d.label("P6>R", (1.95 + c1 - 1.15) / 2, n - 0.3, "drift report,\nalerts", va="top")
    # D4 -> P6
    d.arrow("D4>P6", [(c1, o + 0.475), (c1, n - 0.6)])
    # ---- online
    d.arrow("P4>D4", [(c3 - 1.5, o + 0.35), (c1 + SW / 2, o + 0.35)])
    d.label("P4>D4", (c3 - 1.5 + c1 + SW / 2) / 2, o + 0.45, "one log row per request", va="bottom")
    d.arrow("P4>P5", [(c3 - 0.45, o + 0.8), (c3 - 0.45, n - 0.5)])
    d.label("P4>P5", c3 - 0.55, (o + 0.8 + n - 0.5) / 2, "applicant\nrow", ha="right")
    d.arrow("P5>P4", [(c3 + 0.35, n - 0.5), (c3 + 0.35, o + 0.8)])
    d.label("P5>P4", c3 + 0.45, (o + 0.8 + n - 0.5) / 2, "top-3\nreasons", ha="left")
    d.arrow("D3>P4", [(c3 + 1.3, m - 0.475), (c3 + 1.3, o + 0.8)])
    d.label("D3>P4", c3 + 1.2, (m - 0.475 + n + 0.5) / 2 + 0.2, "model\n(loaded at\nstartup)", ha="right")
    # applicant <-> P4 and officer <-> P4
    d.arrow("A<>P4", [(c3, p + 0.6), (c3, o - 0.8)], both=True)
    d.label("A<>P4", c3 - 0.15, (p + 0.6 + o - 0.8) / 2, "application in;\nPD, decision, reasons out", ha="right")
    d.arrow("O<>P4", [(c3 - 1.5, o - 0.35), (c2 + 0.3, o - 0.35), (c2 + 0.3, p + 0.6)], both=True)
    d.label("O<>P4", c2 + 0.2, (o - 0.35 + p + 0.6) / 2, "kill switch in;\nREVIEW cases out", ha="right")
    # D3 -> P6 : model for the score PSI, runs in the corridor under row m
    d.arrow("D3>P6", [(c3 - 1.2, m - 0.475), (c3 - 1.2, 7.45), (c1 + 0.6, 7.45), (c1 + 0.6, n + 0.6)], z=2.6)
    d.bridge(c2, 7.45, vertical_under=True)
    d.check("dfd level 1")
    d.save(OUT_ARCH / "dfd_level1.png")


# ====================================================================================
#  Block diagram
# ====================================================================================
def block_diagram():
    W, H = 11.8, 9.3
    d = Diagram(W, H)
    d.group("OFF", 0.1, 6.5, 11.7, 9.15, "Offline pipeline (Python, run on the developer's laptop)")
    bh = 1.45
    yr = 7.8
    w = 1.85
    xs = [1.4, 3.65, 5.9, 8.15, 10.4]
    spec = [
        [L("data_prep.py", 10.5, "bold"), L("Kaggle CSV, clean,", 9.5), L("70/15/15 split", 9.5)],
        [L("train.py", 10.5, "bold"), L("LR, RF, XGBoost;", 9.5), L("best on validation", 9.5), L("AUC", 9.5)],
        [L("evaluate.py,", 10.5, "bold"), L("robustness.py", 10.5, "bold"), L("test metrics, NPA,", 9.5),
         L("5-fold CV", 9.5)],
        [L("explain.py", 10.5, "bold"), L("SHAP importance", 9.5), L("plots", 9.5)],
        [L("drift.py", 10.5, "bold"), L("PSI per feature,", 9.5), L("Evidently report", 9.5)],
    ]
    for i, (x, lines) in enumerate(zip(xs, spec)):
        d.process_box(f"O{i}", x, yr, w, bh, lines)
    for i in range(4):
        d.arrow(f"O{i}>O{i + 1}", [(xs[i] + w / 2, yr), (xs[i + 1] - w / 2, yr)])

    # online lane
    d.group("ON", 0.1, 1.9, 11.7, 5.45, "Online scoring service (FastAPI, run with uvicorn)",
            title_xy=(11.5, 2.05), ha="right", va="bottom")
    yb, bw = 3.3, 1.6
    xo = [1.15, 3.05, 4.95, 6.85, 8.75, 10.65]
    bhh = 1.6
    d.process_box("N0", xo[0], yb, bw, bhh, [L("Pydantic", 10.5, "bold"), L("validation", 10.5, "bold"),
                                             L("LoanApplication,", 9.5), L("422 if invalid", 9.5)])
    d.process_box("N1", xo[1], yb, bw, bhh, [L("Pipeline", 10.5, "bold"), L("imputer + encoder", 9.5), L("+ XGBoost", 9.5),
                                             L("loan_percent_income", 9.5), L("computed first", 9.5)])
    d.process_box("N2", xo[2], yb, bw, bhh, [L("Decision policy", 10.5, "bold"), L("APPROVE < 0.20", 9.5),
                                             L("REVIEW < 0.50", 9.5), L("else REJECT", 9.5)])
    d.process_box("N3", xo[3], yb, bw, bhh, [L("SHAP Explainer", 10.5, "bold"), L("top-3 reasons", 9.5),
                                             L("(TreeExplainer)", 9.5)])
    d.cylinder("N4", xo[4], yb, bw, bhh, [L("SQLite log", 10.5, "bold"), L("predictions.db,", 9.5), L("one row per", 9.5),
                                          L("application", 9.5)])
    d.process_box("N5", xo[5], yb, bw, bhh, [L("/monitoring/drift", 10.5, "bold"), L("PSI, decision mix,", 9.5),
                                             L("alerts", 9.5)])
    for i in range(5):
        d.arrow(f"N{i}>N{i + 1}", [(xo[i] + bw / 2, yb), (xo[i + 1] - bw / 2, yb)])
    # kill switch above the decision policy
    d.entity("KS", xo[2], 4.75, 1.9, 0.62, [L("SCORING_DISABLED=1", 9.3, "bold"), L("kill switch, env var", 8.6)])
    d.arrow("KS>N2", [(xo[2], 4.75 - 0.31), (xo[2], yb + bhh / 2)])

    # offline -> online
    d.arrow("O1>N1", [(3.3, yr - bh / 2), (3.3, yb + bhh / 2)])
    d.label("O1>N1", 3.42, 6.2, "model_v1.joblib,\nmetadata_v1.json", ha="left")
    d.arrow("O0>N5", [(0.85, yr - bh / 2), (0.85, 5.9), (10.2, 5.9), (10.2, yb + bhh / 2)], z=2.6)
    d.label("O0>N5", 5.5, 5.97, "train.csv, val.csv (drift reference and approval baseline)", ha="left", va="bottom")
    d.bridge(3.3, 5.9, vertical_under=True)

    # clients
    d.group("CL", 0.1, 0.1, 7.3, 1.45, "Clients (HTTP, JSON)", title_xy=(0.28, 1.35))
    d.entity("C0", 1.35, 0.7, 1.95, 0.7, [L("Swagger UI", 10, "bold"), L("/docs", 9)])
    d.entity("C1", 3.7, 0.7, 2.2, 0.7, [L("simulate_traffic.py", 10, "bold"), L("500 requests", 9)])
    d.entity("C2", 6.0, 0.7, 1.9, 0.7, [L("Any HTTP client", 10, "bold"), L("(lending app, curl)", 9)])
    d.arrow("CL<>N0", [(1.15, 1.45), (1.15, yb - bhh / 2)], both=True)
    d.label("CL<>N0", 1.3, 1.67, "POST /predict, JSON in;  ScoreResponse JSON out", ha="left")
    d.check("block")
    d.save(OUT_ARCH / "block_diagram.png")


# ====================================================================================
#  SRS figures: Canvas class (copied from the reference build_srs.py)
# ====================================================================================
class Canvas:
    """A matplotlib canvas in inches with a text-overlap check."""

    def __init__(self, w: float, h: float):
        self.w, self.h = w, h
        self.fig = plt.figure(figsize=(w, h), dpi=DPI, facecolor="white")
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w)
        self.ax.set_ylim(0, h)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.texts: list = []

    def text(self, x, y, s, size=9, weight="normal", style="normal", color=INK, ha="center",
             va="center", bg=None, z=5, check=True, **kw):
        bbox = dict(facecolor=bg, edgecolor="none", pad=1.2) if bg else None
        t = self.ax.text(x, y, s, fontsize=size, fontweight=weight, fontstyle=style, color=color,
                         ha=ha, va=va, bbox=bbox, zorder=z, linespacing=1.18, **kw)
        if check:
            self.texts.append(t)
        return t

    def line(self, p, q, color=LINE, lw=1.1, ls="-", z=2):
        self.ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=lw, ls=ls, zorder=z, solid_capstyle="butt")

    def arrow(self, p, q, color=LINE, lw=1.1, ls="-", head=9, z=3):
        self.ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=head, color=color,
                                          lw=lw, ls=ls, zorder=z, shrinkA=0, shrinkB=0))

    def check_text_overlap(self, name: str):
        self.fig.canvas.draw()
        r = self.fig.canvas.get_renderer()
        boxes = [(t, t.get_window_extent(r)) for t in self.texts if t.get_text().strip()]
        bad = []
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i][1], boxes[j][1]
                if a.overlaps(b):
                    bad.append((boxes[i][0].get_text()[:30], boxes[j][0].get_text()[:30]))
        fb = self.fig.bbox
        for t, bb in boxes:
            if bb.x0 < fb.x0 - 1 or bb.x1 > fb.x1 + 1 or bb.y0 < fb.y0 - 1 or bb.y1 > fb.y1 + 1:
                bad.append((t.get_text()[:30], "outside the figure"))
        print(f"  {name}: {len(boxes)} labels, overlaps/outside: {len(bad)}")
        for b in bad:
            print("     !", b)
        return bad

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path, dpi=DPI, facecolor="white")
        plt.close(self.fig)
        print("   saved", path)


def _stick(c: Canvas, x, y, label, sub=None):
    """Stick figure with head at (x, y+0.42)."""
    c.ax.add_patch(plt.Circle((x, y + 0.42), 0.11, fill=False, ec=INK, lw=1.3, zorder=4))
    c.line((x, y + 0.31), (x, y - 0.05), color=INK, lw=1.3, z=4)
    c.line((x - 0.2, y + 0.18), (x + 0.2, y + 0.18), color=INK, lw=1.3, z=4)
    c.line((x, y - 0.05), (x - 0.17, y - 0.34), color=INK, lw=1.3, z=4)
    c.line((x, y - 0.05), (x + 0.17, y - 0.34), color=INK, lw=1.3, z=4)
    c.text(x, y - 0.62, label, size=9, weight="bold", bg="white", z=6)
    if sub:
        c.text(x, y - 1.0, sub, size=7.5, color=GREY, bg="white", z=6)


# ====================================================================================
#  Use case diagram
# ====================================================================================
def draw_use_case():
    W, H = 10.6, 10.6
    c = Canvas(W, H)
    ax = c.ax
    bx0, bx1, by0, by1 = 1.75, 8.6, 1.25, H - 0.35
    ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fill=False, ec=PROC_EDGE, lw=1.6, zorder=1))
    c.text((bx0 + bx1) / 2, by1 - 0.25, "Loan Default Prediction System (Python pipeline + FastAPI service)",
           size=9.6, weight="bold", color=PROC_EDGE)

    cx, cw, ch = 3.95, 3.5, 0.5
    ix, iw = 7.3, 2.15
    y0 = by1 - 1.35
    main = [
        ("Submit application for scoring", y0),
        ("View PD, decision and reasons", y0 - 1.75),
        ("Review a REVIEW-band application", y0 - 2.55),
        ("Turn on kill switch", y0 - 3.3),
        ("Check API health", y0 - 4.0),
        ("View model info", y0 - 4.7),
        ("Run drift report", y0 - 5.4),
        ("Retrain / evaluate model (offline pipeline)", y0 - 6.1),
        ("Run tests", y0 - 6.8),
    ]
    for t, y in main:
        ax.add_patch(Ellipse((cx, y), cw, ch, fc=PROC_FILL, ec=PROC_EDGE, lw=1.3, zorder=3))
        c.text(cx, y, t, size=8.4, z=6)
    ys = [y for _, y in main]
    incl = [("Validate input (422 if bad)", ys[0] + 0.75, ys[0]), ("Score: PD, band, decision", ys[0], ys[0]),
            ("Log prediction (SQLite)", ys[0] - 0.75, ys[0]), ("Explain: SHAP top-3 reasons", ys[1], ys[1])]
    for t, y, src_y in incl:
        ax.add_patch(Ellipse((ix, y), iw, ch, fc="white", ec=PROC_EDGE, lw=1.3, ls="--", zorder=3))
        c.text(ix, y, t, size=7.9, z=6)
        c.arrow((cx + cw / 2, src_y), (ix - iw / 2, y), ls="--", lw=1.0, head=8)
        c.text((cx + cw / 2 + ix - iw / 2) / 2 + 0.02, (src_y + y) / 2 + 0.17, "«include»", size=6.6, color=GREY, bg="white")

    # actors
    def link(ax_x, ax_y, row, side):
        y = ys[row]
        x = cx - cw / 2 if side == "L" else cx + cw / 2
        c.line((ax_x, ax_y + 0.18), (x, y), lw=0.9, color="#555555", z=2)

    ay_app, ay_off = ys[0] - 1.0, ys[2] - 0.4
    _stick(c, 0.8, ay_app, "Loan applicant", "(through a\nlending app)")
    link(0.92, ay_app, 0, "L")
    link(0.92, ay_app, 1, "L")
    _stick(c, 0.8, ay_off - 0.85, "Loan officer", "(credit analyst)")
    link(0.92, ay_off - 0.85, 1, "L")
    link(0.92, ay_off - 0.85, 2, "L")
    ay_adm = (ys[3] + ys[4]) / 2 - 0.05
    _stick(c, 9.6, ay_adm, "Administrator", "sets\nSCORING_DISABLED")
    link(9.48, ay_adm, 3, "R")
    link(9.48, ay_adm, 4, "R")
    ay_risk = (ys[6] + ys[8]) / 2 - 0.05
    _stick(c, 9.6, ay_risk, "Risk analyst", "model owner")
    for row in (5, 6, 7, 8):
        link(9.48, ay_risk, row, "R")

    c.text(bx0, 0.72, "Solid line: association.   Dashed arrow: «include».   With the kill switch on, the model still scores\n"
           "and logs every application, but the decision is always REVIEW (a person decides).", size=7.6,
           color=GREY, ha="left")
    c.check_text_overlap("use_case")
    c.save(OUT_SRS / "use_case.png")


# ====================================================================================
#  ER diagram
# ====================================================================================
def _one(c: Canvas, pt, direction):
    dx, dy = direction
    for off in (0.13, 0.2):
        bx, by = pt[0] + dx * off, pt[1] + dy * off
        c.line((bx - dy * 0.09, by + dx * 0.09), (bx + dy * 0.09, by - dx * 0.09), lw=1.2, z=4)


def _many(c: Canvas, pt, direction, optional=True):
    dx, dy = direction
    tip = (pt[0] + dx * 0.2, pt[1] + dy * 0.2)
    for s in (-1, 0, 1):
        c.line(tip, (pt[0] - dy * 0.11 * s, pt[1] + dx * 0.11 * s), lw=1.1, z=4)
    if optional:
        cxy = (pt[0] + dx * 0.3, pt[1] + dy * 0.3)
        c.ax.add_patch(plt.Circle(cxy, 0.065, fc="white", ec=LINE, lw=1.1, zorder=5))


def _table(c: Canvas, x, y_top, w, name, badge, rows, physical, line_h=0.21, head_h=0.6, size=8.1):
    """Entity box with a name + badge header and rows of (field, type, tag). Returns (x0, y0, x1, y1, ys)."""
    h = head_h + len(rows) * line_h + 0.12
    y0 = y_top - h
    edge = PROC_EDGE if physical else ENT_EDGE
    c.ax.add_patch(Rectangle((x, y0), w, h, fc="white", ec=edge, lw=1.5, zorder=3,
                             ls="-" if physical else (0, (6, 3))))
    c.ax.add_patch(Rectangle((x, y_top - head_h), w, head_h, fc=PROC_FILL if physical else ENT_FILL, ec=edge, lw=1.5,
                             zorder=3, ls="-" if physical else (0, (6, 3))))
    c.text(x + w / 2, y_top - 0.2, name, size=9.4, weight="bold", z=6)
    c.text(x + w / 2, y_top - 0.45, badge, size=7.2, style="italic", color=GREY, z=6)
    yy = y_top - head_h - 0.06 - line_h / 2
    ys = []
    for field, typ, tag in rows:
        if tag:
            c.text(x + 0.3, yy, tag, size=size - 0.4, weight="bold", color=PROC_EDGE, ha="center", z=6)
        c.text(x + 0.55, yy, field, size=size, ha="left", z=6)
        c.text(x + w - 0.12, yy, typ, size=size - 0.7, ha="right", color=GREY, z=6)
        ys.append(yy)
        yy -= line_h
    return x, y0, x + w, y_top, ys


def draw_er():
    W, H = 9.3, 9.5
    c = Canvas(W, H)
    top = 9.25
    tr_rows = [("person_age", "int", ""), ("person_income", "int", ""), ("person_home_ownership", "text", ""),
               ("person_emp_length", "float, some missing", ""), ("loan_intent", "text", ""), ("loan_grade", "text", ""),
               ("loan_amnt", "int", ""), ("loan_int_rate", "float, some missing", ""),
               ("loan_status", "int, 1 = default", "target"), ("loan_percent_income", "float", ""),
               ("cb_person_default_on_file", "text, Y or N", ""), ("cb_person_cred_hist_length", "int", "")]
    tr = _table(c, 0.2, top, 4.0, "TrainingRecord", "logical: credit_risk_dataset.csv, data/processed/*.csv", tr_rows,
                physical=False)
    c.text(0.2 + 2.0, tr[1] - 0.14, "no key column: the dataset has no id, one row = one loan", size=7.2, style="italic",
           color=GREY)
    mv_top = tr[1] - 1.45
    mv_rows = [("model_version", "text", "PK"), ("model_name", "text", ""), ("trained_at", "ISO time, UTC", ""),
               ("features", "list of 11 names", ""), ("validation_metrics", "3 models x 6 numbers", ""),
               ("train_rows", "int", ""), ("train_default_rate", "float", "")]
    mv = _table(c, 0.2, mv_top, 4.0, "ModelVersion", "logical: models/metadata_v1.json + model_v1.joblib", mv_rows,
                physical=False)
    pr_rows = [("application_id", "TEXT", "PK"), ("created_at", "TEXT NOT NULL", ""),
               ("model_version", "TEXT NOT NULL", "FK"), ("person_age", "INTEGER", ""), ("person_income", "REAL", ""),
               ("person_home_ownership", "TEXT", ""), ("person_emp_length", "REAL", ""), ("loan_intent", "TEXT", ""),
               ("loan_grade", "TEXT", ""), ("loan_amnt", "REAL", ""), ("loan_int_rate", "REAL", ""),
               ("loan_percent_income", "REAL", ""), ("cb_person_default_on_file", "TEXT", ""),
               ("cb_person_cred_hist_length", "INTEGER", ""), ("pd", "REAL NOT NULL", ""),
               ("decision", "TEXT NOT NULL", ""), ("latency_ms", "REAL", "")]
    # align the model_version FK row of predictions with the PK row of ModelVersion
    head_h, line_h = 0.6, 0.21
    fk_offset = head_h + 0.06 + line_h / 2 + 2 * line_h
    pk_offset = head_h + 0.06 + line_h / 2
    pr_top = mv_top - pk_offset + fk_offset
    pr = _table(c, 5.0, pr_top, 4.1, "predictions", "physical: SQLite table, logs/predictions.db", pr_rows, physical=True)
    c.text(5.0 + 2.05, pr[1] - 0.17, "index idx_predictions_created on created_at", size=7.2, style="italic", color=GREY)

    # TrainingRecord -> ModelVersion : many rows train one version (dashed = logical link)
    xm = 2.2
    c.line((xm, tr[1] - 0.32), (xm, mv[3] + 0.2), lw=1.1, ls=(0, (2, 2)), z=2)
    _many(c, (xm, tr[1] - 0.32), (0, -1), optional=False)
    _one(c, (xm, mv[3]), (0, 1))
    c.text(xm + 0.12, (tr[1] - 0.32 + mv[3]) / 2 - 0.12, "trains  (rows of train.csv fit\none ModelVersion)", size=7.2,
           color=GREY, ha="left", bg="white")
    # ModelVersion -> predictions : one version scores many predictions (dashed: no FOREIGN KEY in SQLite)
    ypk = mv[4][0]
    p, q = (mv[2], ypk), (pr[0], ypk)
    c.line(p, q, lw=1.1, ls=(0, (2, 2)), z=2)
    _one(c, p, (1, 0))
    _many(c, q, (-1, 0))
    c.text((p[0] + q[0]) / 2, ypk + 0.17, "scored by", size=7.2, color=GREY, bg="white")

    # reading guide, top right
    gx, gy = 5.0, 9.25
    c.ax.add_patch(Rectangle((gx, gy - 3.55), 4.1, 3.55, fill=False, ec="#BBBBBB", lw=0.9, zorder=1))
    c.text(gx + 0.15, gy - 0.22, "How to read this diagram", size=8.6, weight="bold", ha="left")
    c.ax.add_patch(Rectangle((gx + 0.15, gy - 0.78), 0.55, 0.28, fc=PROC_FILL, ec=PROC_EDGE, lw=1.3, zorder=3))
    c.text(gx + 0.85, gy - 0.64, "physical: a table inside the SQLite file", size=7.8, ha="left")
    c.ax.add_patch(Rectangle((gx + 0.15, gy - 1.2), 0.55, 0.28, fc=ENT_FILL, ec=ENT_EDGE, lw=1.3, zorder=3,
                             ls=(0, (4, 2))))
    c.text(gx + 0.85, gy - 1.06, "logical: kept in files (CSV, JSON, joblib),\nnot in a database", size=7.8, ha="left")
    c.line((gx + 0.15, gy - 1.62), (gx + 0.7, gy - 1.62), lw=1.1, ls=(0, (2, 2)))
    c.text(gx + 0.85, gy - 1.62, "link by value, no database constraint", size=7.8, ha="left")
    c.text(gx + 0.15, gy - 2.05, "PK primary key.  FK foreign key by value only:\n"
           "SQLite has no FOREIGN KEY on model_version.", size=7.6, color=GREY, ha="left")
    c.text(gx + 0.15, gy - 2.62, "Bars = exactly one.  Crow's foot = many.\nCircle = zero allowed.", size=7.6,
           color=GREY, ha="left")
    c.text(gx + 0.15, gy - 3.2, "Source: src/api/store.py (SCHEMA), models/metadata_v1.json,\n"
           "data/raw/credit_risk_dataset.csv.", size=7.2, color=GREY, ha="left")
    c.check_text_overlap("er_diagram")
    c.save(OUT_SRS / "er_diagram.png")


# ====================================================================================
#  Sequence diagram: POST /predict
# ====================================================================================
def draw_sequence():
    lanes = ["Client", "FastAPI\n/predict", "Pydantic\nLoanApplication", "Pipeline\n(imputer, encoder,\nXGBoost)",
             "Decision\npolicy", "Explainer\n(SHAP)", "store\n(SQLite)"]
    n = len(lanes)
    W, H = 9.6, 11.4
    c = Canvas(W, H)
    x0, dx = 0.9, 1.3
    xs = [x0 + i * dx for i in range(n)]
    top = H - 0.3
    bottom = 0.85
    for x, name in zip(xs, lanes):
        c.ax.add_patch(Rectangle((x - 0.56, top - 0.72), 1.12, 0.72, fc=PROC_FILL, ec=PROC_EDGE, lw=1.3, zorder=3))
        c.text(x, top - 0.36, name, size=7.6, weight="bold", z=6)
        c.line((x, top - 0.72), (x, bottom), color="#9A9A9A", lw=0.9, ls=(0, (4, 3)), z=1)
    CL, FA, PY, PL, DP, EX, ST = range(7)
    state = {"y": top - 1.15, "n": 0}

    def msg(a, b, label, ret=False, gap=0.55, num=True):
        y = state["y"]
        if num and not ret:
            state["n"] += 1
            label = f"{state['n']}  {label}"
        xa, xb = xs[a], xs[b]
        if a == b:
            c.line((xa, y), (xa + 0.5, y), lw=1.1)
            c.line((xa + 0.5, y), (xa + 0.5, y - 0.26), lw=1.1)
            c.arrow((xa + 0.5, y - 0.26), (xa + 0.02, y - 0.26), lw=1.1)
            c.text(xa + 0.62, y - 0.13, label, size=8.0, ha="left", bg="white")
            state["y"] -= gap + 0.12
            return
        c.arrow((xa, y), (xb, y), ls=(0, (4, 2.5)) if ret else "-", lw=1.1)
        c.text((xa + xb) / 2, y + (0.21 if "\n" in label else 0.15), label, size=8.0, bg="white", z=6)
        state["y"] -= gap

    def frame(kind, cond, xl, xr, y_top, y_bot, cond2=None, y_mid=None):
        c.ax.add_patch(Rectangle((xl, y_bot), xr - xl, y_top - y_bot, fill=False, ec=PROC_EDGE, lw=1.1, zorder=2))
        kw = 0.62
        c.ax.add_patch(Rectangle((xl, y_top - 0.22), kw, 0.22, fc=PROC_FILL, ec=PROC_EDGE, lw=1.1, zorder=2))
        c.text(xl + kw / 2, y_top - 0.11, kind, size=7.4, weight="bold", z=6)
        c.text(xl + kw + 0.1, y_top - 0.11, cond, size=7.4, ha="left", style="italic", z=6)

    msg(CL, FA, "POST /predict\n(JSON, 10 fields)", gap=0.58)
    msg(FA, PY, "validate\nLoanApplication", gap=0.62)
    # break frame: invalid input
    fy = state["y"] + 0.2
    state["y"] -= 0.3
    msg(PY, FA, "ValidationError", ret=True, gap=0.45)
    msg(FA, CL, "422 with field errors; nothing is\nscored or logged", ret=True, gap=0.5)
    frame("break", "[invalid input]", xs[0] - 0.62, xs[2] + 0.62, fy, state["y"] + 0.22)
    state["y"] -= 0.05
    msg(PY, FA, "validated application", ret=True, gap=0.5)
    msg(FA, FA, "loan_percent_income =\nround(loan_amnt / person_income, 2)", gap=0.46)
    msg(FA, PL, "predict_proba(X)[0, 1]", gap=0.45)
    msg(PL, FA, "PD", ret=True, gap=0.5)
    msg(FA, DP, "PD below 0.20: APPROVE,\nbelow 0.50: REVIEW, else REJECT", gap=0.62)
    fy2 = state["y"] + 0.22
    state["y"] -= 0.3
    msg(DP, DP, "decision = REVIEW", gap=0.3)
    frame("opt", "[SCORING_DISABLED=1]", xs[DP] - 0.7, xs[DP] + 1.6 + 0.3, fy2, state["y"] + 0.1)
    state["y"] -= 0.05
    msg(DP, FA, "risk_band, decision", ret=True, gap=0.5)
    msg(FA, EX, "reasons(X)", gap=0.45)
    msg(EX, FA, "top_reasons (SHAP > 0, up to 3)", ret=True, gap=0.5)
    msg(FA, ST, "log_prediction(row)\nINSERT INTO predictions", gap=0.62)
    msg(ST, FA, "committed", ret=True, gap=0.5)
    msg(FA, CL, "200  ScoreResponse JSON\n(PD, band, decision, reasons, latency_ms)", ret=True, gap=0.3)
    c.text(0.25, 0.45, "Solid arrow: call.   Dashed arrow: return.   Source: src/api/main.py, schemas.py, store.py.",
           size=7.0, color=GREY, ha="left")
    c.text(0.25, 0.2, "latency_ms: the timer starts when predict() is entered (after validation) and stops before the log write.",
           size=7.0, color=GREY, ha="left")
    print("   sequence final y:", round(state["y"], 2), "bottom", bottom)
    c.check_text_overlap("sequence_predict")
    c.save(OUT_SRS / "sequence_predict.png")


if __name__ == "__main__":
    which = sys.argv[1:] or ["l0", "l1", "block", "uc", "er", "seq"]
    if "l0" in which:
        dfd_level0()
    if "l1" in which:
        dfd_level1()
    if "block" in which:
        block_diagram()
    if "uc" in which:
        draw_use_case()
    if "er" in which:
        draw_er()
    if "seq" in which:
        draw_sequence()
