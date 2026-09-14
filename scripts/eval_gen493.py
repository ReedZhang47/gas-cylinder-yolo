r"""gen493 evaluation (2026-09-14 rerun on the reviewed 493-image batch).

Same protocol as eval_gen500.py:
  1. gen493 val (99 generated images)  -> model selection view
  2. gen493 test (93 real photos)      -> headline number, imgsz=640
  3. real93 baseline on the same test  -> "real data only" reference, imgsz=640
     (caveat: 75/93 were in its train split -> biased toward the baseline)
  4. val18 clean subset (real93 val, 18 photos neither side trained on)
  5. inference imgsz scan {640,960,1280,1536} on all six gen493 weights

Writes phase6_gen493_summary.json and prints comparison tables.
Windows note: __main__ guard + workers=0 (COMMANDS.md pitfall 3).
"""
import json
from pathlib import Path

from ultralytics import YOLO

GEN_YAML = r"D:\gas_cylinders\Placement_Issues\gen493_split\data.yaml"
REAL93_YAML = r"D:\gas_cylinders\real_photo\93_real_photos\data.yaml"  # val = 18 photos
GEN_RUNS = Path(r"D:\yolo\runs\detect\gen493")
REAL93_RUNS = Path(r"D:\yolo\runs\detect\real93")
OUT = Path(r"D:\yolo\phase6_gen493_summary.json")
WEIGHTS = ["yolov8s", "yolov8m", "yolo11s", "yolo11m", "yolo26s", "yolo26m"]
SCAN_IMGSZ = [640, 960, 1280, 1536]


def val_one(best: Path, data: str, split: str, name: str, imgsz: int = 640):
    model = YOLO(str(best))
    batch = 8 if imgsz >= 1280 else 16
    r = model.val(data=data, split=split, imgsz=imgsz, batch=batch,
                  device=0, workers=0, verbose=False, name=name)
    b = r.box
    return {"P": round(float(b.mp), 4), "R": round(float(b.mr), 4),
            "mAP50": round(float(b.map50), 4), "mAP50-95": round(float(b.map), 4)}


def run_group(tag_list, runs_root, data, split, name_fmt, imgsz=640):
    rows = []
    for w in tag_list:
        best = runs_root / w / "weights" / "best.pt"
        if not best.exists():
            rows.append({"tag": w, "error": "missing best.pt"})
            print(f"  {w}: MISSING {best}", flush=True)
            continue
        try:
            m = val_one(best, data, split, name_fmt.format(w), imgsz)
            rows.append({"tag": w, **m})
            print(f"  {w}: P={m['P']:.3f} R={m['R']:.3f} "
                  f"mAP50={m['mAP50']:.3f} mAP50-95={m['mAP50-95']:.3f}", flush=True)
        except Exception as e:  # keep the long run going
            rows.append({"tag": w, "error": str(e)[:300]})
            print(f"  {w}: ERROR {str(e)[:200]}", flush=True)
    return rows


def table(rows, title):
    print(f"\n=== {title} ===", flush=True)
    for row in rows:
        if "error" in row:
            print(f"{row['tag']}: ERROR {row['error'][:120]}", flush=True)
        else:
            print(f"{row['tag']}: P={row['P']:.3f} R={row['R']:.3f} "
                  f"mAP50={row['mAP50']:.3f} mAP50-95={row['mAP50-95']:.3f}", flush=True)


def main():
    res = {"meta": {"date": "2026-09-14", "note": "rerun after review deleted 7 images (493 generated total)"}}

    print("[1/5] gen493 val (99 generated images)", flush=True)
    res["gen493_val"] = run_group(WEIGHTS, GEN_RUNS, GEN_YAML, "val", "gen493_val/{}")
    table(res["gen493_val"], "gen493 val (99 generated imgs)")

    print("\n[2/5] gen493 test (93 real photos) @ imgsz=640", flush=True)
    res["gen493_test"] = run_group(WEIGHTS, GEN_RUNS, GEN_YAML, "test", "gen493_test/{}")
    table(res["gen493_test"], "gen493 test (93 real imgs) @640")

    print("\n[3/5] real93 baseline on same test @ imgsz=640", flush=True)
    res["real93_test_baseline"] = run_group(WEIGHTS, REAL93_RUNS, GEN_YAML, "test", "real93_test_b/{}")
    table(res["real93_test_baseline"], "real93 baseline test (75/93 seen in training -> biased high)")

    print("\n[4/5] val18 clean subset (18 real photos, neither side trained on)", flush=True)
    gen18 = run_group(WEIGHTS, GEN_RUNS, REAL93_YAML, "val", "gen493_val18/{}")
    real18 = run_group(WEIGHTS, REAL93_RUNS, REAL93_YAML, "val", "real93_val18_b/{}")
    res["val18"] = ([{"weights": "gen493", **r} for r in gen18]
                    + [{"weights": "real93", **r} for r in real18])
    table(res["val18"], "val18 clean subset")

    print("\n[5/5] imgsz scan on gen493 test (all six weights)", flush=True)
    scan = []
    for s in SCAN_IMGSZ:
        print(f"--- imgsz={s} ---", flush=True)
        rows = run_group(WEIGHTS, GEN_RUNS, GEN_YAML, "test", f"gen493_scan/s{int(s)}{{}}", imgsz=s)
        for row in rows:
            row = dict(row)
            row["imgsz"] = s
            scan.append(row)
    res["imgsz_scan"] = scan

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
