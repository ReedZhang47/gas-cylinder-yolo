r"""Paper figures, rebuilt from experiments/ JSON so no number is hand-copied into the tex.

  selection-curve : checkpoint-selection curves (Fig. 3); one row per arm, one column per detector
  bootstrap-ci    : interval plot of the arm contrasts with paired-bootstrap CIs (Fig. 4)
  arms-samples    : qualitative A/B/C sample comparison (Fig. 2)
  detections      : qualitative dev61 predictions, ground truth next to the three deployment models
  tab-selection   : checkpoint-selection table (arm A)
  tab-main        : three-arm main table, both metrics

All write into paper/figures/ or paper/tables/. `--png PATH` additionally writes a raster
copy, which is handy for eyeballing the result in a viewer that does not render PDF.

Usage:
  python paper/make_figures.py --fig selection-curve
  python paper/make_figures.py --fig selection-curve --png $TEMP/fig3.png
  python paper/make_figures.py --fig bootstrap-ci --png $TEMP/fig4.png
  python paper/make_figures.py --fig arms-samples
  python paper/make_figures.py --fig detections --png $TEMP/fig5.png
  python paper/make_figures.py --fig detections --refresh --png $TEMP/fig5.png

Colours are the validated categorical slots 1-3 of the dataviz skill palette (the first
three that clear its all-pairs CVD gate): blue #2a78d6, orange #eb6834, aqua #1baf7a. Aqua
measures below 3:1 against the light surface, so the skill's relief rule applies - every
figure using it ships visible labels and a table twin.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from PIL import Image

ROOT = Path(r"D:/yolo")
FIG_DIR = ROOT / "paper" / "figures"
TABLE_DIR = ROOT / "paper" / "tables"
SCRIPTS = ROOT / "scripts"
V4_JSON = ROOT / "experiments" / "v4_protocol" / "v4_protocol_real93v4.json"  # cited by the tex figure it backs
BOOTSTRAP_JSON = ROOT / "experiments" / "v4_protocol" / "bootstrap_paired.json"
SEED_IMAGES = Path(r"D:/gas_cylinders/real_photo/93_real_photos/images")
GEN_DIRS = [Path(r"D:/gas_cylinders/Placement_Issues/images"),
            Path(r"D:/gas_cylinders/Placement_Issues_2/images")]
WEIGHTS = ["yolov8s", "yolov8m", "yolo11s", "yolo11m", "yolo26s", "yolo26m"]
METRIC = "mAP50-95"

# Arm identity: fixed slot order, never reassigned by rank or by which arm leads.
ARM_ORDER = ["real93v4", "aug1085v4", "gen1085v4"]
ARM_SHORT = {"real93v4": "A", "aug1085v4": "B", "gen1085v4": "C"}
ARM_DESC = {"real93v4": "93 real photos",
            "aug1085v4": "1085 classical-augmented",
            "gen1085v4": "1085 edited"}
ARM_COLOR = {"real93v4": "#2a78d6", "aug1085v4": "#eb6834", "gen1085v4": "#1baf7a"}
# Contrasts shown by the CI figure, in the order the reader meets them, each keyed as stored
# in bootstrap_paired.json (arm_a, arm_b) with the delta defined as arm_b - arm_a. Each keeps
# its own hue so a reader who learned "C-A is blue" is not misled if a contrast drops out.
PAIR_ORDER = [("real93v4", "gen1085v4"), ("aug1085v4", "gen1085v4"), ("real93v4", "aug1085v4")]
PAIR_COLOR = {("real93v4", "gen1085v4"): "#2a78d6",
              ("aug1085v4", "gen1085v4"): "#eb6834",
              ("real93v4", "aug1085v4"): "#1baf7a"}

# Chart chrome (dataviz palette, light surface).
INK = {"text": "#0b0b0b", "secondary": "#52514e", "muted": "#898781",
       "grid": "#e1e0d9", "axis": "#c3c2b7", "surface": "#fcfcfb"}
FLAG_COLOR = "#d03b3b"  # status "critical"; always paired with the dagger glyph, never alone

# The seed photo and generated samples used by the committed Fig. 2. Chosen by hand for a
# legible violation (a cylinder lying on the ground among rebar) and pinned here so re-running
# the script without arguments reproduces the figure exactly; --seed-photo and --generated
# override them.
DEFAULT_SEED_PHOTO = "real_photo_30"
DEFAULT_GENERATED = ["Placement_Issues_0001.png", "Placement_Issues_0554.png",
                     "Placement_Issues_0515.png"]

# Qualitative detection figure (Fig. 5): the deployment checkpoint of each arm - the arm-level
# detector+checkpoint joint selection recorded in PROGRESS.md, which landed on yolo26s for all
# three arms - inferred on the same development images.
DEV_LIST_V4 = Path(r"D:/gas_cylinders/v4/dev61.txt")
DEPLOY = {"real93v4": ("yolo26s", 280), "aug1085v4": ("yolo26s", 200), "gen1085v4": ("yolo26s", 260)}
DET_CACHE = ROOT / "experiments" / "v4_protocol" / "qualitative_detections.json"
DET_CONF = 0.25  # Ultralytics predict default; the caption states it
DET_IMGSZ = 640
DET_GT_COLOR = "lime"
# Hand-picked panels, pinned so a re-run reproduces the figure. Each row shows one outcome and
# the four columns are the same image, left to right: the reviewed label and each arm's
# deployment model. The second element is the outcome the row is there to show.
DET_ROWS = [
    ("new_test_set_0012.jpg", "every arm finds all three cylinders"),
    ("new_test_set_0014.jpg", "only C finds the fallen cylinder"),
    ("new_test_set_0010.jpg", "C is exact, A over-fires, B is blind"),
    ("new_test_set_0055.jpg", "no arm finds it"),
]
DET_IMAGES = [name for name, _ in DET_ROWS]
DET_OUTCOME = dict(DET_ROWS)

sys.path.insert(0, str(SCRIPTS))
import make_aug1085_dataset as aug  # reuse the arm-B augmentation, never reimplement it

# Journal PDFs must embed TrueType, not matplotlib's default Type 3.
matplotlib.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42,
                           "font.size": 9, "axes.titlesize": 10})


def save(fig, name: str, png: str | None, out_dir: Path | None = None) -> Path:
    target = out_dir or FIG_DIR
    target.mkdir(parents=True, exist_ok=True)
    out = target / name
    fig.savefig(out, bbox_inches="tight")
    if png:
        fig.savefig(png, dpi=170, bbox_inches="tight")
        print(f"preview -> {png}")
    plt.close(fig)
    print(f"saved -> {out}")
    return out


def flag_non_convergent(detectors: dict) -> set[str]:
    """EXPERIMENTS.md rule: fixed endpoint AND pooled OOF both below half the arm median."""
    fixed = {w: d["fixed_endpoint"]["metrics"][METRIC] for w, d in detectors.items()}
    oof = {w: d["cross_fitted"]["official_pooled_oof_metrics"][METRIC] for w, d in detectors.items()}
    return {w for w in detectors
            if fixed[w] < statistics.median(fixed.values()) / 2
            and oof[w] < statistics.median(oof.values()) / 2}


def fold_summary(folds: list[int]) -> str:
    """e.g. '280 x5' when every fold agrees, else '260, 280, 290'."""
    if len(set(folds)) == 1:
        return f"{folds[0]} x{len(folds)}"
    return ", ".join(str(epoch) for epoch in sorted(folds))


def load_arm(arm: str) -> dict:
    path = ROOT / "experiments" / "v4_protocol" / f"v4_protocol_{arm}.json"
    return json.loads(path.read_text(encoding="utf-8"))["arms"][arm]


def selection_curve(png: str | None, arm: str = "all") -> None:
    """Checkpoint selection, one row per arm.

    Every panel shows the same pre-registered rule - the 3-point-smoothed mAP50-95 argmax -
    read off one arm, so the rows differ only in how tightly the five folds agree. `--arm X`
    writes a single-arm version to its own file, for inspection; it never replaces the paper
    figure.
    """
    arms = ARM_ORDER if arm == "all" else [arm]
    name = "fig3_selection_curve.pdf" if arm == "all" else f"fig3_selection_curve_{arm}.pdf"
    fig, axes = plt.subplots(len(arms), len(WEIGHTS), figsize=(11.0, 2.45 * len(arms) + 1.15),
                             sharex=True, sharey="row", squeeze=False)
    any_flagged = False
    for row, arm_key in enumerate(arms):
        detectors = load_arm(arm_key)["detectors"]
        flagged = flag_non_convergent(detectors)
        any_flagged |= bool(flagged)
        for column, weight in enumerate(WEIGHTS):
            ax = axes[row, column]
            record = detectors[weight]
            curve = record["full_dev_curve"]
            epochs = [point["epoch"] for point in curve]
            ax.plot(epochs, [point[METRIC] for point in curve], color=INK["grid"], lw=0.9,
                    zorder=2, label="per-checkpoint score on dev61")
            ax.plot(epochs, [point["smoothed_mAP50-95"] for point in curve],
                    color=ARM_COLOR[arm_key], lw=2.0, zorder=3,
                    label="3-point smoothed (the selection curve)")
            deployment = record["deployment"]["selected_epoch"]
            ax.axvline(deployment, color=INK["secondary"], ls="--", lw=1.0, zorder=1,
                       label="epoch selected on all dev61 (deployment)")
            folds = [fold["selected_epoch"] for fold in record["cross_fitted"]["folds"]]
            ax.plot(folds, [0.03] * len(folds), marker="|", color=INK["text"], ms=10, mew=1.8,
                    ls="none", transform=ax.get_xaxis_transform(), clip_on=False, zorder=4,
                    label="epoch selected by each of the five folds")
            ax.text(0.03, 0.10, fold_summary(folds), transform=ax.transAxes, va="bottom",
                    ha="left", fontsize=6.5, color=INK["secondary"],
                    bbox=dict(facecolor=INK["surface"], edgecolor="none", alpha=0.85, pad=1.2))
            ax.set_title(weight + (r"$^\dagger$" if weight in flagged else ""), fontsize=9,
                         color=(FLAG_COLOR if weight in flagged else INK["text"]))
            ax.set_xlim(0, 310)
            ax.set_axisbelow(True)
            ax.grid(lw=0.5, color=INK["grid"])
            ax.tick_params(labelsize=7.5, colors=INK["secondary"])
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            for side in ("left", "bottom"):
                ax.spines[side].set_color(INK["axis"])
        axes[row, 0].set_ylabel(f"{ARM_SHORT[arm_key]} arm\ndev61 {METRIC}", fontsize=8.5,
                                color=INK["text"])
    for ax in axes[-1]:
        ax.set_xlabel("epoch", fontsize=8.5, color=INK["secondary"])
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=8.5,
               bbox_to_anchor=(0.5, 0.005))
    fig.suptitle("Checkpoint selection on dev61: one pre-registered rule, applied arm by arm"
                 "   (each row keeps its own mAP50-95 scale)\n"
                 + "    ".join(f"{ARM_SHORT[a]}: {ARM_DESC[a]}" for a in arms)
                 + (r"     $^\dagger$ flagged non-convergent (EXPERIMENTS.md)" if any_flagged else ""),
                 fontsize=9.5, color=INK["text"])
    fig.tight_layout(rect=(0, 0.075, 1, 0.90))
    save(fig, name, png, out_dir=None if arm == "all" else ROOT / ".tmp")


def find_comparison(comparisons: list[dict], target: str, arm_a: str, arm_b: str,
                    detector: str | None = None) -> dict:
    for entry in comparisons:
        if (entry["target"] == target and entry["arm_a"] == arm_a and entry["arm_b"] == arm_b
                and entry["detector"] == detector):
            return entry
    raise KeyError(f"no comparison {target} {arm_a}->{arm_b} detector={detector}")


def bootstrap_ci(png: str | None) -> None:
    """Arm contrasts with their paired cluster-bootstrap 95% CIs.

    Panel (a) is the arm-level detector+checkpoint contrast - the paper's primary claim - for
    both metrics. Panels (b)-(d) repeat the same contrasts detector by detector on pooled OOF
    (primary metric): the consistency evidence. Each of (b)-(d) names its own contrast in the
    title, so identity never rests on colour alone, and all four panels share one x scale so
    they can be read against each other. Values are labelled in (a) only - eighteen labels
    spread over (b)-(d) would be unreadable, and the table carries every number.
    """
    comparisons = json.loads(BOOTSTRAP_JSON.read_text(encoding="utf-8"))["comparisons"]
    metrics = [(METRIC, "o"), ("mAP50", "s")]

    # One shared x range for all panels, computed from the data plus room for panel (a)'s labels.
    spans = [(entry[metric]["ci95"][0], entry[metric]["ci95"][1])
             for entry in comparisons if entry["target"] == "joint" for metric, _ in metrics]
    spans += [(entry[METRIC]["ci95"][0], entry[METRIC]["ci95"][1])
              for entry in comparisons if entry["target"] == "oof"]
    xlim = (min(low for low, _ in spans) - 0.05, max(high for _, high in spans) + 0.14)

    fig, axes = plt.subplots(1, 4, figsize=(11.0, 3.1),
                             gridspec_kw={"width_ratios": [1.45, 1.0, 1.0, 1.0]})
    left = axes[0]
    for row, (arm_a, arm_b) in enumerate(PAIR_ORDER):
        entry = find_comparison(comparisons, "joint", arm_a, arm_b)
        color = PAIR_COLOR[(arm_a, arm_b)]
        for offset, (metric, marker) in zip((-0.17, 0.17), metrics):
            delta = entry["observed_delta"][metric]
            low, high = entry[metric]["ci95"]
            left.plot([low, high], [row + offset] * 2, color=color, lw=2.0,
                      solid_capstyle="butt", zorder=3)
            left.plot([delta], [row + offset], marker=marker, color=color, ms=7,
                      markeredgecolor=INK["surface"], markeredgewidth=1.2, ls="none", zorder=4)
            left.text(high + 0.022, row + offset, f"{delta:+.3f}", va="center", ha="left",
                      fontsize=7.5, color=INK["secondary"])
            if row == 0:
                # Name the two metrics once, on the top row, where the whole left band is free.
                # The metric-to-offset pairing is the same in every row, so this label set
                # teaches the pattern; no legend box is needed, and none would fit here.
                left.text(low - 0.025, row + offset, metric, va="center", ha="right",
                          fontsize=7.5, color=INK["text"])
    left.set_yticks(range(len(PAIR_ORDER)))
    left.set_yticklabels([f"{ARM_SHORT[b]} − {ARM_SHORT[a]}" for a, b in PAIR_ORDER], fontsize=9)
    left.set_ylim(len(PAIR_ORDER) - 0.55, -0.45)
    left.set_title("(a) arm-level contrast\nboth metrics", fontsize=9, color=INK["text"])

    for letter, panel, (arm_a, arm_b) in zip("bcd", axes[1:], PAIR_ORDER):
        color = PAIR_COLOR[(arm_a, arm_b)]
        for column, weight in enumerate(WEIGHTS):
            entry = find_comparison(comparisons, "oof", arm_a, arm_b, weight)
            delta = entry["observed_delta"][METRIC]
            low, high = entry[METRIC]["ci95"]
            panel.plot([low, high], [column] * 2, color=color, lw=2.0, solid_capstyle="butt",
                       zorder=3)
            panel.plot([delta], [column], marker="o", color=color, ms=6,
                       markeredgecolor=INK["surface"], markeredgewidth=1.2, ls="none", zorder=4)
        panel.set_yticks(range(len(WEIGHTS)))
        panel.set_title(f"({letter}) {ARM_SHORT[arm_b]} − {ARM_SHORT[arm_a]}\nper detector",
                        fontsize=9, color=INK["text"])
        panel.set_ylim(len(WEIGHTS) - 0.5, -0.5)
    axes[1].set_yticklabels(WEIGHTS, fontsize=8)
    for panel in axes[2:]:
        panel.sharey(axes[1])
        panel.tick_params(labelleft=False)

    for ax in axes:
        ax.axvline(0.0, color=INK["axis"], lw=1.0, zorder=1)
        ax.set_xlim(*xlim)
        ax.set_axisbelow(True)
        ax.grid(axis="x", lw=0.5, color=INK["grid"])
        ax.tick_params(labelsize=8, colors=INK["secondary"])
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(INK["axis"])
        ax.set_xlabel("Δ mAP on dev61", fontsize=8.5, color=INK["secondary"])
    fig.suptitle("Paired cluster bootstrap over the 61 dev61 images (10 000 resamples, seed 0); "
                 "an interval that meets the zero line does not establish a difference",
                 fontsize=9.5, color=INK["text"])
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    save(fig, "fig4_bootstrap_ci.pdf", png)


def label_path(image: Path) -> Path:
    parts = list(image.parts)
    parts[len(parts) - 1 - parts[::-1].index("images")] = "labels"
    return Path(*parts).with_suffix(".txt")


def positive_images(directory: Path, limit: int | None = None) -> list[Path]:
    found = [p for p in sorted(directory.glob("*.png"))
             if label_path(p).exists() and label_path(p).stat().st_size]
    return found[:limit] if limit else found


def pick_seed_photo(name: str | None = None) -> Path:
    """The seed photo used by the illustration.

    Pinned by name rather than chosen by a rule: real93 mixes annotation conventions (178 of
    its 179 boxes are small, median area 0.021, while one photo carries a single whole-frame
    box), so any automatic "most prominent box" rule picks that anomaly rather than a legible
    violation.
    """
    chosen = SEED_IMAGES / f"{name or DEFAULT_SEED_PHOTO}.png"
    assert chosen.exists(), f"no such seed photo: {chosen}"
    return chosen


def resolve_generated(name: str) -> Path:
    """Locate a generated image by name or stem in either reviewed batch."""
    stem = name if name.endswith(".png") else f"{name}.png"
    for directory in GEN_DIRS:
        candidate = directory / stem
        if candidate.exists():
            return candidate
    raise SystemExit(f"no such generated image: {name} (looked in {[str(d) for d in GEN_DIRS]})")


def pick_generated(names: list[str] | None = None, n: int = 3) -> list[Path]:
    """The generated samples shown in Fig. 2.

    With names (the pinned default, or --generated) the choice is exactly what was asked for.
    Without any, fall back to a deterministic greedy pick of mutually dissimilar images, which
    is only a way to explore candidates; the paper uses a hand-picked set.
    """
    if names:
        chosen = [resolve_generated(name) for name in names]
        for path in chosen:
            if not aug.read_label(label_path(path)):
                print(f"note: {path.name} has no annotated box; its panel will show none")
        return chosen
    pool = positive_images(GEN_DIRS[0], limit=60) + positive_images(GEN_DIRS[1], limit=60)
    chosen = [pool[0]]
    while len(chosen) < n:
        def distance(candidate):
            return min(1.0 - float(np.dot(thumb(candidate), thumb(other)))
                       for other in chosen)
        chosen.append(max((p for p in pool if p not in chosen), key=distance))
    return chosen


def thumb(path: Path):
    array = np.asarray(Image.open(path).convert("L").resize((48, 48), Image.BILINEAR),
                       dtype=np.float32)
    array -= array.mean()
    norm = np.linalg.norm(array)
    return (array / norm if norm > 0 else array).reshape(-1)


def draw(ax, source, title: str, rows) -> None:
    picture = Image.open(source).convert("RGB") if isinstance(source, (str, Path)) else source
    ax.imshow(picture)
    # imshow shrinks the axes box to the image aspect; anchoring at the top keeps the panel
    # titles of a row on one line when the images have different aspect ratios.
    ax.set_anchor("N")
    width, height = picture.size
    for _, cx, cy, bw, bh in rows:
        ax.add_patch(Rectangle(((cx - bw / 2) * width, (cy - bh / 2) * height),
                               bw * width, bh * height, fill=False, edgecolor="lime", lw=1.5))
    ax.set_title(title, fontsize=9)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def arms_samples(png: str | None, seed_name: str | None,
                 generated_names: list[str] | None, force: bool = False) -> None:
    # Fig. 2 is finalized by hand in a PDF editor after the script picks the panels, so the
    # script must not silently throw that work away on a re-run.
    target = FIG_DIR / "fig2_arms_samples.pdf"
    if target.exists() and not force:
        raise SystemExit(
            f"{target.name} already exists and Fig. 2 is hand-finalized; pass --force to "
            f"overwrite it with a script-generated version.")
    seed_photo = pick_seed_photo(seed_name)
    seed_rows = aug.read_label(label_path(seed_photo))
    variants = [aug.augment(Image.open(seed_photo).convert("RGB"), seed_rows,
                            random.Random(seed)) for seed in (1, 2, 3)]
    generated = pick_generated(generated_names if generated_names is not None
                               else DEFAULT_GENERATED)

    fig, top, bottom, note_y = layout(seed_photo, generated)
    draw(fig.add_subplot(top[0, 0]), seed_photo,
         f"A: real seed photo ({seed_photo.stem})", seed_rows)
    for column, (picture, rows) in enumerate(variants, start=1):
        draw(fig.add_subplot(top[0, column]), picture, f"B: classical aug {column}", rows)
    for column, image in enumerate(generated):
        draw(fig.add_subplot(bottom[0, column]), image,
             f"C: generated sample {column + 1}", aug.read_label(label_path(image)))

    fig.suptitle("What each same-source arm actually adds: geometry and colour versus a new "
                 "hazard state", fontsize=10.5)
    fig.text(0.5, note_y,
             "Top row: one real seed photo (A) and three variants produced by the exact "
             "augmentation function used to build the B arm; boxes are carried through every\n"
             "transform. Rotation and down-scaling pad with grey, so a variant can carry grey "
             "margins - a property of this arm, not a rendering artefact.\n"
             "Bottom row: generated samples (C) - "
             + ", ".join(image.name for image in generated) + ".\n"
             "Every synthesized image is an edit of one of the same seed photos, but the "
             "panels are not a matched set: the samples shown are edits of other seeds,\n"
             "not of the photo above, so the vertical pairing is illustrative only. No "
             "synthesized image derives from the development benchmark.\n"
             "All boxes are the reviewed human labels.",
             ha="center", va="top", fontsize=7.5, color="0.2")
    save(fig, "fig2_arms_samples.pdf", png)


def layout(seed_photo: Path, generated: list[Path]):
    """Size the canvas from the images' real aspect ratios so no dead band is left over."""
    fig_w, side, head, title, gap, note = 11.0, 0.10, 0.34, 0.26, 0.30, 0.80
    columns = len(generated)
    with Image.open(seed_photo) as handle:
        seed_aspect = handle.width / handle.height
    aspects = []
    for image in generated:
        with Image.open(image) as handle:
            aspects.append(handle.width / handle.height)
    usable = fig_w - 2 * side
    top_h = (usable / 4) / seed_aspect
    bottom_h = (usable / columns) / min(aspects)
    fig_h = head + title + top_h + gap + title + bottom_h + note
    top_bottom = fig_h - head - title - top_h
    bottom_top = top_bottom - gap - title
    bottom_bottom = bottom_top - bottom_h
    fig = plt.figure(figsize=(fig_w, fig_h))
    spans = dict(left=side / fig_w, right=1 - side / fig_w, wspace=0.05)
    top = fig.add_gridspec(1, 4, bottom=top_bottom / fig_h, top=(top_bottom + top_h) / fig_h, **spans)
    bottom = fig.add_gridspec(1, columns, bottom=bottom_bottom / fig_h,
                              top=(bottom_bottom + bottom_h) / fig_h, **spans)
    return fig, top, bottom, (bottom_bottom - 0.40) / fig_h


