"""Draw the v5 study pipeline as vector PDF and editable SVG.

The PDF and editable SVG stay beside this
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
OUT_PDF = HERE / "fig1_pipeline.pdf"
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

    def circle(self, x: float, y: float, radius: float, *, fill: str,
               stroke: str | None = None, width: float = 1.0) -> None:
        p = self.pdf
        p.saveState()
        p.setFillColor(HexColor(fill))
        if stroke:
            p.setStrokeColor(HexColor(stroke))
            p.setLineWidth(width)
        p.circle(x, H - y, radius, stroke=int(stroke is not None), fill=1)
        p.restoreState()
        edge = f' stroke="{stroke}" stroke-width="{width:g}"' if stroke else ''
        self.svg.append(
            f'<circle cx="{x:g}" cy="{y:g}" r="{radius:g}" fill="{fill}"{edge}/>'
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

    # An editorial schematic: an open page, shallow arm rails, one dark shared
    # protocol band, and a ruled evaluation summary.  Status is carried by line
    # style as well as colour so it survives greyscale reproduction.
    f.text(24, 24, "STUDY DESIGN", size=17.0, bold=True, color=INK)
    f.text(680, 25, "real93  /  four arms  /  dev61", size=10.8,
           color=MUTED, align="right")
    f.line([(24, 43), (680, 43)], color="#C7D4DC", width=0.85)
    f.text(24, 63, "01   DATA CONSTRUCTION", size=10.9,
           bold=True, color=MUTED)

    # Source block and small photographic glyph.
    f.box(24, 85, 153, 149, fill="#F3F7F9", stroke="#D8E3EA",
          radius=4, width=0.9)
    f.box(125, 105, 26, 19, fill="#FFFFFF", stroke="#9AAEBB",
          radius=1, width=0.9)
    f.box(131, 112, 26, 19, fill="#FFFFFF", stroke="#8099AA",
          radius=1, width=0.9)
    f.line([(136, 125), (142, 119), (148, 124)], color=A, width=1.0)
    f.text(38, 121, "93", size=35.0, bold=True, color=A)
    f.text(39, 153, "REAL PHOTOS", size=11.8, bold=True, color=INK)
    f.text(39, 170, "annotated seed set", size=10.8, color=MUTED)
    f.line([(39, 185), (160, 185)], color="#B8C8D2", width=0.8)
    f.text(39, 208, "real93", size=14.0, bold=True, color=INK)
    f.text(39, 224, "shared origin", size=10.6, color=MUTED)

    # Four parallel data arms.  The open rails make the count comparison the
    # visual focus; the dashed D rail encodes prospective status.
    f.line([(177, 158), (198, 158)], color=A, width=1.15)
    f.line([(198, 104), (198, 215)], color=A, width=1.15)
    arms = [
        (86, A, "A", "Real-only baseline", "manual labels", "93", False),
        (123, B, "B", "Offline augmentation", "geometry and colour", "1,085", False),
        (160, C, "C", "Image editing", "human-reviewed boxes", "1,085", False),
        (197, D, "D", "LoRA text-to-image", "formal dataset pending", "1,085 target", True),
    ]
    for y, accent, letter, title, detail, count, pending in arms:
        f.line([(198, y + 17.5), (215, y + 17.5)], color=accent,
               dashed=pending, arrow=True)
        f.box(215, y, 465, 35, fill="#FFFFFF", stroke=accent if pending else "#DBE5EB",
              radius=2, width=1.0 if pending else 0.75, dashed=pending)
        f.circle(232, y + 17.5, 10.0, fill=accent)
        f.text(232, y + 18.2, letter, size=11.1, bold=True, color="#FFFFFF",
               align="center")
        f.text(251, y + 12, title, size=12.5, bold=True, color=INK,
               max_width=250)
        f.text(251, y + 27, detail, size=11.0, color=MUTED,
               max_width=250)
        f.text(667, y + 18.7, count, size=12.9 if pending else 15.2,
               bold=True, color=accent, align="right", max_width=100)

    f.line([(352, 234), (352, 266)], color=TRAIN, width=1.25, arrow=True)
    f.text(365, 250, "independent run per arm", size=11.0,
           color=MUTED, max_width=190)

    # High-contrast central band is the figure's shared-protocol anchor.
    f.box(24, 269, 656, 68, fill="#203746", stroke="#203746",
          radius=4, width=0.6)
    f.text(40, 285, "02   CONTROLLED TRAINING", size=10.8,
           bold=True, color="#C3DCE0")
    f.text(40, 315, "Six YOLO detectors  /  300 epochs", size=16.7,
           bold=True, color="#FFFFFF", max_width=425)
    for x, h in ((492, 18), (500, 24), (508, 16), (516, 27), (524, 21), (532, 30)):
        f.box(x, 321 - h, 4, h, fill="#86BCC2", stroke="#86BCC2",
              radius=0.6, width=0.2)
    f.text(665, 297, "v8  /  v11  /  v26", size=11.3,
           bold=True, color="#FFFFFF", align="right", max_width=121)
    f.text(665, 316, "s, m  ·  save /10", size=10.8,
           color="#D4E2E7", align="right", max_width=121)

    # Development-only analysis is rendered as a ruled three-column readout,
    # rather than as another row of cards.
    f.text(24, 358, "03   DEVELOPMENT EVALUATION", size=10.9,
           bold=True, color=MUTED)
    f.box(507, 345, 173, 25, fill="#F1F5F7", stroke=DEV,
          radius=12, width=0.9, dashed=True)
    f.text(593.5, 358, "dev61  ·  61 external images", size=10.6,
           color=INK, align="center", max_width=157)
    f.line([(352, 337), (352, 381)], color=TRAIN, width=1.15,
           arrow=True)
    f.line([(593.5, 370), (593.5, 381)], color=DEV,
           width=0.9, dashed=True)
    f.line([(24, 383), (680, 383)], color="#B9CAD4", width=0.85)
    f.line([(242, 391), (242, 431)], color="#D1DDE4", width=0.8)
    f.line([(461, 391), (461, 431)], color="#D1DDE4", width=0.8)
    reports = [
        (34, "Fixed endpoint", "last.pt on dev61", "transparent benchmark"),
        (253, "Cross-fitted OOF", "five held-out folds; pooled AP", "joint model + checkpoint"),
        (472, "Deployment choice", "selected on all dev61", "development score only"),
    ]
    for x, title, line1, line2 in reports:
        f.text(x, 399, title, size=12.5, bold=True, color=INK,
               max_width=204)
        f.text(x, 416, line1, size=11.1, color=INK,
               max_width=204)
        f.text(x, 431, line2, size=10.9, color=MUTED,
               max_width=204)
    f.text(352, 443, "Paired image-cluster bootstrap  ·  10,000 resamples",
           size=11.0, color=MUTED, align="center", max_width=650)

    f.save()
    print(OUT_PDF)
    print(OUT_SVG)


if __name__ == "__main__":
    make_figure()
