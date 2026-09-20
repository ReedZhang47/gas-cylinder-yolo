r"""Legacy v3 P1 add-on: two-half checkpoint-selection study.

The main P1 number ("max over snapshots on the 61 images") is an upper bound on what
the 61val scheme can report, because it selects and reports on the SAME set. The
scheme as it would really be used has a smaller, but real, inflation: pick the best
checkpoint on one half of the images, then read the score on the other half.

This script evaluates a small set of snapshots (every 20 epochs plus the key ones) on
the first half and the second half of the 61 test images, and reports:
  - the epoch each half would pick
  - the score of the co-selected checkpoint on the *other* half (the optimistic path)
  - the score of the final checkpoint (epoch 300) on that same half (the last.pt path)

Windows note: __main__ guard + workers=0.
"""
import json
from pathlib import Path

from ultralytics import YOLO

SNAP_DIR = Path(r"D:\yolo\runs\detect\_p1_snapshots")
RUN_DIR = Path(r"D:\yolo\runs\detect\p1_real93_yolo26s")
TEST_TXT = Path(r"D:\gas_cylinders\v3\test61.txt")
OUT = Path(r"D:\yolo\runs\detect\p1_cross_split.json")

EPOCHS = [100, 140, 200, 240, 250, 260, 280, 290, 300]
HALVES = {"first_half": None, "second_half": None}


def write_subset_yaml(indices, tag):
    lines = [l.strip() for l in TEST_TXT.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    lst = Path(rf"D:\yolo\runs\detect\_p1_{tag}.txt")
    lst.write_text("\n".join(lines[i] for i in indices) + "\n", encoding="utf-8")
    y = Path(rf"D:\yolo\runs\detect\_p1_{tag}.yaml")
    y.write_text("names:\n  0: Placement Issues\npath: D:/gas_cylinders\n"
                 f"train: {lst}\nval: {lst}\ntest: {lst}\n", encoding="utf-8")
    return y


def score(weights, yaml_path, tag):
    r = YOLO(str(weights)).val(data=str(yaml_path), split="test", imgsz=640, batch=16,
                               device=0, workers=0, verbose=False, plots=False, name=f"p1x/{tag}")
    return round(float(r.box.map), 4)


def main():
    n = len([l for l in TEST_TXT.read_text(encoding="utf-8-sig").splitlines() if l.strip()])
    halves = {
        "first_half": write_subset_yaml(list(range(0, n // 2)), "first"),
        "second_half": write_subset_yaml(list(range(n // 2, n)), "second"),
    }
    table = {}
    for ep in EPOCHS:
        w = RUN_DIR / "weights" / "last.pt" if ep == 300 else SNAP_DIR / f"epoch{ep}.pt"
        if not w.exists():
            print(f"epoch {ep}: missing {w}", flush=True)
            continue
        row = {}
        for hname, hyaml in halves.items():
            row[hname] = score(w, hyaml, f"{hname}_e{ep}")
        table[ep] = row
        print(f"epoch {ep:>3}: " + "  ".join(f"{k}={v:.4f}" for k, v in row.items()), flush=True)

    res = {"protocol": "pick best epoch on one half of the 61 images, then read the other half",
           "per_epoch": table, "summary": {}}
    for hname, other in (("first_half", "second_half"), ("second_half", "first_half")):
        pick = max(table, key=lambda e: table[e][hname])
        last_score = table[300][other]
        picked_score = table[pick][other]
        res["summary"][hname] = {
            "picks_epoch": pick,
            "picked_epoch_score_on_other_half": picked_score,
            "final_epoch_score_on_other_half": last_score,
            "selection_gain_on_other_half": round(picked_score - last_score, 4),
        }
        print(f"\n[{hname}] picks epoch {pick}; on the OTHER half: picked={picked_score:.4f} "
              f"vs final(300)={last_score:.4f} -> selection gain {picked_score - last_score:+.4f}", flush=True)

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