def deploy_weights(arm: str) -> Path:
    weight, epoch = DEPLOY[arm]
    path = ROOT / "runs" / "detect" / arm / weight / "weights" / f"epoch{epoch}.pt"
    if not path.exists():
        raise SystemExit(f"missing deployment checkpoint: {path}")
    return path


def run_predictions(conf_floor: float = 0.05) -> dict:
    """Infer every dev61 image once with each arm's deployment model, then cache the boxes.

    The cache is what lets the figure be rebuilt without a GPU. It records the checkpoint path
    and every box above `conf_floor`, so re-rendering cannot silently show different
    detections; the display threshold is applied at draw time. Inference is deterministic
    (no augmentation, fixed imgsz, one image at a time).
    """
    from ultralytics import YOLO  # lazy: the other figures must not need torch

    images = [Path(line.strip()) for line in DEV_LIST_V4.read_text(encoding="utf-8-sig").splitlines()
              if line.strip()]
    cache = {"conf_floor": conf_floor, "imgsz": DET_IMGSZ, "weights": {}, "images": {}}
    for arm in ARM_ORDER:
        path = deploy_weights(arm)
        cache["weights"][arm] = str(path.relative_to(ROOT))
        model = YOLO(str(path))
        for image in images:
            boxes = model.predict(str(image), conf=conf_floor, iou=0.45, imgsz=DET_IMGSZ,
                                  device=0, verbose=False)[0].boxes
            cache["images"].setdefault(image.name, {"path": str(image), "arms": {}})
            cache["images"][image.name]["arms"][arm] = [
                {"xyxy": [float(v) for v in box], "conf": float(score)}
                for box, score in zip(boxes.xyxy.cpu().numpy(), boxes.conf.cpu().numpy())]
        print(f"predicted {arm} -> {cache['weights'][arm]}", flush=True)
    DET_CACHE.parent.mkdir(parents=True, exist_ok=True)
    DET_CACHE.write_text(json.dumps(cache, indent=1) + "\n", encoding="utf-8")
    print(f"cached detections -> {DET_CACHE}")
    return cache


