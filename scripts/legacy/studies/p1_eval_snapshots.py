r"""Legacy v3 P1 snapshot evaluation.

Called by scripts\p1_run.ps1 after a 300-epoch run with save_period=10. For each
snapshot (epoch10.pt ... epoch300.pt) plus last.pt it records mAP50 / mAP50-95 on
the v3 test list, then derives the three quantities documented in
docs/archive/PLAN_61VAL.md:

  1. 61test reading  - value of the final checkpoint (what the last.pt protocol reports)
  2. 61val reading   - max over snapshots (what the val-selection protocol would report),
                       together with the inflation over the final checkpoint
  3. overfitting     - which epoch peaks, and the shape of the snapshot curve

Also reports selection stability: pick the best snapshot using only the first half /
second half / odd / even images of the 61, and see whether the choice agrees.

Windows note: __main__ guard + workers=0.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from ultralytics import YOLO

SNAP_DIR = Path(r"D:\yolo\runs\detect\_p1_snapshots")
RUN_DIR = Path(r"D:\yolo\runs\detect\p1_real93_yolo26s")
TEST_YAML = r"D:\gas_cylinders\v3\data_test61.yaml"
TEST_TXT = Path(r"D:\gas_cylinders\v3\test61.txt")
OUT = Path(r"D:\yolo\runs\detect\p1_61val_vs_61test.json")


def epoch_of(p: Path) -> int:
    return 300 if p.stem == "last" else int(p.stem.replace("epoch", ""))


def val_on(weights: Path, name: str):
    r = YOLO(str(weights)).val(data=TEST_YAML, split="test", imgsz=640, batch=16,
                               device=0, workers=0, verbose=False, plots=False,
                               name=f"p1_check/{name}")
    b = r.box
    return {"P": float(b.mp), "R": float(b.mr),
            "mAP50": float(b.map50), "mAP50-95": float(b.map)}


def val_on_subset(weights: Path, img_indices, name: str):
    """Evaluate on a subset of test images (used for the stability check)."""
    lines = [l.strip() for l in TEST_TXT.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    subset = [lines[i] for i in img_indices]
    tmp = Path(r"D:\yolo\runs\detect\_p1_subset.txt")
    tmp.write_text("\n".join(subset) + "\n", encoding="utf-8")
    tmp_yaml = Path(r"D:\yolo\runs\detect\_p1_subset.yaml")
    tmp_yaml.write_text("names:\n  0: Placement Issues\npath: D:/gas_cylinders\n"
                        f"train: {tmp}\nval: {tmp}\ntest: {tmp}\n", encoding="utf-8")
    return _val_yaml(weights, tmp_yaml, name)


def _val_yaml(weights: Path, yaml_path: Path, name: str):
    r = YOLO(str(weights)).val(data=str(yaml_path), split="test", imgsz=640, batch=16,
                               device=0, workers=0, verbose=False, plots=False,
                               name=f"p1_check/{name}")
    b = r.box
    return {"mAP50": float(b.map50), "mAP50-95": float(b.map)}


def main():
    snaps = sorted(SNAP_DIR.glob("epoch*.pt"), key=epoch_of)
    last = RUN_DIR / "weights" / "last.pt"
    print(f"snapshots: {len(snaps)} (+last.pt={last.exists()})", flush=True)

    curve = []
    for p in snaps:
        m = val_on(p, p.stem)
        curve.append({"epoch": epoch_of(p), **m})
        print(f"  epoch {epoch_of(p):>3}: mAP50={m['mAP50']:.4f} mAP50-95={m['mAP50-95']:.4f}", flush=True)

    last_m = val_on(last, "last_epoch300") if last.exists() else None
    if last_m:
        print(f"  last  (300): mAP50={last_m['mAP50']:.4f} mAP50-95={last_m['mAP50-95']:.4f}", flush=True)

    m95 = [c["mAP50-95"] for c in curve]
    best_i = int(np.argmax(m95))
    res = {
        "setup": "A arm real93 (93 imgs, full) + yolo26s, 300 epochs, patience=0, "
                 "save_period=10, imgsz 640, batch 16; snapshots scored on the 61-image network set",
        "curve": curve,
        "last_epoch300": last_m,
        "best_snapshot": curve[best_i],
        "report_61test": {"epoch": 300, **(last_m or {})},
        "report_61val": {**curve[best_i]},
        "inflation_61val_over_61test_mAP50-95": (curve[best_i]["mAP50-95"] - (last_m or curve[-1])["mAP50-95"]),
        "spread_mAP50-95": {"min": float(np.min(m95)), "max": float(np.max(m95)),
                            "std": float(np.std(m95))},
    }
    if last_m:
        res["inflation_61val_over_61test_mAP50"] = curve[best_i]["mAP50"] - last_m["mAP50"]

    # selection stability: pick the best snapshot using only half of the 61 images
    n = len([l for l in TEST_TXT.read_text(encoding="utf-8-sig").splitlines() if l.strip()])
    splits = {"first_half": list(range(0, n // 2)), "second_half": list(range(n // 2, n))}
    stability = {}
    for name, idx in splits.items():
        sub = [(c["epoch"], val_on_subset(SNAP_DIR / f"epoch{c['epoch']}.pt", idx, f"{name}_e{c['epoch']}")
                ["mAP50-95"]) for c in curve]
        pick = max(sub, key=lambda t: t[1])
        stability[name] = {"pick_epoch": pick[0], "subset_best_mAP50-95": pick[1]}
        print(f"  [{name}] picks epoch {pick[0]} (subset mAP50-95 {pick[1]:.4f})", flush=True)
    res["selection_stability"] = stability

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT}", flush=True)
    print(f"61test (last@300) mAP50-95 = {(last_m or curve[-1])['mAP50-95']:.4f}", flush=True)
    print(f"61val  (best snapshot, ep{curve[best_i]['epoch']}) mAP50-95 = {curve[best_i]['mAP50-95']:.4f} "
          f"-> inflation {res['inflation_61val_over_61test_mAP50-95']:+.4f}", flush=True)


if __name__ == "__main__":
    main()
