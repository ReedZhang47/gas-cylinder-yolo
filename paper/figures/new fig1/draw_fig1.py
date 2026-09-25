"""Draw the v5 study pipeline as vector PDF and editable SVG.

The PDF replaces paper/figures/fig1_pipeline.pdf.  The SVG stays beside this
script as the editable master.  All positions are in points with a top-left
origin, and both outputs are generated from the same drawing commands.
"""

from __future__ import annotations

import html
import math
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


HERE = Path(__file__).resolve().parent
OUT_PDF = HERE.parent / "fig1_pipeline.pdf"
OUT_SVG = HERE / "main_pipeline_v5.svg"
W, H = 704, 454

INK = "#1B3448"
MUTED = "#566C7D"
LINE = "#96AABA"
A = "#426F96"
B = "#B88232"
C = "#178A93"
D = "#755CAD"
DEV = "#72879A"
TRAIN = "#206C78"


def register_fonts() -> tuple[str, str]:
    font_dir = Path(r"C:\Windows\Fonts")
    regular = font_dir / "arial.ttf"
    bold = font_dir / "arialbd.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("FigArial", str(regular)))
        pdfmetrics.registerFont(TTFont("FigArialBold", str(bold)))
        return "FigArial", "FigArialBold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


class Figure:
    def __init__(self) -> None:
        self.pdf = canvas.Canvas(str(OUT_PDF), pagesize=(W, H), pageCompression=1)
        self.pdf.setTitle("Four-arm study pipeline")
        self.pdf.setAuthor("Gas Cylinder Safety Detection project")
        self.svg: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" '
            f'viewBox="0 0 {W} {H}" role="img" '
            'aria-label="Four-arm data preparation, training, and development evaluation pipeline">',
            '<rect x="0" y="0" width="704" height="454" fill="#ffffff"/>',
        ]

    def box(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        fill: str = "#ffffff",
        stroke: str = LINE,
        radius: float = 7,
        width: float = 1.05,
        dashed: bool = False,
    ) -> None:
        p = self.pdf
        p.saveState()
        p.setFillColor(HexColor(fill))
        p.setStrokeColor(HexColor(stroke))
        p.setLineWidth(width)
        if dashed:
            p.setDash(4, 3)
        p.roundRect(x, H - y - h, w, h, radius, stroke=1, fill=1)
        p.restoreState()
        dash = ' stroke-dasharray="4 3"' if dashed else ""
        self.svg.append(
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{radius:g}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width:g}"{dash}/>'
        )

    def stripe(self, x: float, y: float, h: float, color: str) -> None:
        p = self.pdf
        p.setFillColor(HexColor(color))
        p.rect(x, H - y - h, 3.5, h, stroke=0, fill=1)
        self.svg.append(
            f'<rect x="{x:g}" y="{y:g}" width="3.5" height="{h:g}" fill="{color}"/>'
        )

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        size: float = 11.5,
        color: str = INK,
        bold: bool = False,
        align: str = "left",
        max_width: float | None = None,
    ) -> None:
        font = FONT_BOLD if bold else FONT
        measured = pdfmetrics.stringWidth(value, font, size)
        if max_width is not None and measured > max_width + 0.2:
            raise ValueError(f"Text exceeds box width ({measured:.1f}>{max_width}): {value}")
        p = self.pdf
        p.saveState()
        p.setFillColor(HexColor(color))
        p.setFont(font, size)
        baseline = H - y - 0.34 * size
        if align == "center":
            p.drawCentredString(x, baseline, value)
        elif align == "right":
            p.drawRightString(x, baseline, value)
        else:
            p.drawString(x, baseline, value)
        p.restoreState()
        anchor = {"left": "start", "center": "middle", "right": "end"}[align]
        weight = "700" if bold else "400"
        self.svg.append(
            f'<text x="{x:g}" y="{y:g}" dominant-baseline="middle" text-anchor="{anchor}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{size:g}" '
            f'font-weight="{weight}" fill="{color}">{html.escape(value)}</text>'
        )

    def line(
        self,
        points: list[tuple[float, float]],
        *,
        color: str = LINE,
        width: float = 1.15,
        dashed: bool = False,
        arrow: bool = False,
    ) -> None:
        p = self.pdf
        p.saveState()
        p.setStrokeColor(HexColor(color))
        p.setLineWidth(width)
        p.setLineJoin(1)
        p.setLineCap(1)
        if dashed:
            p.setDash(4, 3)
        path = p.beginPath()
        path.moveTo(points[0][0], H - points[0][1])
        for x, y in points[1:]:
            path.lineTo(x, H - y)
        p.drawPath(path, stroke=1, fill=0)
        p.restoreState()
        coords = " ".join(f"{x:g},{y:g}" for x, y in points)
        dash = ' stroke-dasharray="4 3"' if dashed else ""
        self.svg.append(
            f'<polyline points="{coords}" fill="none" stroke="{color}" '
            f'stroke-width="{width:g}" stroke-linejoin="round" '
            f'stroke-linecap="round"{dash}/>'
        )
        if arrow:
            x1, y1 = points[-2]
            x2, y2 = points[-1]
            length = math.hypot(x2 - x1, y2 - y1)
            ux, uy = (x2 - x1) / length, (y2 - y1) / length
            px, py = -uy, ux
            base_x, base_y = x2 - 6.2 * ux, y2 - 6.2 * uy
            tri = [
                (x2, y2),
                (base_x + 3.0 * px, base_y + 3.0 * py),
                (base_x - 3.0 * px, base_y - 3.0 * py),
            ]
            p.saveState()
            p.setFillColor(HexColor(color))
            shape = p.beginPath()
            shape.moveTo(tri[0][0], H - tri[0][1])
            for x, y in tri[1:]:
                shape.lineTo(x, H - y)
            shape.close()
            p.drawPath(shape, stroke=0, fill=1)
            p.restoreState()
            vertices = " ".join(f"{x:g},{y:g}" for x, y in tri)
            self.svg.append(f'<polygon points="{vertices}" fill="{color}"/>')

    def save(self) -> None:
        self.pdf.showPage()
        self.pdf.save()
        self.svg.append("</svg>")
        OUT_SVG.write_text("\n".join(self.svg) + "\n", encoding="utf-8")