def load_detections(refresh: bool = False) -> dict:
    if refresh or not DET_CACHE.exists():
        return run_predictions()
    return json.loads(DET_CACHE.read_text(encoding="utf-8"))


def ground_truth(image: Path, width: int, height: int) -> list[list[float]]:
    """Reviewed dev61 labels in pixels as [x1, y1, x2, y2]."""
    return [[(cx - w / 2) * width, (cy - h / 2) * height,
             (cx + w / 2) * width, (cy + h / 2) * height]
            for _, cx, cy, w, h in aug.read_label(label_path(image))]


def det_panel(ax, picture, gt, predictions, color: str, conf: float, title: str = "") -> None:
    """One image with the label (dashed) and this arm's predictions (solid, with confidence)."""
    ax.imshow(picture)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    width, height = picture.size
    # A dark under-stroke keeps boxes and labels readable on cluttered site photos without
    # introducing a fourth colour into the palette.
    for x1, y1, x2, y2 in gt:
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor=DET_GT_COLOR,
                               lw=1.0, linestyle=(0, (3, 2)),
                               path_effects=[pe.withStroke(linewidth=2.0, foreground="black")]))
    for detection in predictions:
        if detection["conf"] < conf:
            continue
        x1, y1, x2, y2 = detection["xyxy"]
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor=color, lw=1.4,
                               path_effects=[pe.withStroke(linewidth=2.4, foreground="black")]))
        ax.text(x1, y1, f"{detection['conf']:.2f}", color=color, fontsize=5.5, ha="left", va="bottom",
                path_effects=[pe.withStroke(linewidth=1.6, foreground="black")])
    if title:
        ax.set_title(title, fontsize=8.5, color=INK["text"])


