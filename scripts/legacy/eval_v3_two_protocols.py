r"""Legacy v3 same-set evaluation retained for reproducibility.

Every arm trains with save_period=10, so each weight folder holds ~30 snapshots
(epoch10..epoch300) plus last.pt. Scoring all snapshots on the 61-image network set
gives ONE curve per weight, from which both protocols are read:

  61test reading = last.pt (epoch 300, no selection)      -> the generalisation number
  61val  reading = argmax over snapshots (val-based pick) -> the selection metric

Per weight the script records both numbers, the selected epoch, the selection gain
and the top-3 epochs; per arm it averages the gain. Results go to experiments\ (the
tracked directory), never to runs\ or logs\ (both gitignored).

Usage:
  & D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_two_protocols.py --arm real93v3
  ... --arm all          # real93v3, aug93v3, gen1085v3 in one go

Windows note: __main__ guard + workers=0.
"""
import argparse
import json
import statistics as st
from pathlib import Path

from ultralytics import YOLO

RUNS = Path(r"D:\yolo\runs\detect")
OUT_DIR = Path(r"D:\yolo\experiments\two_protocols")
TEST_YAML = r"D:\gas_cylinders\v3\data_test61.yaml"
WEIGHTS = ["yolov8s", "yolov8m", "yolo11s", "yolo11m", "yolo26s", "yolo26m"]
ARM_DIRS = {
    "real93v3": "A_real93",
    "aug93v3": "B_aug93",
    "gen1085v3": "C_gen1085",
    "gen493v3": "scale_gen493",
}
MAIN_ARMS = ["real93v3", "aug93v3", "gen1085v3"]
TRAIN_SIZES = {"real93v3": 93, "aug93v3": 1085, "gen1085v3": 1085, "gen493v3": 493}


def score(weights: Path, tag: str):
    r = YOLO(str(weights)).val(data=TEST_YAML, split="test", imgsz=640, batch=16,
                               device=0, workers=0, verbose=False, plots=False,
                               project=str(RUNS), name=f"two_protocols/{tag}", exist_ok=True)
    b = r.box
    return {"P": round(float(b.mp), 4), "R": round(float(b.mr), 4),
            "mAP50": round(float(b.map50), 4), "mAP50-95": round(float(b.map))}


def epoch_of(p: Path) -> int:
    return 300 if p.stem == "last" else int(p.stem.replace("epoch", ""))


def run_arm(arm: str) -> dict:
    out = {"arm": arm, "label": ARM_DIRS[arm], "train_images": TRAIN_SIZES[arm], "weights": {}}
    for w in WEIGHTS:
        folder = RUNS / arm / w
        snaps = sorted(folder.glob("weights/epoch*.pt"), key=epoch_of)
        last = folder / "weights" / "last.pt"
        if not snaps and not last.exists():
            print(f"  {w}: MISSING ({folder})", flush=True)
            out["weights"][w] = {"error": "missing run"}
            continue
        curve = []
        for p in snaps:
            m = score(p, f"{arm}_{w}_e{epoch_of(p)}")
            curve.append({"epoch": epoch_of(p), **m})
            if epoch_of(p) % 50 == 0:
                print(f"  {w} epoch {epoch_of(p):>3}: mAP50-95 {m['mAP50-95']:.4f}", flush=True)
        last_m = score(last, f"{arm}_{w}_last") if last.exists() else None
        m95 = [c["mAP50-95"] for c in curve]
        best_i = max(range(len(curve)), key=lambda i: m95[i]) if curve else None
        rec = {
            "n_snapshots": len(curve),
            "curve": curve,
            "last_epoch300": last_m,
            "best_snapshot": curve[best_i] if best_i is not None else None,
            "top3_epochs": sorted(curve, key=lambda c: -c["mAP50-95"])[:3] if curve else [],
        }
        if curve and last_m:
            rec["selection_gain_mAP50-95"] = round(curve[best_i]["mAP50-95"] - last_m["mAP50-95"], 4)
            rec["selection_gain_mAP50"] = round(curve[best_i]["mAP50"] - last_m["mAP50"], 4)
        out["weights"][w] = rec
        print(f"  {w}: 61test(last) {last_m['mAP50-95'] if last_m else float('nan'):.4f}  "
              f"61val(ep{curve[best_i]['epoch'] if best_i is not None else '-'}) "
              f"{curve[best_i]['mAP50-95'] if best_i is not None else float('nan'):.4f}  "
              f"gain {rec.get('selection_gain_mAP50-95', float('nan')):+.4f}", flush=True)

    gains = [r["selection_gain_mAP50-95"] for r in out["weights"].values()
             if "selection_gain_mAP50-95" in r]
    if gains:
        out["summary"] = {"n": len(gains), "mean_gain": round(st.mean(gains), 4),
                          "min_gain": min(gains), "max_gain": max(gains),
                          "last_mean_mAP50-95": round(st.mean(
                              [r["last_epoch300"]["mAP50-95"] for r in out["weights"].values()
                               if r.get("last_epoch300")]), 4),
                          "best_mean_mAP50-95": round(st.mean(
                              [r["best_snapshot"]["mAP50-95"] for r in out["weights"].values()
                               if r.get("best_snapshot")]), 4)}
        print(f"  [{arm}] mean selection gain {out['summary']['mean_gain']:+.4f} "
              f"({out['summary']['min_gain']:+.4f} .. {out['summary']['max_gain']:+.4f})", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="all", choices=[*ARM_DIRS, "all"])
    args = ap.parse_args()
    arms = MAIN_ARMS if args.arm == "all" else [args.arm]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = {}
    for arm in arms:
        print(f"== {arm} ({ARM_DIRS[arm]}, train {TRAIN_SIZES[arm]} imgs)", flush=True)
        result[arm] = run_arm(arm)
    out = OUT_DIR / ("two_protocols_all.json" if args.arm == "all" else f"two_protocols_{args.arm}.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {out}", flush=True)


if __name__ == "__main__":
    main()
