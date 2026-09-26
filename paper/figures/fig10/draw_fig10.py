"""Fig. 10: vector detection overlays on three pinned dev61 photographs.

The images, GT, and A/B/C predictions are real project evidence.  The D column
is blank.  The figure deliberately illustrates cases and does not estimate
their prevalence; numerical evidence belongs in the result figures.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.patches import Rectangle
from PIL import Image, ImageOps


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / "experiments" / "v4_protocol" / "qualitative_detections.json"
OUT_PDF = HERE / "fig10_detection_cases.pdf"
OUT_SVG = HERE / "detection_cases_abc.svg"

CASES = [
    ("new_test_set_0014.jpg", "Fallen cylinder: C detects one labelled object", 2,
     {"real93v4": 1, "aug1085v4": 0, "gen1085v4": 1}),
    ("new_test_set_0006.jpg", "Empty-label image: A fires, B and C remain silent", 0,
     {"real93v4": 1, "aug1085v4": 0, "gen1085v4": 0}),
    ("new_test_set_0005.jpg", "One label: A fires twice; B and C fire once", 1,
     {"real93v4": 2, "aug1085v4": 1, "gen1085v4": 1}),
]
ARMS = [("real93v4", "A  REAL93", "#426F96"),
        ("aug1085v4", "B  AUGMENTED", "#B88232"),
        ("gen1085v4", "C  IMAGE EDIT", "#178A93")]
INK, MUTED, LINE, D_COLOR = "#1B3448", "#566C7D", "#D2DFE6", "#755CAD"

plt.rcParams.update({"font.family": "Arial", "pdf.fonttype": 42,
                     "ps.fonttype": 42, "svg.fonttype": "none",
                     "savefig.facecolor": "white"})


def gt_boxes(image_path: Path, width: int, height: int) -> list[tuple[float, ...]]:
    label_path = image_path.parent.parent / "labels" / f"{image_path.stem}.txt"
    assert label_path.exists(), label_path
    boxes = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        values = line.split()
        assert len(values) == 5 and int(values[0]) == 0
        cx, cy, w, h = map(float, values[1:])
        boxes.append(((cx - w / 2) * width, (cy - h / 2) * height,
                      (cx + w / 2) * width, (cy + h / 2) * height))
    return boxes


def prepared_image(path: Path):
    target_w, target_h = 430, 460
    with Image.open(path) as handle:
        original_w, original_h = handle.size
        contained = ImageOps.contain(handle.convert("RGB"), (target_w, target_h),
                                      method=Image.Resampling.LANCZOS)
    output = Image.new("RGB", (target_w, target_h), "#F4F7F9")
    xoff = (target_w - contained.width) // 2
    yoff = (target_h - contained.height) // 2
    output.paste(contained, (xoff, yoff))
    sx, sy = contained.width / original_w, contained.height / original_h
    return output, (xoff, yoff, sx, sy), (original_w, original_h)


def transformed(box, transform):
    xoff, yoff, sx, sy = transform
    x1, y1, x2, y2 = box
    return xoff + x1 * sx, yoff + y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy


def tile(ax, image, transform, boxes, *, color: str | None,
         is_ground_truth: bool) -> None:
    ax.imshow(image)
    ax.set_xlim(0, 430)
    ax.set_ylim(460, 0)
    ax.axis("off")
    for box, confidence in boxes:
        x, y, width, height = transformed(box, transform)
        if width <= 0 or height <= 0:
            continue
        if is_ground_truth:
            # Dark relief below white dashes remains visible on both concrete and soil.
            ax.add_patch(Rectangle((x, y), width, height, fill=False,
                                   edgecolor="#273845", linewidth=4.5))
            ax.add_patch(Rectangle((x, y), width, height, fill=False,
                                   edgecolor="white", linewidth=2.7,
                                   linestyle=(0, (4, 2))))
        else:
            ax.add_patch(Rectangle((x, y), width, height, fill=False,
                                   edgecolor="white", linewidth=5.0))
            ax.add_patch(Rectangle((x, y), width, height, fill=False,
                                   edgecolor=color, linewidth=3.0))
            ty = y - 5 if y > 21 else y + 20
            label = ax.text(x + 4, ty, f"{confidence:.2f}", color=color,
                            fontsize=9.8, weight="bold", va="center", ha="left",
                            bbox={"facecolor": "white", "edgecolor": "none",
                                  "boxstyle": "round,pad=0.15"})
            label.set_path_effects([patheffects.Normal()])
    ax.add_patch(Rectangle((0, 0), 430, 460, fill=False,
                           edgecolor=LINE, linewidth=1.0))


def blank(ax) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                           facecolor="#FBF9FE", edgecolor="#AA98CA",
                           linewidth=1.2, linestyle=(0, (5, 3))))
    ax.text(.5, .5, "D OUTPUT\nRESERVED", ha="center", va="center",
            color=D_COLOR, fontsize=10.4, weight="bold", linespacing=1.4)


def build() -> None:
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    assert cache["conf_floor"] <= .25 and cache["imgsz"] == 640
    expected_epochs = {"real93v4": "epoch280.pt", "aug1085v4": "epoch200.pt",
                       "gen1085v4": "epoch260.pt"}
    for arm, suffix in expected_epochs.items():
        assert cache["weights"][arm].endswith(suffix)

    fig = plt.figure(figsize=(10.0, 7.25), facecolor="white")
    fig.text(.032, .963, "DETECTION CASES ON DEV61", fontsize=17,
             color=INK, weight="bold")
    fig.text(.968, .966, "illustrative cases  /  confidence >= 0.25",
             fontsize=10.5, color=MUTED, ha="right")
    fig.add_artist(plt.Line2D([.032, .968], [.939, .939], color=LINE,
                              lw=.9, transform=fig.transFigure))

    heads = [("REVIEWED GT", MUTED)] + [(name, color) for _, name, color in ARMS] + [
        ("D  LORA T2I", D_COLOR)]
    xs = [.032, .222, .412, .602, .792]
    w = .176
    for (name, color), x in zip(heads, xs):
        fig.add_artist(plt.Line2D([x, x + w], [.902, .902], color=color,
                                  lw=2.7, transform=fig.transFigure))
        fig.text(x, .912, name, fontsize=10.5, weight="bold", color=color,
                 va="bottom")

    ys = [.660, .426, .192]
    h = .185
    for row, (name, outcome, gt_count, expected_counts) in enumerate(CASES):
        entry = cache["images"][name]
        image_path = Path(entry["path"])
        image, transform, original_size = prepared_image(image_path)
        gt = gt_boxes(image_path, *original_size)
        assert len(gt) == gt_count
        fig.text(.032, ys[row] + h + .024,
                 f"({chr(97 + row)})  {outcome}", fontsize=11.3,
                 color=INK, weight="bold", va="bottom")
        fig.text(.968, ys[row] + h + .024, name.removesuffix(".jpg"),
                 fontsize=8.7, color=MUTED, va="bottom", ha="right")
        ax = fig.add_axes([xs[0], ys[row], w, h])
        tile(ax, image, transform, [(box, None) for box in gt],
             color=None, is_ground_truth=True)
        for col, (arm, _, color) in enumerate(ARMS, start=1):
            detections = [d for d in entry["arms"][arm] if d["conf"] >= .25]
            assert len(detections) == expected_counts[arm], (name, arm)
            rows = [(d["xyxy"], d["conf"]) for d in detections]
            ax = fig.add_axes([xs[col], ys[row], w, h])
            tile(ax, image, transform, rows, color=color, is_ground_truth=False)
        ax = fig.add_axes([xs[4], ys[row], w, h])
        blank(ax)

    fig.add_artist(plt.Line2D([.032, .968], [.114, .114], color=LINE,
                              lw=.9, transform=fig.transFigure))
    fig.text(.032, .077,
             "White dashed = reviewed label; coloured solid = prediction with confidence. "
             "Cases are hand-selected illustrations, not frequency estimates.",
             fontsize=9.8, color=MUTED)
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_SVG)
    plt.close(fig)


if __name__ == "__main__":
    build()