def detections(png: str | None, images: list[str] | None = None, conf: float = DET_CONF,
               refresh: bool = False) -> None:
    """Ground truth beside each arm's deployment predictions, one outcome per row.

    Rows are hand-picked (DET_IMAGES) to illustrate specific outcomes rather than sampled, so
    the caption says so; every panel in a row is the same image at the same scale. Pass
    --images to render other candidates for inspection.
    """
    cache = load_detections(refresh)
    picks = images or DET_IMAGES
    missing = [name for name in picks if name not in cache["images"]]
    if missing:
        raise SystemExit(f"no cached detections for {missing}; known names look like "
                         f"{sorted(cache['images'])[:2]}, or run --refresh")

    # head holds the four column headers; gap_y holds the per-row titles, which sit just above
    # the ground-truth panel of their row and must not touch the panels above them.
    fig_w, side, gap_x, gap_y, head, note = 11.0, 0.06, 0.035, 0.30, 0.62, 0.95
    panel_w = (fig_w - 2 * side - 3 * gap_x) / 4
    rows = []
    for name in picks:
        path = Path(cache["images"][name]["path"])
        with Image.open(path) as handle:
            aspect = handle.width / handle.height
        rows.append((name, path, panel_w / aspect))
    heights = [height for *_, height in rows]
    fig_h = head + sum(heights) + gap_y * (len(rows) - 1) + note
    fig = plt.figure(figsize=(fig_w, fig_h))

    headers = ["Ground truth (labels)", *[f"{ARM_SHORT[a]}: {ARM_DESC[a]}" for a in ARM_ORDER]]
    for column, header in enumerate(headers):
        fig.text((side + column * (panel_w + gap_x)) / fig_w, 1 - 0.10 / fig_h, header,
                 ha="left", va="top", fontsize=9, color=INK["text"])
    top = fig_h - head
    for index, (name, path, height) in enumerate(rows):
        y = top - sum(heights[:index]) - gap_y * index - height
        entry = cache["images"][name]
        with Image.open(path) as handle:
            picture = handle.convert("RGB")
            gt = ground_truth(path, handle.width, handle.height)
        for column in range(4):
            ax = fig.add_axes([(side + column * (panel_w + gap_x)) / fig_w, y / fig_h,
                               panel_w / fig_w, height / fig_h])
            arm = ARM_ORDER[column - 1] if column else None
            label = DET_OUTCOME.get(name)
            title = (f"{name}  ({len(gt)} labelled box{'es' if len(gt) != 1 else ''}"
                     + (f")  ·  {label}" if label else ")") if column == 0 else "")
            det_panel(ax, picture, gt, [] if arm is None else entry["arms"][arm],
                      INK["muted"] if arm is None else ARM_COLOR[arm], conf, title)
    fig.text(0.5, (note - 0.66) / fig_h,
             "Predictions of each arm's deployment checkpoint on the development benchmark "
             "(dev61); all three arms selected yolo26s, at epoch 280 (A), 200 (B) and 260 (C). "
             f"Boxes are drawn at confidence ≥ {conf:.2f}.\n"
             "Dashed lime: the reviewed human label. Solid, in the arm's colour: a prediction, "
             "labelled with its confidence. A dashed box with no solid box over it was missed.\n"
             "Rows are hand-picked to show the outcome named in each row title, not a random "
             "sample; per-image statistics are in the main table.\n"
             "The benchmark images differ widely in resolution and aspect, so every panel is "
             "shown at its source scale.",
             ha="center", va="top", fontsize=7.5, color="0.2")
    # --images is for inspection: it must never overwrite the paper figure.
    name = ("fig5_detections_dev61.pdf" if images is None
            else "fig5_detections_dev61_candidates.pdf")
    save(fig, name, png)


