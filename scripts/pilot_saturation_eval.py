r"""Saturation pilot analysis: is 300 epochs the budget, or does more training still help?

Input: the 450-epoch run produced by scripts\pilot_saturation.ps1 (A arm real93 full,
yolo26s, patience=0, save_period=10). Every snapshot is scored on the 61-image network
set, and the run's own self-validation curve is read from results.csv.

Outputs:
  - the snapshot curve on the 61 images (epochs 10..450)
  - the self-validation curve over all 450 epochs (dense, 1-epoch resolution)
  - band gains (100->200, 200->300, 300->400, 400->450), both curves
  - saturation epoch: first epoch after which the running best is never beaten by
    more than TOL (default 0.01) again - i.e. "the curve has flattened"
  - comparison against the P1 300-epoch run over the shared epochs

Windows note: __main__ guard + workers=0.
"""
import csv
import json
import statistics as st
from pathlib import Path

import numpy as np
from ultralytics import YOLO

ROOT = Path(r"D:\yolo\runs\detect\_pilot_sat")
RUN = ROOT / "yolo26s"
SNAPS = ROOT / "snapshots"
TEST_YAML = r"D:\gas_cylinders\v3\data_test61.yaml"
P1_JSON = Path(r"D:\yolo\runs\detect\p1_61val_vs_61test.json")
OUT = Path(r"D:\yolo\runs\detect\pilot_saturation.json")
TOL = 0.01          # "flattened" tolerance in mAP50-95
TOTAL = 450


def score(weights: Path, tag: str):
    r = YOLO(str(weights)).val(data=TEST_YAML, split="test", imgsz=640, batch=16,
                               device=0, workers=0, verbose=False, plots=False,
                               name=f"pilot/{tag}")
    b = r.box
    return {"mAP50": round(float(b.map50), 4), "mAP50-95": round(float(b.map), 4)}


def saturated_at(epochs, vals, tol=TOL):
    """First epoch after which no later epoch beats the running max by more than tol."""
    best = -1.0
    sat = epochs[-1]
    for i in range(len(vals) - 1, -1, -1):
        if vals[i] > best + tol:
            sat = epochs[i]
            break
        best = max(best, vals[i])
    return sat


def band_gain(epochs, vals, lo, hi):
    a = next((v for e, v in zip(epochs, vals) if e >= lo), None)
    b = next((v for e, v in zip(epochs, vals) if e >= hi), None)
    return None if a is None or b is None else round(b - a, 4)


def main():
    snaps = sorted(SNAPS.glob("epoch*.pt"), key=lambda p: int(p.stem.replace("epoch", "")))
    print(f"snapshots: {len(snaps)}", flush=True)

    curve = []
    for p in snaps:
        ep = int(p.stem.replace("epoch", ""))
        m = score(p, f"e{ep}")
        curve.append({"epoch": ep, **m})
        if ep % 50 == 0:
            print(f"  epoch {ep:>3}: mAP50={m['mAP50']:.4f} mAP50-95={m['mAP50-95']:.4f}", flush=True)

    last_m = score(RUN / "weights" / "last.pt", "last450")
    print(f"  last (450): mAP50={last_m['mAP50']:.4f} mAP50-95={last_m['mAP50-95']:.4f}", flush=True)

    rows = list(csv.DictReader(open(RUN / "results.csv")))
    ep_all = [int(r["epoch"]) for r in rows]
    self_all = [float(r["metrics/mAP50-95(B)"]) for r in rows]
    self_smooth = list(np.convolve(self_all, np.ones(9) / 9, mode="valid"))   # centred-ish 9-epoch mean
    print(f"\nself-val (93 train imgs): last {self_all[-1]:.4f}, best ep{ep_all[int(np.argmax(self_all))]} "
          f"{max(self_all):.4f}", flush=True)

    days = [c["epoch"] for c in curve]
    vs = [c["mAP50-95"] for c in curve]
    res = {
        "setup": f"A arm real93 (93 imgs, full) + yolo26s, {TOTAL} epochs, patience=0, "
                 "save_period=10, imgsz 640, batch 16; snapshots scored on the 61-image set",
        "curve": curve,
        "last_epoch450": last_m,
        "best_snapshot": curve[int(np.argmax(vs))],
        "snapshot_spread": {"min": float(min(vs)), "max": float(max(vs)), "std": float(np.std(vs))},
        "bands_61img": {f"{lo}->{hi}": band_gain(days, vs, lo, hi)
                        for lo, hi in ((100, 200), (200, 300), (300, 400), (400, 450))},
        "bands_selfval": {f"{lo}->{hi}": band_gain(ep_all, self_all, lo, hi)
                          for lo, hi in ((100, 200), (200, 300), (300, 400), (400, 450))},
        "saturation_61img_tol0.01": saturated_at(days, vs),
        "saturation_selfval_tol0.01": saturated_at(ep_all, self_all),
        "selfval_last20_slope_per10": round((self_all[-1] - self_all[-21]) / 2, 5),
        "selfval_smoothed_last20_slope_per10": round(
            (st.mean(self_smooth[-10:]) - st.mean(self_smooth[-20:-10])), 5),
    }

    if P1_JSON.exists():
        p1 = json.loads(P1_JSON.read_text(encoding="utf-8"))
        shared = [c for c in curve if any(x["epoch"] == c["epoch"] for x in p1["curve"])]
        d = [c["mAP50-95"] - next(x["mAP50-95"] for x in p1["curve"] if x["epoch"] == c["epoch"])
             for c in shared]
        res["vs_p1_same_epochs"] = {
            "epochs": [c["epoch"] for c in shared],
            "delta_mean": round(float(st.mean(d)), 4),
            "delta_min": round(float(min(d)), 4),
            "delta_max": round(float(max(d)), 4),
        }
        print(f"\nvs P1 300-epoch run on shared epochs: mean delta {st.mean(d):+.4f} "
              f"({min(d):+.4f} .. {max(d):+.4f})", flush=True)

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT}", flush=True)
    print("band gains (61-img):", res["bands_61img"], flush=True)
    print("band gains (self-val):", res["bands_selfval"], flush=True)
    print(f"saturation: 61-img tol0.01 -> epoch {res['saturation_61img_tol0.01']}; "
          f"self-val -> epoch {res['saturation_selfval_tol0.01']}", flush=True)


if __name__ == "__main__":
    main()
