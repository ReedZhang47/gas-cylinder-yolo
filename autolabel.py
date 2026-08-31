r"""auto-label gas-cylinder images with a trained weight -> YOLO-format labels.

Output convention matches the first500 dataset:
  - one .txt per image, same basename, 5 columns: class cx cy w h (normalized)
  - images with no detection get an EMPTY .txt (negative sample / keep 1:1 correspondence)
  - default labels dir: <source>/../labels ; class id comes from the model (0: Upside-down)
  - a data.yaml (names/nc/path/train) is always written into the labels output dir

CVAT import (Ultralytics YOLO): use --cvat-dir <dir> to assemble the full dataset
  structure required by CVAT (images/train + labels/train + data.yaml + train.txt),
  then zip that dir and upload it to CVAT.

Usage:
  & D:\yolo\.venv\Scripts\python.exe D:\yolo\autolabel.py --source <图片目录> \
        [--model <best.pt>] [--labels-out <目录>] [--cvat-dir <目录>] \
        [--conf 0.25] [--iou 0.45] [--imgsz 640] [--overwrite]
"""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def write_yaml(path: Path, names: dict):
    lines = ["path: .", "train: train.txt"]
    if names:
        lines.append("nc: {}".format(len(names)))
        lines.append("names:")
        for cid, cname in sorted(names.items()):
            lines.append(f"  {cid}: {cname}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Auto-label gas cylinder images (Upside-down class 0)")
    ap.add_argument("--source", required=True, help="directory containing new images")
    ap.add_argument("--labels-out", default=None, help="label output dir (default: <source>/../labels)")
    ap.add_argument("--cvat-dir", default=None, help="also assemble a CVAT-importable dataset into this dir")
    ap.add_argument("--model", default=r"D:\yolo\runs\detect\first500\yolo11m\weights\best.pt")
    ap.add_argument("--conf", type=float, default=0.25, help="detection confidence threshold")
    ap.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--overwrite", action="store_true", help="overwrite existing label files (default: skip)")
    args = ap.parse_args()

    src = Path(args.source)
    if not src.is_dir():
        raise SystemExit(f"source is not a directory: {src}")
    out = Path(args.labels_out) if args.labels_out else src.parent / "labels"
    out.mkdir(parents=True, exist_ok=True)

    imgs = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS)
    if not imgs:
        raise SystemExit(f"no images (*.png/jpg/jpeg/webp/bmp/tif) found in {src}")
    print(f"images: {len(imgs)}  labels -> {out}  model: {args.model}  conf={args.conf} iou={args.iou}")

    model = YOLO(args.model)
    names = {int(k): v for k, v in model.names.items()}

    def make_lines(p: Path) -> tuple[list[str], Path]:
        """Return (label lines, label path). Generates via model if label missing."""
        lab = out / (p.stem + ".txt")
        if lab.exists() and not args.overwrite:
            raw = lab.read_text(encoding="utf-8")
            lines = [ln for ln in raw.splitlines() if ln.strip()]
            return lines, lab
        res = model.predict(str(p), conf=args.conf, iou=args.iou, imgsz=args.imgsz, verbose=False)[0]
        lines = []
        if res.boxes is not None and len(res.boxes):
            cls = res.boxes.cls.cpu().numpy().astype(int)
            xywhn = res.boxes.xywhn.cpu().numpy()
            for c, (cx, cy, w, h) in zip(cls, xywhn):
                cx, cy = min(max(cx, 0.0), 1.0), min(max(cy, 0.0), 1.0)
                w, h = min(max(w, 0.0), 1.0), min(max(h, 0.0), 1.0)
                lines.append(f"{c} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        lab.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return lines, lab

    n_det = n_empty = n_skip = 0
    for i, p in enumerate(imgs, 1):
        lab = out / (p.stem + ".txt")
        existed = lab.exists() and not args.overwrite
        lines, lab = make_lines(p)
        if existed:
            n_skip += 1
        elif lines:
            n_det += 1
        else:
            n_empty += 1
        print(f"[{i}/{len(imgs)}] {p.name}: {len(lines)} box(es) -> {lab}")

    # always ship a data.yaml with the labels (CVAT import requirement)
    write_yaml(out / "data.yaml", names)
    print(f"data.yaml written to {out / 'data.yaml'}")

    if args.cvat_dir:
        cdir = Path(args.cvat_dir)
        img_dir = cdir / "images" / "train"
        lab_dir = cdir / "labels" / "train"
        img_dir.mkdir(parents=True, exist_ok=True)
        lab_dir.mkdir(parents=True, exist_ok=True)
        list_lines = []
        for i, p in enumerate(imgs, 1):
            lines, lab = make_lines(p)
            shutil.copy2(p, img_dir / p.name)
            shutil.copy2(lab, lab_dir / lab.name)
            list_lines.append(f"images/train/{p.name}")
        (cdir / "train.txt").write_text("\n".join(list_lines) + "\n", encoding="utf-8")
        write_yaml(cdir / "data.yaml", names)
        print(f"CVAT dataset assembled in {cdir}: {len(imgs)} images, {len(imgs)} labels, data.yaml, train.txt")
        print("  -> zip this dir and upload into CVAT as 'Ultralytics YOLO'")

    print(f"done: {n_det} images with detections, {n_empty} empty (no detection), {n_skip} skipped (label exists)")


if __name__ == "__main__":
    main()