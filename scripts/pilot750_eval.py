r"""Extended saturation pilot: 750-epoch run, sparse snapshot scoring.

Follow-up to the 450-epoch pilot (which showed +0.0435 mAP50-95 gained between
epochs 300 and 400 on the 61-image set - i.e. still not saturated). Same setup,
only the budget changes: A arm real93 (93 imgs, full) + yolo26s, patience=0,
save_period=10, imgsz 640, batch 16.

Snapshot scoring is sparse to keep GPU time bounded:
  epochs 10, 50, 100 (early ramp) + every 50 from 150 to 750
The run's self-validation curve (every epoch, on the 93 training images) is read
from results.csv and used only as a trend reference - the 450-epoch pilot showed
self-val flattens earlier than the independent set, so it cannot decide saturation.

Outputs runs\detect\pilot_saturation_750.json with the curve, band gains, the
saturation epoch under a tolerance, and the last-vs-best snapshot comparison.

Windows note: __main__ guard + workers=0.
"""
import csv
import json
from pathlib import Path

import numpy as np
from ultralytics import YOLO

ROOT = Path(r"D:\yolo\runs\detect\_pilot_sat750")
RUN = ROOT / "yolo26s"
SNAPS = ROOT / "snapshots"
TEST_YAML = r"D:\gas_cylinders\v3\data_test61.yaml"
OUT = Path(r"D:\yolo\runs\detect\pilot_saturation_750.json")
OLD450 = Path(r"D:\yolo\runs\detect\pilot_saturation.json")
EVAL_EPOCHS = [10, 50, 100] + list(range(150, 751, 50))
TOL = 0.01
TOTAL = 750


def score(weights: Path, tag: str):
    r = YOLO(str(weights)).val(data=TEST_YAML, split="test", imgsz=640, batch=16,
                               device=0, workers=0, verbose=False, plots=False,
                               name=f"pilot750/{tag}")
    b = r.box
    return {"mAP50": round(float(b.map50), 4), "mAP50-95": round(float(b.map), 4)}


def saturated_at(epochs, vals, tol=TOL):
    best = -1.0
    sat = epochs[-1]
    for i in range(len(vals) - 1, -1, -1):
        if vals[i] > best + tol:
            sat = epochs[i]
            break
        best = max(best, vals[i])
    return sat


def band(epochs, vals, lo, hi):
    a = next((v for e, v in zip(epochs, vals) if e >= lo), None)
    b = next((v for e, v in zip(epochs, vals) if e >= hi), None)
    return None if a is None or b is None else round(b - a, 4)


def main():
    curve = []
    for ep in EVAL_EPOCHS:
        p = SNAPS / f"epoch{ep}.pt"
        if not p.exists():
            print(f"epoch {ep}: missing", flush=True)
            continue
        m = score(p, f"e{ep}")
        curve.append({"epoch": ep, **m})
        print(f"  epoch {ep:>3}: mAP50={m['mAP50']:.4f} mAP50-95={m['mAP50-95']:.4f}", flush=True)

    last_m = score(RUN / "weights" / "last.pt", "last750")
    print(f"  last (750): mAP50={last_m['mAP50']:.4f} mAP50-95={last_m['mAP50-95']:.4f}", flush=True)

    rows = list(csv.DictReader(open(RUN / "results.csv")))
    ep_all = [int(r["epoch"]) for r in rows]
    self95 = [float(r["metrics/mAP50-95(B)"]) for r in rows]
    sm9 = list(np.convolve(self95, np.ones(9) / 9, mode="valid"))

    days = [c["epoch"] for c in curve]
    vs = [c["mAP50-95"] for c in curve]
    res = {
        "setup": f"A arm real93 (93 imgs, full) + yolo26s, {TOTAL} epochs, patience=0, "
                 "save_period=10, imgsz 640, batch 16; sparse snapshots scored on the 61-image set",
        "eval_epochs": EVAL_EPOCHS,
        "curve": curve,
        "last_epoch750": last_m,
        "best_snapshot": curve[int(np.argmax(vs))],
        "bands_61img": {f"{lo}->{hi}": band(days, vs, lo, hi)
                        for lo, hi in ((100, 200), (200, 300), (300, 400), (400, 500),
                                       (500, 600), (600, 700), (700, 750))},
        "bands_selfval": {f"{lo}->{hi}": band(ep_all, self95, lo, hi)
                          for lo, hi in ((100, 200), (200, 300), (300, 400), (400, 500),
                                         (500, 600), (600, 700), (700, 750))},
        "saturation_61img_tol0.01": saturated_at(days, vs),
        "saturation_selfval_tol0.01": saturated_at(ep_all, self95),
        "selfval_best_epoch": ep_all[int(np.argmax(self95))],
        "selfval_last": round(self95[-1], 4),
        "selfval_smoothed_last50_vs_prev50": round(
            float(np.mean(sm9[-50:]) - np.mean(sm9[-100:-50])), 5),
    }

    # cross-check against the 450-epoch pilot at the epochs they share
    if OLD450.exists():
        old = json.loads(OLD450.read_text(encoding="utf-8"))
        shared = [(c["epoch"], c["mAP50-95"],
                   next(o["mAP50-95"] for o in old["curve"] if o["epoch"] == c["epoch"]))
                  for c in curve if any(o["epoch"] == c["epoch"] for o in old["curve"])]
        if shared:
            d = [a - b for _, a, b in shared]
            res["vs_450pilot_shared_epochs"] = {
                "n": len(shared), "mean": round(float(np.mean(d)), 4),
                "std": round(float(np.std(d)), 4),
                "min": round(float(np.min(d)), 4), "max": round(float(np.max(d)), 4),
            }
            print(f"\nvs 450-epoch pilot on {len(shared)} shared epochs: mean {np.mean(d):+.4f} "
                  f"std {np.std(d):.4f} ({np.min(d):+.4f} .. {np.max(d):+.4f})", flush=True)

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT}", flush=True)
    print("bands (61-img)  :", res["bands_61img"], flush=True)
    print("bands (self-val):", res["bands_selfval"], flush=True)
    print(f"saturation: 61-img -> epoch {res['saturation_61img_tol0.01']}, "
          f"self-val -> epoch {res['saturation_selfval_tol0.01']}", flush=True)
    print(f"last(750) {last_m['mAP50-95']:.4f} vs best snapshot "
          f"ep{res['best_snapshot']['epoch']} {res['best_snapshot']['mAP50-95']:.4f}", flush=True)


if __name__ == "__main__":
    main()
