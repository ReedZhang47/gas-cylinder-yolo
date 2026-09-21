r"""Paper figures, rebuilt from experiments/ JSON so no number is hand-copied into the tex.

  selection-curve : A-arm checkpoint-selection curves (Fig. 3), 2x3 detector panels
  arms-samples    : qualitative A/B/C sample comparison (Fig. 2)

Both write into paper/figures/. `--png PATH` additionally writes a raster copy, which is
handy for eyeballing the result in a viewer that does not render PDF.

Usage:
  python paper/make_figures.py --fig selection-curve
  python paper/make_figures.py --fig selection-curve --png $TEMP/fig3.png
  python paper/make_figures.py --fig arms-samples
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
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from PIL import Image

ROOT = Path(r"D:/yolo")
FIG_DIR = ROOT / "paper" / "figures"
SCRIPTS = ROOT / "scripts"
V4_JSON = ROOT / "experiments" / "v4_protocol" / "v4_protocol_real93v4.json"
SEED_IMAGES = Path(r"D:/gas_cylinders/real_photo/93_real_photos/images")
GEN_DIRS = [Path(r"D:/gas_cylinders/Placement_Issues/images"),
            Path(r"D:/gas_cylinders/Placement_Issues_2/images")]
WEIGHTS = ["yolov8s", "yolov8m", "yolo11s", "yolo11m", "yolo26s", "yolo26m"]
METRIC = "mAP50-95"
# The seed photo and generated samples used by the committed Fig. 2. Chosen by hand for a
# legible violation (a cylinder lying on the ground among rebar) and pinned here so re-running
# the script without arguments reproduces the figure exactly; --seed-photo and --generated
# override them.
DEFAULT_SEED_PHOTO = "real_photo_30"
DEFAULT_GENERATED = ["Placement_Issues_0001.png", "Placement_Issues_0554.png",
                     "Placement_Issues_0515.png"]

sys.path.insert(0, str(SCRIPTS))
import make_aug1085_dataset as aug  # reuse the arm-B augmentation, never reimplement it

# Journal PDFs must embed TrueType, not matplotlib's default Type 3.
matplotlib.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42,
                           "font.size": 9, "axes.titlesize": 10})


def save(fig, name: str, png: str | None) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / name
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


def selection_curve(png: str | None) -> None:
    arm = json.loads(V4_JSON.read_text(encoding="utf-8"))["arms"]["real93v4"]
    detectors = arm["detectors"]
    flagged = flag_non_convergent(detectors)

    fig, axes = plt.subplots(2, 3, figsize=(11.0, 5.8), sharex=True)
    for ax, weight in zip(axes.ravel(), WEIGHTS):
        record = detectors[weight]
        curve = record["full_dev_curve"]
        epochs = [point["epoch"] for point in curve]
        ax.plot(epochs, [point[METRIC] for point in curve], color="0.72", lw=1.0,
                label="checkpoint score on dev61")
        ax.plot(epochs, [point["smoothed_mAP50-95"] for point in curve], color="C0", lw=2.0,
                label="3-point smoothed (selection curve)")
        deployment = record["deployment"]["selected_epoch"]
        ax.axvline(deployment, color="C3", ls="--", lw=1.2,
                   label="epoch selected on all dev61 (deployment)")
        folds = [fold["selected_epoch"] for fold in record["cross_fitted"]["folds"]]
        ax.plot(folds, [0.04] * len(folds), marker="|", color="black", ms=12, mew=2.0,
                ls="none", transform=ax.get_xaxis_transform(), clip_on=False,
                label="epoch selected by each of the five folds")
        ax.text(0.015, 0.045, f"folds {fold_summary(folds)}  |  dep ep {deployment}",
                transform=ax.transAxes, va="bottom", ha="left", fontsize=7.5, color="0.2",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1.5))
        title = weight + ("   [non-convergent]" if weight in flagged else "")
        ax.set_title(title, color=("C3" if weight in flagged else "black"))
        ax.set_xlim(0, 310)
        ax.grid(alpha=0.25, lw=0.5)

    for ax in axes[-1]:
        ax.set_xlabel("epoch")
    for ax in axes[:, 0]:
        ax.set_ylabel(METRIC)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("A arm (93 real photos): checkpoint selection on the dev61 benchmark\n"
                 "the dashed line and the black ticks are the same pre-registered "
                 "smoothed-argmax rule, applied to all dev61 versus to each fold's "
                 "four-fold complement")
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    save(fig, "fig3_selection_curve.pdf", png)


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
                 generated_names: list[str] | None) -> None:
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
             "Bottom row: generated samples (C) in sampling order - "
             + ", ".join(image.name for image in generated) + ".\n"
             "The generation step kept no source-image mapping, so these are not edits of the "
             "photo above; the pairing is illustrative only. All boxes are the reviewed human "
             "labels.",
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
    """Emit the checkpoint-selection table straight from the result JSON.

    The paper's own rule is that numbers are never hand-copied into the tex, so the whole
    float is generated and \\input by working_paper.tex. It is emitted as a complete float
    rather than as bare rows because \\input inside a tabular trips over the end-of-file
    token state and `\\bottomrule` then reports a misplaced \\noalign.
    """
    arm = json.loads(V4_JSON.read_text(encoding="utf-8"))["arms"]["real93v4"]
    detectors = arm["detectors"]
    flagged = flag_non_convergent(detectors)
    rows = []
    for weight in WEIGHTS:
        record = detectors[weight]
        folds = [fold["selected_epoch"] for fold in record["cross_fitted"]["folds"]]
        name = weight + ("$^{\\dagger}$" if weight in flagged else "")
        rows.append(
            f"  {name} & {record['deployment']['selected_epoch']} & {fold_summary_tex(folds)} & "
            f"{record['fixed_endpoint']['metrics'][METRIC]:.4f} & "
            f"{record['cross_fitted']['official_pooled_oof_metrics'][METRIC]:.4f} \\\\")
    body = [
        f"% Generated by paper/make_figures.py --fig tab-selection.",
        f"% Source: {V4_JSON.relative_to(ROOT).as_posix()} (arm A, real 93 photos).",
        "% Do not edit by hand; re-run the script so the numbers cannot drift from the JSON.",
        "\\begin{table}[t]",
        "  \\centering",
        "  \\small",
        "  \\caption{Checkpoint selection on dev61 for arm~A (real 93 photos); all scores are",
        "  mAP50--95. ``Fold-selected epochs'' gives the epoch chosen by each of the five",
        "  cross-fitting folds, with repeats folded into a count. $^{\\dagger}$ marks the run",
        "  flagged \\emph{non-convergent} by the pre-registered rule in \\texttt{EXPERIMENTS.md}.}",
        "  \\label{tab:selection}",
        "  \\setlength{\\tabcolsep}{4pt}",
        "  \\begin{tabular}{lcccc}",
        "  \\toprule",
        "  Detector & Deploy.\\ epoch & Fold-selected epochs & Fixed endpoint & Pooled OOF \\\\",
        "  \\midrule",
        *rows,
        "  \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
    ]
    out = ROOT / "paper" / "tables" / "tab_selection.tex"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"saved -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fig", required=True,
                        choices=["selection-curve", "arms-samples", "tab-selection"])
    parser.add_argument("--png", default=None, help="also write a raster copy to this path")
    parser.add_argument("--seed-photo", default=None,
                        help="arms-samples: seed photo stem, e.g. real_photo_30")
    parser.add_argument("--generated", default=None,
                        help="arms-samples: comma-separated generated images for the bottom "
                             "row (name or stem); default is the pinned paper set, pass '' to "
                             "fall back to the automatic diverse pick")
    args = parser.parse_args()
    if args.fig == "selection-curve":
        selection_curve(args.png)
    elif args.fig == "arms-samples":
        names = (None if args.generated is None
                 else [name.strip() for name in args.generated.split(",") if name.strip()])
        arms_samples(args.png, args.seed_photo, names)
    else:
        table_selection()


if __name__ == "__main__":
    sys.exit(main())
