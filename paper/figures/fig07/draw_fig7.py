"""Fig. 7: dev61 held-out miss/false-alarm trade-off for A/B/C.

The input is each arm's joint detector-and-checkpoint pooled OOF prediction
cache.  Each image appears only in its held-out fold.  Arm D is an unfilled
table row and has no plotted curve until a validated D cache is available.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / "experiments" / "v4_protocol" / "per_image"
OUT_PDF = HERE / "fig7_operating_tradeoff.pdf"
OUT_SVG = HERE / "operating_tradeoff_abc.svg"

ARMS = [
    ("A", "real93v4", "#426F96"),
    ("B", "aug1085v4", "#B88232"),
    ("C", "gen1085v4", "#178A93"),
]
D_COLOR = "#755CAD"
INK, MUTED, GRID = "#1B3448", "#566C7D", "#D7E2E8"

plt.rcParams.update({
    "font.family": "Arial", "font.size": 11,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "savefig.facecolor": "white",
})


def read_arm(key: str) -> dict:
    data = json.loads((CACHE / f"per_image_{key}.json").read_text(encoding="utf-8"))
    assert data["arm"] == key
    rows = data["joint"]["oof_rows"]
    assert len(rows) == 61 and set(rows) == set(data["image_names"])
    assert sum(row["n_gt"] for row in rows.values()) == 72
    assert sum(row["n_gt"] == 0 for row in rows.values()) == 31
    for row in rows.values():
        assert row["n_iou"] == 10
        assert len(row["tp_masks"]) == len(row["conf"])
    return rows


def count_at(rows: dict, threshold: float) -> tuple[int, int, int, int]:
    """Return TP, FP, FN, and GT count at IoU 0.50 and score threshold."""
    n_gt = sum(row["n_gt"] for row in rows.values())
    tp = 0
    predicted = 0
    for row in rows.values():
        for mask, confidence in zip(row["tp_masks"], row["conf"]):
            if confidence >= threshold:
                predicted += 1
                tp += int(bool(mask & 1))  # first bit = IoU 0.50 match
    assert tp <= n_gt
    return tp, predicted - tp, n_gt - tp, n_gt


def build() -> None:
    data = {letter: read_arm(key) for letter, key, _ in ARMS}
    reference_names = set(data["A"])
    assert all(set(rows) == reference_names for rows in data.values())
    thresholds = np.sort(np.unique(np.r_[np.linspace(.05, .95, 131), .25, .50]))
    fig = plt.figure(figsize=(10.0, 5.0), facecolor="white")
    fig.text(.042, .946, "OPERATING TRADE-OFF", fontsize=17, weight="bold")
    fig.text(.962, .950, "pooled held-out predictions  /  dev61  /  IoU = 0.50",
             ha="right", fontsize=10.5, color=MUTED)
    fig.add_artist(Line2D([.042, .962], [.916, .916], transform=fig.transFigure,
                          color=GRID, lw=.9))
    fig.text(.085, .842, "(a)  Misses versus false alarms", fontsize=13, weight="bold")
    fig.text(.724, .842, "(b)  At confidence >= 0.25", fontsize=13, weight="bold")

    ax = fig.add_axes([.085, .19, .565, .565])
    ax.set_xlim(0, .70)
    ax.set_ylim(0, 1.0)
    ax.set_xticks([0, .1, .2, .3, .4, .5, .6, .7])
    ax.set_yticks([0, .2, .4, .6, .8, 1.0])
    ax.set_xlabel("False positives per development image (FP / 61)", labelpad=8)
    ax.set_ylabel("Missed labelled objects (FN / 72)", labelpad=8)
    ax.grid(color=GRID, lw=.75, zorder=0)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(labelsize=10)

    readout = {}
    for letter, _, color in ARMS:
        rows = data[letter]
        points = [count_at(rows, float(t)) for t in thresholds]
        x = np.array([fp / 61 for tp, fp, fn, gt in points])
        y = np.array([fn / gt for tp, fp, fn, gt in points])
        ax.plot(x, y, color=color, lw=2.5, zorder=2, label=f"Arm {letter}")
        for threshold, filled in ((.25, True), (.50, False)):
            tp, fp, fn, gt = count_at(rows, threshold)
            ax.scatter([fp / 61], [fn / gt], s=80,
                       facecolor=color if filled else "white",
                       edgecolor="white" if filled else color,
                       linewidth=1.7, zorder=5)
        readout[letter] = count_at(rows, .25)

    # The table is a true placeholder for D: empty numerals, no suggested trend.
    table = fig.add_axes([.715, .20, .255, .555])
    table.axis("off")
    table.set_xlim(0, 1)
    table.set_ylim(0, 1)
    table.text(.02, .96, "ARM", fontsize=9.8, weight="bold", color=MUTED)
    table.text(.40, .96, "MISSED", fontsize=9.8, weight="bold", color=MUTED,
               ha="center")
    table.text(.82, .96, "FP/IMAGE", fontsize=9.8, weight="bold", color=MUTED,
               ha="center")
    table.plot([.02, .98], [.915, .915], color=GRID, lw=.9)
    ys = {"A": .78, "B": .60, "C": .42, "D": .24}
    for letter, _, color in ARMS:
        tp, fp, fn, gt = readout[letter]
        y = ys[letter]
        table.text(.02, y, letter, color=color, fontsize=13, weight="bold",
                   va="center")
        table.text(.40, y, f"{fn}/{gt}", ha="center", va="center",
                   fontsize=11.8, color=INK)
        table.text(.82, y, f"{fp/61:.3f}", ha="center", va="center",
                   fontsize=11.8, color=INK)
        table.plot([.02, .98], [y - .105, y - .105], color=GRID, lw=.7)
    table.add_patch(FancyBboxPatch((.015, .145), .97, .18,
                                   boxstyle="round,pad=0.005,rounding_size=0.02",
                                   transform=table.transAxes, facecolor="#FBF9FE",
                                   edgecolor="#AA98CA", lw=1.0,
                                   linestyle=(0, (4, 3))))
    table.text(.02, ys["D"], "D", color=D_COLOR, fontsize=13,
               weight="bold", va="center")
    table.text(.65, ys["D"], "reserved", color=D_COLOR, fontsize=10.5,
               ha="center", va="center")
    table.text(.02, .02, "Filled marker: 0.25   Open marker: 0.50",
               fontsize=8.8, color=MUTED)

    legend_handles = [Line2D([], [], color=color, lw=2.6, label=f"Arm {letter}")
                      for letter, _, color in ARMS]
    fig.legend(handles=legend_handles, loc="center left", bbox_to_anchor=(.087, .785),
               frameon=False, ncol=3, fontsize=10.5, handlelength=2.0,
               columnspacing=1.1)
    fig.text(.042, .065,
             "Thresholds 0.05-0.95. Each dev61 image contributes only its held-out fold predictions; "
             "curves describe development behaviour, not final-test performance.",
             fontsize=9.5, color=MUTED)
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_SVG)
    plt.close(fig)


if __name__ == "__main__":
    build()
