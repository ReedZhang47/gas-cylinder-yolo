"""Draw Fig. 2: provenance and the two generative-data workflows.

The photographs are embedded from archived PPT source extracts. All diagrams
and type remain vector/editable in the SVG.
"""

from __future__ import annotations

import base64
import html
import math
from io import BytesIO
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


HERE = Path(__file__).resolve().parent
SOURCE_PHOTOS = (HERE / "source_real93_a.jpg", HERE / "source_real93_b.jpg")
OUT_PDF = HERE / "fig2_generation_workflows.pdf"
OUT_SVG = HERE / "generation_workflows_v5.svg"
W, H = 720, 470

INK = "#1B3448"
MUTED = "#566C7D"
LINE = "#9EB3C1"
BLUE = "#426F96"
TEAL = "#178A93"
PURPLE = "#755CAD"


def register_fonts() -> tuple[str, str]:
    font_dir = Path(r"C:\Windows\Fonts")
    regular, bold = font_dir / "arial.ttf", font_dir / "arialbd.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Fig2Arial", str(regular)))
        pdfmetrics.registerFont(TTFont("Fig2ArialBold", str(bold)))
        return "Fig2Arial", "Fig2ArialBold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


def source_photo(index: int) -> bytes:
    """Read a print-resolution JPEG extracted from the archived source deck."""
    return SOURCE_PHOTOS[index].read_bytes()