def fold_summary_tex(folds: list[int]) -> str:
    """Compact LaTeX summary of the five fold choices, e.g. '280 $\\times$ 3, 260, 300'.

    Listing all five epochs verbatim makes the column wider than the text block, so repeats
    are folded into a count.
    """
    counts = {}
    for epoch in folds:
        counts[epoch] = counts.get(epoch, 0) + 1
    parts = []
    for epoch, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        parts.append(f"{epoch} $\\times$ {count}" if count > 1 else str(epoch))
    return ", ".join(parts)


def table_selection() -> None:
    """Emit the checkpoint-selection table straight from the result JSON, one block per arm.

    The paper's own rule is that numbers are never hand-copied into the tex, so the whole
    float is generated and \\input by working_paper.tex. It is emitted as a complete float
    rather than as bare rows because \\input inside a tabular trips over the end-of-file
    token state and `\\bottomrule` then reports a misplaced \\noalign.
    """
    rows = []
    for arm in ARM_ORDER:
        detectors = load_arm(arm)["detectors"]
        flagged = flag_non_convergent(detectors)
        for weight in WEIGHTS:
            record = detectors[weight]
            folds = [fold["selected_epoch"] for fold in record["cross_fitted"]["folds"]]
            name = weight + ("$^{\\dagger}$" if weight in flagged else "")
            rows.append(
                f"  {ARM_SHORT[arm]} & {name} & {record['deployment']['selected_epoch']} & "
                f"{fold_summary_tex(folds)} & "
                f"{record['fixed_endpoint']['metrics'][METRIC]:.4f} & "
                f"{record['cross_fitted']['official_pooled_oof_metrics'][METRIC]:.4f} \\\\")
        if arm != ARM_ORDER[-1]:
            rows.append("  \\midrule")
    legend = " \\quad ".join(f"{ARM_SHORT[a]}: {ARM_DESC[a]}" for a in ARM_ORDER)
    body = [
        "% Generated by paper/make_figures.py --fig tab-selection.",
        "% Source: experiments/v4_protocol/v4_protocol_<arm>.json (arms A, B and C).",
        "% Do not edit by hand; re-run the script so the numbers cannot drift from the JSON.",
        "\\begin{table}[t]",
        "  \\centering",
        "  \\small",
        "  \\caption{Checkpoint selection on dev61, arm by arm; all scores are mAP50--95, the",
        "  pre-registered selection metric. ``Fold-selected epochs'' gives the epoch chosen by",
        "  each of the five cross-fitting folds, with repeats folded into a count. $^{\\dagger}$",
        "  marks a run flagged \\emph{non-convergent} by the rule in \\texttt{EXPERIMENTS.md}.",
        f"  Arms: {legend}.}}",
        "  \\label{tab:selection}",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{llcccc}",
        "  \\toprule",
        "  Arm & Detector & Deploy.\\ epoch & Fold-selected epochs & Fixed endpoint & Pooled OOF \\\\",
        "  \\midrule",
        *rows,
        "  \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    out = TABLE_DIR / "tab_selection.tex"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"saved -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fig", required=True,
                        choices=["selection-curve", "bootstrap-ci", "arms-samples",
                                 "detections", "tab-selection"])
    parser.add_argument("--png", default=None, help="also write a raster copy to this path")
    parser.add_argument("--arm", default="all",
                        help="selection-curve: 'all' for the paper figure, or one arm key "
                             "for a single-arm copy written to its own file")
    parser.add_argument("--seed-photo", default=None,
                        help="arms-samples: seed photo stem, e.g. real_photo_30")
    parser.add_argument("--generated", default=None,
                        help="arms-samples: comma-separated generated images for the bottom "
                             "row (name or stem); default is the pinned paper set, pass '' to "
                             "fall back to the automatic diverse pick")
    parser.add_argument("--force", action="store_true",
                        help="arms-samples: overwrite the hand-finalized Fig. 2 PDF")
    parser.add_argument("--images", default=None,
                        help="detections: comma-separated dev61 image names to render instead "
                             "of the pinned set (e.g. new_test_set_0054.jpg)")
    parser.add_argument("--refresh", action="store_true",
                        help="detections: re-run the deployment models instead of using the "
                             "cached boxes (needs a GPU, about two minutes)")
    parser.add_argument("--conf", type=float, default=DET_CONF,
                        help=f"detections: display confidence threshold (default {DET_CONF})")
    args = parser.parse_args()
    if args.fig == "selection-curve":
        selection_curve(args.png, args.arm)
    elif args.fig == "bootstrap-ci":
        bootstrap_ci(args.png)
    elif args.fig == "arms-samples":
        names = (None if args.generated is None
                 else [name.strip() for name in args.generated.split(",") if name.strip()])
        arms_samples(args.png, args.seed_photo, names, args.force)
    elif args.fig == "detections":
        chosen = (None if args.images is None
                  else [name.strip() for name in args.images.split(",") if name.strip()])
        detections(args.png, chosen, args.conf, args.refresh)
    else:
        table_selection()


if __name__ == "__main__":
    sys.exit(main())
