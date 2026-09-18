r"""v3 evaluation (2026-09-19): every arm on the independent v3 test set.

Arms (add rows to ARMS as they are trained):
  C_gen1085      -> runs/detect/gen1085   synthesis arm (train 868)
  C_gen493_scale -> runs/detect/gen493    first scale point (train 394)
  A_real93       -> runs/detect/real93v3  real-only arm (train 93)   [after training]
  B_aug93        -> runs/detect/aug93     real + classical aug (868) [after training]

Protocol: last.pt, imgsz 640 (fixed schedule, no val-based selection).
Writes phase10_v3_main.json. Windows note: __main__ guard + workers=0.
"""
import json
from pathlib import Path

from ultralytics import YOLO

TEST_YAML = r"D:\gas_cylinders\v3\data_test61.yaml"
OUT = Path(r"D:\yolo\phase10_v3_main.json")
WEIGHTS = ["yolov8s", "yolov8m", "yolo11s", "yolo11m", "yolo26s", "yolo26m"]
ARMS = {
    "C_gen1085": Path(r"D:\yolo\runs\detect\gen1085"),
    "C_gen493_scale": Path(r"D:\yolo\runs\detect\gen493"),
    # "A_real93": Path(r"D:\yolo\runs\detect\real93v3"),
    # "B_aug93": Path(r"D:\yolo\runs\detect\aug93"),
}


def main():
    res = {"meta": {"date": "2026-09-19",
                    "protocol": "v3: test = new_test_set (61 web images, independent); "
                                "last.pt, 100-epoch fixed schedule, imgsz 640"}}
    for arm, root in ARMS.items():
        rows = []
        print(f"== {arm}", flush=True)
        for w in WEIGHTS:
            p = root / w / "weights" / "last.pt"
            if not p.exists():
                rows.append({"tag": w, "error": f"missing {p}"})
                print(f"  {w}: MISSING", flush=True)
                continue
            try:
                r = YOLO(str(p)).val(data=TEST_YAML, split="test", imgsz=640, batch=16,
                                     device=0, workers=0, verbose=False,
                                     name=f"v3/{arm}_{w}")
                b = r.box
                m = {"P": round(float(b.mp), 4), "R": round(float(b.mr), 4),
                     "mAP50": round(float(b.map50), 4), "mAP50-95": round(float(b.map), 4)}
                rows.append({"tag": w, **m})
                print(f"  {w}: P={m['P']:.3f} R={m['R']:.3f} "
                      f"mAP50={m['mAP50']:.3f} mAP50-95={m['mAP50-95']:.3f}", flush=True)
            except Exception as e:
                rows.append({"tag": w, "error": str(e)[:300]})
                print(f"  {w}: ERROR {str(e)[:150]}", flush=True)
        res[arm] = rows

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
