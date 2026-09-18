r"""Training-budget check (2026-09-18): the real-only v2 arm trained with a
3x budget (300 epochs) vs the protocol budget (100 epochs), evaluated on
test33 (clean) and test93 (reference).

Motivation: at 100 epochs the m-size real arms had not converged (train60
self-val mAP50 still climbing; the generated-data arms plateau by ~70-90
epochs). This check quantifies how much of the gen-vs-real gap is training
budget vs data scarcity.

Writes phase7_300ep_check.json (also embeds the 100-epoch numbers read from
phase7_realv2_summary.json for a direct comparison).
Windows note: __main__ guard + workers=0 (COMMANDS.md pitfall 2).
"""
import json
from pathlib import Path

from ultralytics import YOLO

V2_YAML = r"D:\gas_cylinders\real_photo\93_real_photos\v2_split\data_real_v2.yaml"   # test = test33
GEN_YAML = r"D:\gas_cylinders\Placement_Issues\gen493_split\data.yaml"              # test = 93 real photos
RUNS_300 = Path(r"D:\yolo\runs\detect\real60_300ep")
PHASE7 = Path(r"D:\yolo\phase7_realv2_summary.json")
OUT = Path(r"D:\yolo\phase7_300ep_check.json")
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
        p = RUNS_300 / w / "weights" / "last.pt"
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
                    "protocol": "budget check: real60 trained 300 epochs (3x) vs 100 epochs; "
                                "same v2 split, reported at last.pt"}}

    print("[1/2] real60_300ep last.pt on test33 (clean)", flush=True)
    res["real300_test33"] = run_group(V2_YAML, "test", "p7/real300_t33/{}")

    print("\n[2/2] real60_300ep last.pt on test93 (reference)", flush=True)
    res["real300_test93"] = run_group(GEN_YAML, "test", "p7/real300_t93/{}")

    # embed the 100-epoch v2 numbers for a direct comparison
    if PHASE7.exists():
        p7 = json.loads(PHASE7.read_text(encoding="utf-8"))
        res["ref_100ep_test33"] = p7.get("real60_last_test33")
        res["ref_100ep_test93"] = p7.get("real60_last_test93")
        res["ref_gen_last_test33"] = p7.get("gen_last_test33")
        res["ref_gen_last_test93"] = p7.get("gen_last_test93")

    def by(rows, tag):
        for r in rows or []:
            if r["tag"] == tag:
                return r
        return {}

    print("\n=== budget check: real arm 100ep vs 300ep (mAP50-95) ===", flush=True)
    for w in WEIGHTS:
        a33, b33 = by(res.get("ref_100ep_test33"), w), by(res["real300_test33"], w)
        a93, b93 = by(res.get("ref_100ep_test93"), w), by(res["real300_test93"], w)
        g33 = by(res.get("ref_gen_last_test33"), w)
        f = lambda r, k: f"{r[k]:.3f}" if k in r else "  -  "
        print(f"{w:8s} test33 100ep {f(a33,'mAP50-95')} -> 300ep {f(b33,'mAP50-95')} "
              f"(gen {f(g33,'mAP50-95')})   test93 100ep {f(a93,'mAP50-95')} -> 300ep {f(b93,'mAP50-95')}",
              flush=True)

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
