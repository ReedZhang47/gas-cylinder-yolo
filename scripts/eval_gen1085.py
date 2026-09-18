r"""Phase 8 evaluation (2026-09-18): gen1085 (merged 493+592, train=868) vs
gen493 (train=394) vs real60 (60 real), all at last.pt under the v2 protocol.

Groups:
  1. gen1085 last.pt on test93   (headline; all 93 real photos clean for gen models)
  2. gen1085 last.pt on test33   (v2 clean column)
  + embeds the phase-7 numbers (gen493 / real60) for the scale comparison.

Writes phase8_gen1085_summary.json.
Windows note: __main__ guard + workers=0 (COMMANDS.md pitfall 2).
"""
import json
from pathlib import Path

from ultralytics import YOLO

GEN1085_YAML = r"D:\gas_cylinders\gen1085_split\data.yaml"                          # test = 93 real photos
V2_YAML = r"D:\gas_cylinders\real_photo\93_real_photos\v2_split\data_real_v2.yaml"   # test = test33
RUNS = Path(r"D:\yolo\runs\detect\gen1085")
PHASE7 = Path(r"D:\yolo\phase7_realv2_summary.json")
OUT = Path(r"D:\yolo\phase8_gen1085_summary.json")
WEIGHTS = ["yolov8s", "yolov8m", "yolo11s", "yolo11m", "yolo26s", "yolo26m"]


def val_one(weights: Path, data: str, split: str, name: str):
    model = YOLO(str(weights))
    r = model.val(data=data, split=split, imgsz=640, batch=16,
                  device=0, workers=0, verbose=False, name=name)
    b = r.box
    return {"P": round(float(b.mp), 4), "R": round(float(b.mr), 4),
            "mAP50": round(float(b.map50), 4), "mAP50-95": round(float(b.map), 4)}


def run_group(data, split, name_fmt):
    rows = []
    for w in WEIGHTS:
        p = RUNS / w / "weights" / "last.pt"
        if not p.exists():
            rows.append({"tag": w, "error": f"missing {p}"})
            print(f"  {w}: MISSING {p}", flush=True)
            continue
        try:
            m = val_one(p, data, split, name_fmt.format(w))
            rows.append({"tag": w, **m})
            print(f"  {w}: P={m['P']:.3f} R={m['R']:.3f} "
                  f"mAP50={m['mAP50']:.3f} mAP50-95={m['mAP50-95']:.3f}", flush=True)
        except Exception as e:
            rows.append({"tag": w, "error": str(e)[:300]})
            print(f"  {w}: ERROR {str(e)[:200]}", flush=True)
    return rows


def main():
    res = {"meta": {"date": "2026-09-18",
                    "protocol": "v2: report last.pt (fixed 100 epochs, no val selection); "
                                "gen1085 = merged 493+592 reviewed generated images"}}

    print("[1/2] gen1085 last.pt on test93 (93 real photos)", flush=True)
    res["gen1085_last_test93"] = run_group(GEN1085_YAML, "test", "p8/gen1085_t93/{}")

    print("\n[2/2] gen1085 last.pt on test33 (v2 clean)", flush=True)
    res["gen1085_last_test33"] = run_group(V2_YAML, "test", "p8/gen1085_t33/{}")

    def by(rows, tag):
        for r in rows or []:
            if r["tag"] == tag:
                return r
        return {}

    if PHASE7.exists():
        p7 = json.loads(PHASE7.read_text(encoding="utf-8"))
        res["ref_gen493_test93"] = p7.get("gen_last_test93")
        res["ref_gen493_test33"] = p7.get("gen_last_test33")
        res["ref_real60_test33"] = p7.get("real60_last_test33")

    print("\n=== scale curve (mAP50-95) ===", flush=True)
    print(f"{'weight':9s} {'real60 (60)':13s} {'gen493 (394)':14s} {'gen1085 (868)':14s} "
          f"{'t93: gen493->1085':19s}", flush=True)
    for w in WEIGHTS:
        r33 = by(res.get("ref_real60_test33"), w)
        g4_33 = by(res.get("ref_gen493_test33"), w)
        g8_33 = by(res["gen1085_last_test33"], w)
        g4_93 = by(res.get("ref_gen493_test93"), w)
        g8_93 = by(res["gen1085_last_test93"], w)
        f = lambda r: f"{r['mAP50-95']:.3f}" if "mAP50-95" in r else "  -  "
        print(f"{w:9s} {f(r33):13s} {f(g4_33):14s} {f(g8_33):14s} "
              f"{f(g4_93)} -> {f(g8_93)}", flush=True)

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