class Figure:
    def __init__(self) -> None:
        self.pdf = canvas.Canvas(str(OUT_PDF), pagesize=(W, H), pageCompression=1)
        self.pdf.setTitle("Data provenance and generative workflows")
        self.pdf.setAuthor("Gas Cylinder Safety Detection project")
        self.svg: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" '
            f'viewBox="0 0 {W} {H}" role="img" '
            'aria-label="Common image source, C image-editing workflow, and D LoRA text-to-image workflow">',
            f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>',
        ]

    def box(
        self, x: float, y: float, w: float, h: float, *,
        fill: str = "#ffffff", stroke: str = LINE, radius: float = 7,
        width: float = 1.0, dashed: bool = False,
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
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'rx="{radius:g}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{width:g}"{dash}/>'
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
        self, x: float, y: float, value: str, *, size: float = 11.5,
        color: str = INK, bold: bool = False, align: str = "left",
        max_width: float | None = None,
    ) -> None:
        font = FONT_BOLD if bold else FONT
        measured = pdfmetrics.stringWidth(value, font, size)
        if max_width is not None and measured > max_width + 0.2:
            raise ValueError(f"Text exceeds box ({measured:.1f}>{max_width}): {value}")
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
            f'<text x="{x:g}" y="{y:g}" dominant-baseline="middle" '
            f'text-anchor="{anchor}" font-family="Arial, Helvetica, sans-serif" '
            f'font-size="{size:g}" font-weight="{weight}" fill="{color}">'
            f'{html.escape(value)}</text>'
        )

    def line(
        self, points: list[tuple[float, float]], *, color: str = LINE,
        width: float = 1.15, dashed: bool = False, arrow: bool = False,
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

    def photo(self, x: float, y: float, w: float, h: float, jpeg: bytes) -> None:
        self.pdf.drawImage(ImageReader(BytesIO(jpeg)), x, H - y - h,
                           width=w, height=h, mask="auto")
        uri = base64.b64encode(jpeg).decode("ascii")
        self.svg.append(
            f'<image x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'href="data:image/jpeg;base64,{uri}"/>'
        )
        self.pdf.saveState()
        self.pdf.setStrokeColor(HexColor("#9CB1C1"))
        self.pdf.setLineWidth(0.8)
        self.pdf.rect(x, H - y - h, w, h, stroke=1, fill=0)
        self.pdf.restoreState()
        self.svg.append(
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
            'fill="none" stroke="#9CB1C1" stroke-width="0.8"/>'
        )

    def save(self) -> None:
        self.pdf.showPage()
        self.pdf.save()
        self.svg.append("</svg>")
        OUT_SVG.write_text("\n".join(self.svg) + "\n", encoding="utf-8")


def make_figure() -> None:
    f = Figure()

    # A split architecture plate: a photographic seed on the left feeds two
    # separate horizontal mechanisms.  The C instruction and D prompt/LoRA
    # paths merge into their respective model cores, rather than forming a
    # repeated chain of four cards.
    f.text(22, 26, "DATA SYNTHESIS ROUTES", size=16.4,
           bold=True, color=INK)
    f.text(698, 27, "SAME 93-IMAGE ORIGIN", size=10.8,
           color=MUTED, align="right")
    f.line([(22, 47), (698, 47)], color="#C8D6DE", width=0.85)
    f.line([(183, 65), (183, 448)], color="#C7D5DE", width=0.85)
    f.box(202, 66, 496, 164, fill="#F8FCFC", stroke="#E1EBED",
          radius=3, width=0.8)
    f.box(202, 242, 496, 206, fill="#FBF9FD", stroke="#E9E3F0",
          radius=3, width=0.8)

    # Shared source: photographs already present in the author's PPT.
    f.text(26, 82, "real93", size=21.0, bold=True, color=BLUE)
    f.text(26, 103, "93 annotated photos", size=11.5, color=INK)
    f.photo(26, 124, 109, 82, source_photo(0))
    f.photo(46, 178, 109, 82, source_photo(1))
    f.text(26, 278, "on-site examples", size=11.2, color=MUTED)
    f.text(26, 294, "+ web-sourced photos", size=11.2,
           color=MUTED, max_width=150)
    f.line([(26, 323), (158, 323)], color="#B7C9D3", width=0.8)
    f.text(26, 344, "ONE SEED CORPUS", size=10.8, bold=True,
           color=MUTED)
    f.text(26, 367, "C  photo reference", size=11.3,
           bold=True, color=TEAL)
    f.text(26, 388, "D  LoRA supervision", size=11.3,
           bold=True, color=PURPLE)

    # One provenance rail, with separate arrows into the two mechanisms.
    f.line([(155, 223), (183, 223)], color=BLUE, width=1.15)
    f.line([(183, 176), (183, 327)], color=BLUE, width=1.15)
    f.line([(183, 176), (347, 176)], color=TEAL, width=1.2,
           arrow=True)
    f.line([(183, 327), (216, 327)], color=PURPLE, width=1.2,
           arrow=True)

    # C: the instruction and source photograph are distinct conditioning
    # inputs to one image-edit model.  Output is a visual review and label gate.
    f.text(218, 82, "(a)  C  /  IMAGE EDITING", size=14.6,
           bold=True, color=TEAL)
    f.text(682, 82, "COMPLETED", size=10.7,
           bold=True, color=TEAL, align="right")
    f.text(218, 101, "reference scene + target safety state", size=11.3,
           color=MUTED)
    f.box(218, 119, 112, 34, fill="#FFFFFF", stroke="#8CBABD",
          radius=5, width=0.95)
    f.text(274, 132, "EDIT INSTRUCTION", size=10.6,
           bold=True, color=TEAL, align="center", max_width=100)
    f.text(274, 145, "target state", size=10.8,
           color=MUTED, align="center", max_width=100)
    f.line([(274, 153), (274, 161), (347, 161)],
           color=TEAL, width=1.1, arrow=True)
    f.box(350, 117, 158, 91, fill="#FFFFFF", stroke=TEAL,
          radius=4, width=1.25)
    f.box(350, 117, 5, 91, fill=TEAL, stroke=TEAL,
          radius=0.5, width=0.2)
    f.text(364, 138, "Qwen-Image-Edit", size=12.7,
           bold=True, color=INK, max_width=131)
    f.text(364, 155, "2509", size=11.6,
           bold=True, color=TEAL)
    f.text(364, 176, "VL encoder + VAE", size=10.8,
           color=INK, max_width=131)
    f.text(364, 194, "4-step mode available", size=10.9,
           color=MUTED, max_width=131)
    f.line([(508, 162), (529, 162)], color=TEAL,
           width=1.25, arrow=True)
    # Three offset image outlines, then a human-review mark.
    f.box(531, 140, 28, 30, fill="#FFFFFF", stroke="#A3B5BF",
          radius=1, width=0.8)
    f.box(536, 145, 28, 30, fill="#FFFFFF", stroke=TEAL,
          radius=1, width=0.9)
    f.line([(541, 166), (548, 157), (557, 163)], color=TEAL,
           width=0.95)
    f.line([(565, 162), (580, 162)], color=TEAL,
           width=1.2, arrow=True)
    f.circle(597, 162, 16, fill=TEAL)
    f.line([(589, 162), (595, 168), (605, 155)],
           color="#FFFFFF", width=2.0)
    f.text(597, 190, "review", size=11.0,
           color=MUTED, align="center")
    f.line([(613, 162), (632, 162)], color=TEAL,
           width=1.2, arrow=True)
    f.text(687, 153, "1,085", size=20.0, bold=True,
           color=TEAL, align="right", max_width=54)
    f.text(687, 179, "retained", size=11.2,
           color=MUTED, align="right")
    f.text(218, 218, "PHOTO-REFERENCED EDITS", size=10.3,
           bold=True, color=TEAL)

    # D: reviewed captions fed the completed Qwen-Image-2.1 LoRA fit.
    # The screened and annotated dataset is prospective, so the output is dashed.
    f.text(218, 260, "(b)  D  /  LORA TEXT-TO-IMAGE", size=14.4,
           bold=True, color=PURPLE)
    f.text(682, 260, "DATASET PENDING", size=10.6,
           bold=True, color=PURPLE, align="right")
    f.text(218, 280, "fit on real93; synthesize from text", size=11.3,
           color=MUTED)
    f.box(218, 303, 91, 49, fill="#FFFFFF", stroke="#B8A8CF",
          radius=4, width=0.95)
    f.text(263.5, 319, "REVIEWED", size=10.9,
           bold=True, color=PURPLE, align="center", max_width=78)
    f.text(263.5, 338, "93 captions", size=10.7,
           color=MUTED, align="center", max_width=80)
    f.line([(309, 327), (324, 327)], color=PURPLE,
           width=1.2, arrow=True)
    f.box(327, 299, 139, 61, fill="#FFFFFF", stroke=PURPLE,
          radius=4, width=1.2)
    f.box(327, 299, 5, 61, fill=PURPLE, stroke=PURPLE,
          radius=0.5, width=0.2)
    f.text(341, 316, "LoRA training", size=12.4,
           bold=True, color=INK, max_width=116)
    f.text(341, 335, "1,860 steps  ·  r16", size=10.7,
           color=INK, max_width=116)
    f.text(341, 351, "93 imgs  ·  LR 1e-4", size=10.7,
           color=MUTED, max_width=116)
    f.line([(466, 328), (484, 328)], color=PURPLE,
           width=1.2, arrow=True)
    f.circle(499, 328, 14, fill=PURPLE)
    f.text(499, 329, "L", size=11.3, bold=True,
           color="#FFFFFF", align="center")
    f.line([(499, 342), (499, 389), (514, 389)],
           color=PURPLE, width=1.1, arrow=True)
    f.box(218, 386, 112, 34, fill="#FFFFFF", stroke="#B8A8CF",
          radius=14, width=0.95)
    f.text(274, 403, "TEXT PROMPT", size=11.2,
           bold=True, color=PURPLE, align="center", max_width=97)
    f.line([(330, 403), (514, 403)], color=PURPLE,
           width=1.15, arrow=True)
    f.box(517, 369, 101, 60, fill="#FFFFFF", stroke=PURPLE,
          radius=4, width=1.2)
    f.text(567.5, 384, "Qwen-Image", size=11.4,
           bold=True, color=INK, align="center", max_width=92)
    f.text(567.5, 402, "2.1 + LoRA", size=10.9,
           color=PURPLE, align="center", max_width=92)
    f.text(567.5, 418, "sample", size=10.2,
           color=MUTED, align="center", max_width=92)
    f.line([(618, 397), (633, 397)], color=PURPLE,
           width=1.1, dashed=True, arrow=True)
    f.box(636, 370, 61, 57, fill="#FFFFFF", stroke=PURPLE,
          radius=4, width=1.15, dashed=True)
    f.text(666.5, 383, "QC", size=11.2,
           bold=True, color=PURPLE, align="center", max_width=54)
    f.text(666.5, 401, "1,085", size=14.4,
           bold=True, color=PURPLE, align="center", max_width=54)
    f.text(666.5, 418, "target", size=10.9,
           color=MUTED, align="center", max_width=54)
    f.text(218, 438, "LORA FITTING", size=10.9,
           bold=True, color=PURPLE)
    f.text(698, 438, "screening and box review pending", size=10.9,
           color=MUTED, align="right")

    f.save()
    print(OUT_PDF)
    print(OUT_SVG)


if __name__ == "__main__":
    make_figure()
