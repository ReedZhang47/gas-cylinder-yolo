r"""Phase 7 evaluation (2026-09-17, v2 protocol / 方案 A): real-photo v2 split
(train60 / test33) + final-epoch reporting (last.pt, fixed 100 epochs).

Groups:
  1. gen493 last.pt on test93   (headline; all 93 real photos are clean for
                                 generated-data models)
  2. gen493 last.pt on test33   (v2 clean column for the main comparison)
  3. gen493 best.pt on test33   (aux: v1 selection rule on the new test;
                                 not part of the v2 protocol)
  4. real60 last.pt on test93   (contaminated 60/93 -> inflated; reference only)
  5. real60 last.pt on test33   (clean; the main comparison vs group 2)

Writes phase7_realv2_summary.json.
Windows note: __main__ guard + workers=0 (COMMANDS.md pitfall 2).
"""
import json
from pathlib import Path

from ultralytics import YOLO

GEN_YAML = r"D:\gas_cylinders\Placement_Issues\gen493_split\data.yaml"               # test = 93 real photos
V2_YAML = r"D:\gas_cylinders\real_photo\93_real_photos\v2_split\data_real_v2.yaml"   # test = test33
GEN_RUNS = Path(r"D:\yolo\runs\detect\gen493")
REAL60_RUNS = Path(r"D:\yolo\runs\detect\real60")
OUT = Path(r"D:\yolo\phase7_realv2_summary.json")
WEIGHTS = ["yolov8s", "yolov8m", "yolo11s", "yolo11m", "yolo26s", "yolo26m"]


def val_one(weights: Path, data: str, split: str, name: str, imgsz: int = 640):
    model = YOLO(str(weights))
    r = model.val(data=data, split=split, imgsz=imgsz, batch=16,
                  device=0, workers=0, verbose=False, name=name)
    b = r.box
    return {"P": round(float(b.mp), 4), "R": round(float(b.mr), 4),
            "mAP50": round(float(b.map50), 4), "mAP50-95": round(float(b.map), 4)}


def run_group(tags, runs_root, ckpt, data, split, name_fmt):
    rows = []
    for w in tags:
        p = runs_root / w / "weights" / f"{ckpt}.pt"
        if not p.exists():
            rows.append({"tag": w, "error": f"missing {p}"})
            print(f"  {w}: MISSING {p}", flush=True)
            continue
        try:
            m = val_one(p, data, split, name_fmt.format(w))
            rows.append({"tag": w, **m})
            print(f"  {w}: P={m['P']:.3f} R={m['R']:.3f} "
                  f"mAP50={m['mAP50']:.3f} mAP50-95={m['mAP50-95']:.3f}", flush=True)
        except Exception as e:  # keep the long run going
            rows.append({"tag": w, "error": str(e)[:300]})
            print(f"  {w}: ERROR {str(e)[:200]}", flush=True)
    return rows


def compare(gen_rows, real_rows, title):
    print(f"\n=== {title} ===", flush=True)
    real_by = {r["tag"]: r for r in real_rows}
    wins = 0
    for g in gen_rows:
        r = real_by.get(g["tag"], {})
        if "error" in g or "error" in r:
            print(f"{g['tag']}: incomplete", flush=True)
            continue
        d = g["mAP50-95"] - r["mAP50-95"]
        wins += d > 0
        print(f"{g['tag']:8s} gen {g['mAP50']:.3f}/{g['mAP50-95']:.3f}  "
              f"real {r['mAP50']:.3f}/{r['mAP50-95']:.3f}  "
              f"delta50-95 {d:+.3f}", flush=True)
    print(f"gen wins {wins}/{len(gen_rows)} (mAP50-95)", flush=True)


def main():
    res = {"meta": {"date": "2026-09-17",
                    "protocol": "v2 (方案 A): real split train60/test33; report last.pt "
                                "(fixed 100 epochs, no validation-based selection)"}}

    print("[1/5] gen493 last.pt on test93 (93 real photos)", flush=True)
    res["gen_last_test93"] = run_group(WEIGHTS, GEN_RUNS, "last", GEN_YAML, "test", "p7/gen_last_t93/{}")

    print("\n[2/5] gen493 last.pt on test33 (v2 clean)", flush=True)
    res["gen_last_test33"] = run_group(WEIGHTS, GEN_RUNS, "last", V2_YAML, "test", "p7/gen_last_t33/{}")

    print("\n[3/5] gen493 best.pt on test33 (aux, v1 selection rule)", flush=True)
    res["gen_best_test33_aux"] = run_group(WEIGHTS, GEN_RUNS, "best", V2_YAML, "test", "p7/gen_best_t33/{}")

    print("\n[4/5] real60 last.pt on test93 (contaminated 60/93, reference)", flush=True)
    res["real60_last_test93"] = run_group(WEIGHTS, REAL60_RUNS, "last", GEN_YAML, "test", "p7/real60_last_t93/{}")

    print("\n[5/5] real60 last.pt on test33 (clean, main comparison)", flush=True)
    res["real60_last_test33"] = run_group(WEIGHTS, REAL60_RUNS, "last", V2_YAML, "test", "p7/real60_last_t33/{}")

    compare(res["gen_last_test33"], res["real60_last_test33"], "MAIN: gen493(last) vs real60(last) on test33")
    compare(res["gen_best_test33_aux"], res["real60_last_test33"], "AUX: gen493(best) vs real60(last) on test33")

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
