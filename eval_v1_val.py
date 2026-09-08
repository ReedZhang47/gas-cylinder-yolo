r"""v1 labeler evaluation: run the val split (18 real photos) on each real93
best.pt, write phase4_v1_summary.json and print a comparison table.

Windows note: must keep the __main__ guard (DataLoader spawns child processes
that re-import this module) and workers=0 (18 images don't need workers)."""
import json
from pathlib import Path

from ultralytics import YOLO

DATA = r"D:\gas_cylinders\real_photo\93_real_photos\data.yaml"
RUNS = Path(r"D:\yolo\runs\detect\real93")
OUT = Path(r"D:\yolo\phase4_v1_summary.json")
WEIGHTS = ["yolov8s", "yolov8m", "yolo11s", "yolo11m", "yolo26s", "yolo26m"]


def main():
    rows = []
    for w in WEIGHTS:
        best = RUNS / w / "weights" / "best.pt"
        if not best.exists():
            rows.append({"tag": w, "error": "missing best.pt"})
            continue
        model = YOLO(str(best))
        r = model.val(data=DATA, split="val", device=0, workers=0, verbose=False,
                      name=f"real93_val/{w}")
        b = r.box
        rows.append({"tag": w, "P": float(b.mp), "R": float(b.mr),
                     "mAP50": float(b.map50), "mAP50-95": float(b.map)})

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== real93 val summary (18 imgs, 11 pos 28 boxes / 7 neg) ===")
    for row in rows:
        if "error" in row:
            print(f"{row['tag']}: ERROR {row['error']}")
        else:
            print(f"{row['tag']}: P={row['P']:.3f} R={row['R']:.3f} "
                  f"mAP50={row['mAP50']:.3f} mAP50-95={row['mAP50-95']:.3f}")
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