def make_figure() -> None:
    f = Figure()

    # The three phases use quiet tinted fields; the diagram remains readable in greyscale.
    f.box(20, 109, 664, 105, fill="#FAFCFD", stroke="#E5EDF2", radius=8, width=0.8)
    f.box(20, 236, 664, 78, fill="#F7FAFB", stroke="#E5EDF2", radius=8, width=0.8)
    f.box(20, 326, 664, 101, fill="#F4F8FA", stroke="#DCE7ED", radius=8, width=0.8)

    # Main dependencies are drawn behind the nodes.
    f.line([(126, 95), (126, 111)], color=A)
    f.line([(101.5, 111), (602.5, 111)], color=A)
    for cx in (101.5, 268.5, 435.5):
        f.line([(cx, 111), (cx, 129)], color=A, arrow=True)
    f.line([(602.5, 111), (602.5, 129)], color=D, dashed=True, arrow=True)
    for cx in (101.5, 268.5, 435.5):
        f.line([(cx, 205), (cx, 227)], color=LINE)
    f.line([(602.5, 205), (602.5, 227)], color=D, dashed=True)
    f.line([(101.5, 227), (602.5, 227)], color=LINE)
    f.line([(352, 227), (352, 255)], color=TRAIN, arrow=True)
    f.line([(352, 309), (352, 347)], color=TRAIN)
    f.line([(128, 347), (576, 347)], color=TRAIN)
    for cx in (130, 352, 574):
        f.line([(cx, 347), (cx, 360)], color=TRAIN, arrow=True)
    # dev61 bypasses data generation and training, entering evaluation only.
    f.line([(676, 66), (691, 66), (691, 339), (680, 339)],
           color=DEV, dashed=True, arrow=True)

    f.text(28, 18, "DATA ORIGIN AND FOUR TRAINING ARMS", size=11.3, bold=True, color=MUTED)
    f.box(28, 37, 196, 58, fill="#EFF5F9", stroke=A, radius=7, width=1.2)
    f.text(42, 55, "Real seed set", size=14.6, bold=True, max_width=170)
    f.text(42, 76, "real93, 93 annotated photos", size=12.1, max_width=170)
    f.box(493, 37, 183, 58, fill="#F8FAFB", stroke=DEV, radius=7, dashed=True)
    f.text(506, 54, "External development", size=13.3, bold=True, max_width=157)
    f.text(506, 73, "dev61, 61 images", size=11.9, max_width=157)
    f.text(506, 87, "evaluation only", size=11.0, color=MUTED, max_width=157)

    arms = [
        (28, A, "A  Real only", "93 photos", "manual boxes", False),
        (195, B, "B  Offline aug.", "1085 images", "boxes transformed", False),
        (362, C, "C  Image editing", "1085 images", "boxes reviewed", False),
        (529, D, "D  LoRA T2I", "target 1085 images", "dataset in progress", True),
    ]
    for x, accent, title, count, note, pending in arms:
        f.box(x, 129, 147, 76, fill="#FFFFFF", stroke=accent, radius=6,
              width=1.2, dashed=pending)
        f.stripe(x + 1, 135, 64, accent)
        f.text(x + 12, 147, title, size=13.5, bold=True, color=accent, max_width=126)
        f.text(x + 12, 170, count, size=12.3, max_width=126)
        f.text(x + 12, 189, note, size=11.2, color=MUTED, max_width=126)

    f.text(28, 247, "CONTROLLED TRAINING", size=11.3, bold=True, color=MUTED)
    f.box(156, 255, 392, 54, fill="#EAF5F5", stroke=TRAIN, radius=7, width=1.3)
    f.text(352, 272, "Six YOLO detectors, 300 epochs", size=15.1,
           bold=True, align="center", max_width=366)
    f.text(352, 293, "v8 / v11 / v26 (s, m); checkpoints every 10 epochs", size=12.1,
           align="center", max_width=366)

    f.text(32, 337, "DEVELOPMENT EVALUATION", size=11.3, bold=True, color=MUTED)
    reports = [
        (29, "Fixed endpoint", "last.pt on dev61", "transparent benchmark"),
        (251, "Cross-fitted OOF", "5 held-out folds, pooled AP", "joint model + checkpoint"),
        (473, "Deployment choice", "selected on all dev61", "development score only"),
    ]
    for x, title, line1, line2 in reports:
        f.box(x, 360, 202, 58, fill="#FFFFFF", stroke="#A8BBC8", radius=6, width=1.0)
        f.text(x + 11, 375, title, size=13.6, bold=True, max_width=180)
        f.text(x + 11, 392, line1, size=11.6, max_width=180)
        f.text(x + 11, 407, line2, size=11.0, color=MUTED, max_width=180)

    f.text(352, 443,
           "OOF comparisons use paired, image-cluster bootstrap (10,000 resamples).",
           size=11.3, color=MUTED, align="center", max_width=660)
    f.save()
    print(OUT_PDF)
    print(OUT_SVG)


if __name__ == "__main__":
    make_figure()
