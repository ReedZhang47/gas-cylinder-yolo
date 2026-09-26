"""Fig. 3: actual A/B/C training-image examples with the D column reserved.

A and B are row-matched: each B image is an image in the completed aug1085
training pool derived from the A photograph beside it.  The C samples are
independent reviewed edits of other real93 sources, not edits of the A photos
on the same row.  All images are embedded in the PDF and SVG.
"""

from __future__ import annotations

import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image, ImageOps


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GAS = Path(r"D:\gas_cylinders")
A_DIR = GAS / "real_photo" / "93_real_photos"
B_DIR = GAS / "aug1085"
C_DIRS = [GAS / "Placement_Issues", GAS / "Placement_Issues_2"]
OUT_PDF = HERE / "fig3_training_examples.pdf"
OUT_SVG = HERE / "training_examples_abc.svg"

SEED_NUMBERS = [30, 50, 70]
B_RANKS = [1, 3, 2]  # zero-based rank among the retained B variants for each seed
C_NAMES = ["Placement_Issues_0001.png", "Placement_Issues_0554.png",
           "Placement_Issues_0515.png"]
COLORS = ["#426F96", "#B88232", "#178A93", "#755CAD"]
INK, MUTED, LINE = "#1B3448", "#566C7D", "#D2DFE6"
LABEL = "#D72F42"

plt.rcParams.update({"font.family": "Arial", "pdf.fonttype": 42,
                     "ps.fonttype": 42, "svg.fonttype": "none",
                     "savefig.facecolor": "white"})


def source_mapping() -> dict[str, list[Path]]:
    """Reconstruct the documented trim/order without rewriting the B dataset."""
    originals = sorted((A_DIR / "images").glob("*.png"))
    assert len(originals) == 93
    dropped = set(random.Random(42).sample(range(93 * 12), 93 * 12 - 1085))
    mapped: dict[str, list[Path]] = {p.stem: [] for p in originals}
    kept = 0
    for pool_index in range(93 * 12):
        source = originals[pool_index // 12].stem
        if pool_index not in dropped:
            path = B_DIR / "images" / f"aug1085_{kept:04d}.png"
            assert path.exists(), path
            mapped[source].append(path)
            kept += 1
    assert kept == 1085 and all(10 <= len(paths) <= 12 for paths in mapped.values())
    return mapped


def c_path(name: str) -> Path:
    for root in C_DIRS:
        candidate = root / "images" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


def labels(path: Path) -> list[list[float]]:
    label_path = path.parent.parent / "labels" / f"{path.stem}.txt"
    assert label_path.exists(), label_path
    rows = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        tokens = line.split()
        assert len(tokens) == 5
        rows.append([float(v) for v in tokens[1:]])
    return rows


def tile(ax, path: Path) -> None:
    target_w, target_h = 480, 290
    with Image.open(path) as handle:
        image = ImageOps.contain(handle.convert("RGB"), (target_w, target_h),
                                 method=Image.Resampling.LANCZOS)
    sheet = Image.new("RGB", (target_w, target_h), "#F6F8F9")
    offset_x = (target_w - image.width) // 2
    offset_y = (target_h - image.height) // 2
    sheet.paste(image, (offset_x, offset_y))
    ax.imshow(sheet)
    ax.set_xlim(0, target_w)
    ax.set_ylim(target_h, 0)
    ax.set_axis_off()
    for cx, cy, width, height in labels(path):
        x = offset_x + (cx - width / 2) * image.width
        y = offset_y + (cy - height / 2) * image.height
        w, h = width * image.width, height * image.height
        if w <= 0 or h <= 0:
            continue
        for color, linewidth in (("white", 4.6), (LABEL, 2.6)):
            ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor=color,
                                   linewidth=linewidth, clip_on=True))
    ax.add_patch(Rectangle((0, 0), target_w, target_h, fill=False,
                           edgecolor=LINE, linewidth=1.2))


def blank_tile(ax) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                           facecolor="#FBF9FE", edgecolor="#AA98CA",
                           linewidth=1.3, linestyle=(0, (5, 3))))
    ax.text(.5, .5, "D SAMPLE\nRESERVED", ha="center", va="center",
            color=COLORS[3], fontsize=10.5, weight="bold", linespacing=1.45)


def build() -> None:
    mapped = source_mapping()
    train_list = (ROOT / "scripts" / "splits_gen1085" /
                  "gen1085_full_train.txt").read_text(encoding="utf-8")
    c_images = [c_path(name) for name in C_NAMES]
    assert all(str(path).replace("\\", "/") in train_list for path in c_images)
    fig = plt.figure(figsize=(10.0, 7.0), facecolor="white")
    fig.text(.035, .959, "TRAINING IMAGES BY DATA ARM", fontsize=17,
             color=INK, weight="bold")
    fig.text(.965, .962, "A -> B matched by source  /  C independent  /  D reserved",
             ha="right", fontsize=10.4, color=MUTED)
    fig.add_artist(plt.Line2D([.035, .965], [.934, .934], color=LINE,
                              linewidth=.9, transform=fig.transFigure))

    xs = [.035, .273, .511, .749]
    w = .216
    heads = ["A   REAL PHOTO", "B   CLASSICAL AUGMENT", "C   IMAGE EDIT",
             "D   LORA TEXT-TO-IMAGE"]
    for col, (x, title) in enumerate(zip(xs, heads)):
        fig.add_artist(plt.Line2D([x, x + w], [.895, .895], color=COLORS[col],
                                  linewidth=3.0, transform=fig.transFigure))
        fig.text(x, .909, title, fontsize=10.6, color=COLORS[col], weight="bold",
                 va="bottom")

    ys = [.655, .415, .175]
    h = .205
    for row, (seed, rank, c_image) in enumerate(zip(SEED_NUMBERS, B_RANKS, c_images)):
        a = A_DIR / "images" / f"real_photo_{seed}.png"
        b = mapped[a.stem][rank]
        paths = [a, b, c_image]
        for col, path in enumerate(paths):
            ax = fig.add_axes([xs[col], ys[row], w, h])
            tile(ax, path)
            fig.text(xs[col], ys[row] - .022, path.stem, fontsize=9.35,
                     color=MUTED, va="top")
        ax = fig.add_axes([xs[3], ys[row], w, h])
        blank_tile(ax)

    fig.add_artist(plt.Line2D([.035, .965], [.095, .095], color=LINE,
                              linewidth=.9, transform=fig.transFigure))
    fig.text(.035, .063,
             "Red outlines are reviewed training labels. Each A-B row shares a real source; "
             "C examples are edits of other real93 seeds and are not row-matched.",
             fontsize=9.7, color=MUTED)
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_SVG)
    plt.close(fig)


if __name__ == "__main__":
    build()
