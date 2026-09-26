"""Draw Fig. 5 from the v4 fixed-endpoint detector results.

The two matrices share one AP colour scale.  Arm D is an intentionally empty
fourth row; no D result is inferred or copied from another arm.  The vector PDF
and editable SVG are generated from the same drawing calls.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULTS = ROOT / "experiments" / "v4_protocol"
OUT_PDF = HERE / "fig5_detector_consistency.pdf"
OUT_SVG = HERE / "detector_consistency_abc.svg"

W, H = 720, 380
INK = "#1B3448"
MUTED = "#566C7D"
RULE = "#C8D5DD"
PALE = "#F3F8FA"
DEEP = "#033A4A"
ARM_COLORS = {"A": "#426F96", "B": "#B88232", "C": "#178A93", "D": "#755CAD"}
ARMS = [
    ("A", "Real 93", "real93v4", "v4_protocol_real93v4.json", 93),
    ("B", "Augmented 1085", "aug1085v4", "v4_protocol_aug1085v4.json", 1085),
    ("C", "Image-edit 1085", "gen1085v4", "v4_protocol_gen1085v4.json", 1085),
    ("D", "LoRA T2I", None, None, None),  # fill only after the D protocol result is verified
]
DETECTORS = [
    ("yolov8s", "v8s"), ("yolov8m", "v8m"),
    ("yolo11s", "11s"), ("yolo11m", "11m"),
    ("yolo26s", "26s"), ("yolo26m", "26m"),
]
METRICS = [("mAP50-95", "PRIMARY ENDPOINT"), ("mAP50", "SECONDARY ENDPOINT")]


def fonts() -> tuple[str, str]:
    font_dir = Path(r"C:\Windows\Fonts")
    regular, bold = font_dir / "arial.ttf", font_dir / "arialbd.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Fig5Arial", str(regular)))
        pdfmetrics.registerFont(TTFont("Fig5ArialBold", str(bold)))
        return "Fig5Arial", "Fig5ArialBold"
    return "Helvetica", "Helvetica-Bold"


FONT, BOLD = fonts()


def rgb(color: str) -> tuple[int, int, int]:
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def blend(low: str, high: str, amount: float) -> str:
    a, b = rgb(low), rgb(high)
    return "#" + "".join(f"{round(x * (1 - amount) + y * amount):02X}" for x, y in zip(a, b))


def shade(value: float) -> str:
    # A fixed 0..1 scale is used in both matrices, including the future D row.
    # This curve keeps both sides of the 0.50 label switch legible.
    return blend(PALE, DEEP, value ** 0.60)


def relative_luminance(color: str) -> float:
    channels = []
    for raw in rgb(color):
        s = raw / 255.0
        channels.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def number_color(value: float) -> str:
    # Classify the number as printed, so a rounded "0.500" is always white.
    printed_value = float(f"{value:.3f}")
    return "#FFFFFF" if printed_value >= 0.50 else "#000000"


def contrast_ratio(foreground: str, background: str) -> float:
    light, dark = sorted(
        (relative_luminance(foreground), relative_luminance(background)),
        reverse=True,
    )
    return (light + 0.05) / (dark + 0.05)


def load_values() -> dict[str, dict[str, dict[str, float]]]:
    values: dict[str, dict[str, dict[str, float]]] = {}
    reference_folds = None
    for letter, _, key, filename, count in ARMS:
        if filename is None:
            assert key is None and count is None
            continue
        source = json.loads((RESULTS / filename).read_text(encoding="utf-8"))
        assert source["protocol"]["version"] in {"v4", "v5"}, filename
        if letter != "D":
            assert source["protocol"]["version"] == "v4", filename
        assert "dev61" in source["protocol"]["development_set"], filename
        folds = source["protocol"]["folds"]
        if reference_folds is None:
            reference_folds = folds
        else:
            assert folds == reference_folds, f"Different dev61 folds: {filename}"
        arm = source["arms"][key]
        assert arm["train_images"] == count, filename
        assert set(arm["detectors"]) == {name for name, _ in DETECTORS}, filename
        values[letter] = {}
        for name, _ in DETECTORS:
            fixed = arm["detectors"][name]["fixed_endpoint"]
            assert fixed["epoch"] == 300, (filename, name)
            pair = {metric: fixed["metrics"][metric] for metric, _ in METRICS}
            assert all(0 <= value <= 1 for value in pair.values()), (filename, name)
            values[letter][name] = pair
    return values


class Figure:
    def __init__(self) -> None:
        self.pdf = canvas.Canvas(str(OUT_PDF), pagesize=(W, H), pageCompression=1)
        self.pdf.setTitle("Detector-wise fixed-endpoint performance")
        self.pdf.setAuthor("Gas Cylinder Safety Detection project")
        self.svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" '
            f'viewBox="0 0 {W} {H}" role="img" '
            'aria-label="Fixed-endpoint mAP for six detectors, A B C arms, and blank D row">',
            f'<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>',
        ]

    def rect(self, x: float, y: float, width: float, height: float, *,
             fill: str, stroke: str | None = None, radius: float = 0,
             stroke_width: float = 0.8, dashed: bool = False) -> None:
        p = self.pdf
        p.saveState()
        p.setFillColor(HexColor(fill))
        if stroke:
            p.setStrokeColor(HexColor(stroke))
            p.setLineWidth(stroke_width)
            if dashed:
                p.setDash(3.5, 2.5)
        p.roundRect(x, H - y - height, width, height, radius,
                    stroke=int(stroke is not None), fill=1)
        p.restoreState()
        dash = ' stroke-dasharray="3.5 2.5"' if dashed else ""
        edge = (f' stroke="{stroke}" stroke-width="{stroke_width:g}"{dash}'
                if stroke else "")
        self.svg.append(
            f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
            f'rx="{radius:g}" fill="{fill}"{edge}/>'
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, *,
             color: str = RULE, width: float = 0.8) -> None:
        self.pdf.saveState()
        self.pdf.setStrokeColor(HexColor(color))
        self.pdf.setLineWidth(width)
        self.pdf.line(x1, H - y1, x2, H - y2)
        self.pdf.restoreState()
        self.svg.append(
            f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
            f'stroke="{color}" stroke-width="{width:g}"/>'
        )

    def text(self, x: float, y: float, value: str, *, size: float,
             color: str = INK, bold: bool = False, align: str = "left",
             max_width: float | None = None) -> None:
        font = BOLD if bold else FONT
        actual = pdfmetrics.stringWidth(value, font, size)
        if max_width is not None and actual > max_width + 0.1:
            raise ValueError(f"Text overflow ({actual:.1f}>{max_width}): {value}")
        p = self.pdf
        p.saveState()
        p.setFillColor(HexColor(color))
        p.setFont(font, size)
        baseline = H - y - size * 0.80
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
            f'<text x="{x:g}" y="{y + size * 0.80:g}" text-anchor="{anchor}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{size:g}" '
            f'font-weight="{weight}" fill="{color}">{html.escape(value)}</text>'
        )

    def save(self) -> None:
        self.pdf.showPage()
        self.pdf.save()
        self.svg.append("</svg>")
        OUT_SVG.write_text("\n".join(self.svg) + "\n", encoding="utf-8")


def draw() -> None:
    values = load_values()
    for value in (0.499, 0.50):
        assert contrast_ratio(number_color(value), shade(value)) >= 4.5
    fig = Figure()
    fig.text(28, 21, "DETECTOR-WISE PERFORMANCE", size=17.0, bold=True)
    fig.text(692, 25, "fixed endpoint  /  epoch 300  /  dev61 (n = 61)",
             size=10.4, color=MUTED, align="right")
    fig.line(28, 47, 692, 47)

    panels = [("mAP50-95", 168), ("mAP50", 442)]
    cell_width, cell_gap, cell_height = 39.0, 3.0, 42.0
    row_y = [130, 178, 226, 274]

    for index, (metric, panel_x) in enumerate(panels):
        panel_width = 6 * cell_width + 5 * cell_gap
        fig.text(panel_x, 65, f"({chr(97 + index)})  {metric}", size=14.0, bold=True)
        fig.text(panel_x + panel_width, 68, METRICS[index][1], size=10.2,
                 color=MUTED, align="right")
        fig.line(panel_x, 91, panel_x + panel_width, 91, color="#9EB3C1")
        for column, (_, short_name) in enumerate(DETECTORS):
            cx = panel_x + column * (cell_width + cell_gap) + cell_width / 2
            fig.text(cx, 103, short_name, size=10.9, color=MUTED,
                     bold=True, align="center")
        for row, (letter, _, _, _, _) in enumerate(ARMS):
            for column, (name, _) in enumerate(DETECTORS):
                x = panel_x + column * (cell_width + cell_gap)
                y = row_y[row]
                if letter not in values:
                    fig.rect(x, y, cell_width, cell_height, fill="#FCFBFE",
                             stroke="#B7A7D1", radius=3.2, dashed=True)
                    continue
                value = values[letter][name][metric]
                fill = shade(value)
                assert contrast_ratio(number_color(value), fill) >= 4.5
                fig.rect(x, y, cell_width, cell_height, fill=fill,
                         stroke="#D2E0E4", radius=3.2)
                fig.text(x + cell_width / 2, y + 13.0, f"{value:.3f}",
                         size=11.2, color=number_color(value), bold=True,
                         align="center", max_width=cell_width - 3)
    for row, (letter, label, _, _, _) in enumerate(ARMS):
        y = row_y[row]
        fig.rect(28, y + 4, 4.2, cell_height - 8,
                 fill=ARM_COLORS[letter], radius=2.1)
        fig.text(42, y + 12, letter, size=12.4, bold=True,
                 color=ARM_COLORS[letter])
        fig.text(60, y + 13, label, size=10.9, bold=True,
                 max_width=104)
    fig.line(28, 329, 692, 329)
    fig.text(28, 343, "AP scale", size=10.2, color=MUTED, bold=True)
    for step in range(40):
        fig.rect(88 + 2.7 * step, 343, 2.7, 10.0,
                 fill=shade(step / 39))
    fig.text(84, 356, "0", size=10.0, color=MUTED, align="right")
    fig.text(200, 356, "1", size=10.0, color=MUTED)
    fig.text(237, 344, "D cells are intentionally empty until validated results are available.",
             size=10.3, color=MUTED, max_width=455)
    fig.save()


if __name__ == "__main__":
    draw()
