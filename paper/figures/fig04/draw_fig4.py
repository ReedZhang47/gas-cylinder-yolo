"""Fig. 4: four-arm layout with validated A/B/C joint OOF evidence.

Arm D and all D contrasts remain intentionally empty.  The plotted values are
read from bootstrap_paired.json; no score or interval is invented here.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments" / "v4_protocol" / "bootstrap_paired.json"
OUT_PDF = HERE / "fig4_arm_level_comparison.pdf"
OUT_SVG = HERE / "arm_level_comparison_abc.svg"

COLORS = {"A": "#426F96", "B": "#B88232", "C": "#178A93", "D": "#755CAD"}
INK = "#1B3448"
MUTED = "#566C7D"
GRID = "#D7E2E8"
ARM_KEYS = {"A": "real93v4", "B": "aug1085v4", "C": "gen1085v4"}

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 11,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": INK,
    "savefig.facecolor": "white",
})


def source_data() -> tuple[dict, dict]:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert data["params"]["n_boot"] == 10000
    joint = [row for row in data["comparisons"] if row["target"] == "joint"]
    assert len(joint) == 3
    keyed = {(row["arm_a"], row["arm_b"]): row for row in joint}
    expected = {
        ("real93v4", "aug1085v4"),
        ("real93v4", "gen1085v4"),
        ("aug1085v4", "gen1085v4"),
    }
    assert set(keyed) == expected
    scores = {}
    for arm, key in ARM_KEYS.items():
        found = [
            (row["point_a"] if row["arm_a"] == key else row["point_b"])
            for row in joint if key in (row["arm_a"], row["arm_b"])
        ]
        assert len(found) == 2 and found[0] == found[1]
        scores[arm] = found[0]
    return scores, keyed


def build() -> None:
    scores, comparisons = source_data()
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(10.0, 5.6), gridspec_kw={"width_ratios": [0.98, 1.18]}
    )
    fig.subplots_adjust(left=0.145, right=0.965, bottom=0.195, top=0.735, wspace=0.32)
    fig.text(0.038, 0.942, "FOUR-ARM COMPARISON", fontsize=17, weight="bold")
    fig.text(0.962, 0.945, "joint detector + checkpoint selection  /  dev61",
             ha="right", color=MUTED, fontsize=10.6)
    fig.add_artist(Line2D([0.038, 0.962], [0.910, 0.910], transform=fig.transFigure,
                          color=GRID, lw=0.9))
    fig.text(0.145, 0.845, "(a)  Cross-fitted pooled OOF AP", fontsize=13, weight="bold")
    fig.text(0.540, 0.845, "(b)  Paired difference in mAP50-95", fontsize=13,
             weight="bold")

    # Scores: two endpoints per arm, plotted on the same 0-1 AP scale.
    arm_y = {"A": 3, "B": 2, "C": 1, "D": 0}
    left.set_xlim(0, 1.0)
    left.set_ylim(-0.65, 3.65)
    left.set_yticks([3, 2, 1, 0], ["A  Real", "B  Classical",
                                   "C  Image edit", "D  LoRA T2I"])
    left.set_xticks([0, .2, .4, .6, .8, 1.0])
    left.set_xlabel("Average precision (AP)", labelpad=8)
    left.grid(axis="x", color=GRID, lw=0.75, zorder=0)
    left.tick_params(axis="y", length=0, pad=8, labelsize=10.4)
    left.tick_params(axis="x", labelsize=10)
    for spine in ("top", "right", "left"):
        left.spines[spine].set_visible(False)
    for arm in ("A", "B", "C"):
        y = arm_y[arm]
        main = scores[arm]["mAP50-95"]
        secondary = scores[arm]["mAP50"]
        left.plot([main, secondary], [y, y], color=COLORS[arm], lw=2.0,
                  alpha=0.58, zorder=2)
        left.scatter([main], [y], s=91, color=COLORS[arm],
                     edgecolor="white", linewidth=.9, zorder=4)
        left.scatter([secondary], [y], s=85, facecolor="white",
                     edgecolor=COLORS[arm], linewidth=2.0, zorder=4)
        left.annotate(f"{main:.3f}", (main, y), xytext=(0, 11),
                      textcoords="offset points", ha="center", fontsize=9.5,
                      color=COLORS[arm], weight="bold")
        left.annotate(f"{secondary:.3f}", (secondary, y), xytext=(0, -17),
                      textcoords="offset points", ha="center", fontsize=9.5,
                      color=MUTED)
    left.axhspan(-.43, .43, facecolor="#FBF9FE", zorder=0)
    left.hlines(0, 0.07, .93, color="#AA98CA", lw=1.1, ls=(0, (4, 3)))
    left.text(.5, 0, "reserved for D", ha="center", va="center", color=COLORS["D"],
              fontsize=10.3, transform=left.get_yaxis_transform(),
              bbox={"facecolor": "#FBF9FE", "edgecolor": "none", "pad": 1.5})

    # Paired image-cluster bootstrap.  The labels name (second arm - first arm).
    rows = [
        ("C - A", ("real93v4", "gen1085v4"), "C", 5),
        ("C - B", ("aug1085v4", "gen1085v4"), "C", 4),
        ("B - A", ("real93v4", "aug1085v4"), "B", 3),
    ]
    right.set_xlim(-.25, .52)
    right.set_ylim(-.65, 5.65)
    right.set_yticks([5, 4, 3, 2, 1, 0],
                     ["C - A", "C - B", "B - A", "D - A", "D - B", "D - C"])
    right.set_xticks([-.2, 0, .2, .4])
    right.set_xlabel("Difference in mAP50-95 (second - first arm)", labelpad=8)
    right.grid(axis="x", color=GRID, lw=.75, zorder=0)
    right.axvline(0, color="#798C99", lw=1.2, zorder=1)
    right.tick_params(axis="y", length=0, pad=8, labelsize=10.5)
    right.tick_params(axis="x", labelsize=10)
    for spine in ("top", "right", "left"):
        right.spines[spine].set_visible(False)
    for _, key, arm, y in rows:
        row = comparisons[key]
        delta = row["observed_delta"]["mAP50-95"]
        low, high = row["mAP50-95"]["ci95"]
        assert low <= delta <= high
        right.plot([low, high], [y, y], color=COLORS[arm], lw=2.6,
                   solid_capstyle="round", zorder=3)
        right.plot([low, low], [y - .09, y + .09], color=COLORS[arm], lw=1.6)
        right.plot([high, high], [y - .09, y + .09], color=COLORS[arm], lw=1.6)
        right.scatter([delta], [y], s=76, color=COLORS[arm],
                      edgecolor="white", linewidth=.9, zorder=4)
        right.text(.505, y, f"{delta:+.3f}", ha="right", va="center",
                   fontsize=10.2, color=COLORS[arm], weight="bold")
    right.add_patch(Rectangle((-.23, -.43), .73, 2.85, facecolor="#FBF9FE",
                              edgecolor="#AA98CA", lw=1.0, linestyle=(0, (4, 3)),
                              zorder=0))
    right.text(.26, 1, "D contrasts reserved", ha="center", va="center",
               color=COLORS["D"], fontsize=10.1)

    legend = [
        Line2D([], [], ls="none", marker="o", ms=8, color=INK,
               markerfacecolor=INK, label="mAP50-95"),
        Line2D([], [], ls="none", marker="o", ms=8, markerfacecolor="white",
               markeredgecolor=INK, markeredgewidth=1.6, label="mAP50"),
    ]
    fig.legend(handles=legend, frameon=False, loc="center left", bbox_to_anchor=(0.145, .787),
               ncol=2, fontsize=10.2, handletextpad=.35, columnspacing=.7)
    fig.text(0.038, .055,
             "A/B/C: 61 independent-source development images; 10,000 paired image-cluster bootstrap resamples. "
             "D is intentionally unfilled.",
             fontsize=9.8, color=MUTED)
    fig.savefig(OUT_PDF, bbox_inches=None)
    fig.savefig(OUT_SVG, bbox_inches=None)
    plt.close(fig)


if __name__ == "__main__":
    build()
