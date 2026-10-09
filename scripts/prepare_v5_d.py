"""Read-only data audit and frozen inputs for D; never trains or runs inference."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
import sys

import numpy as np
from PIL import Image
import torch
import ultralytics
import yaml

import eval_v4_protocol as ev

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/v5_d"
DATA = Path("D:/gas_cylinders/D1085")
ARM = "D1085v5"
V4 = ROOT / "experiments/v4_protocol"
WEIGHTS = ev.WEIGHTS


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def label_count(path):
    require(path.is_file(), f"Missing label: {path}")
    seen = set()
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split()
        require(len(fields) == 5, f"Not a detection label: {path}:{number}")
        c, x, y, w, h = map(float, fields)
        require(all(math.isfinite(v) for v in (c, x, y, w, h)), f"Nonfinite: {path}:{number}")
        require(c == 0 and 0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1,
                f"Invalid class/xywh: {path}:{number}")
        require(min(x-w/2, y-h/2) >= -1e-5 and max(x+w/2, y+h/2) <= 1.00001,
                f"Box outside image: {path}:{number}")
        row = (c, x, y, w, h)
        require(row not in seen, f"Duplicate annotation: {path}:{number}")
        seen.add(row)
    return len(seen)


def image_record(image):
    label = ev.label_path(image)
    with Image.open(image) as im:
        im.load()  # decode pixels: detect truncated/corrupt images
        size = list(im.size)
        require(min(size) > 0, f"Invalid dimensions: {image}")
        thumb = np.asarray(im.convert("L").resize((48, 48), Image.Resampling.BILINEAR), dtype=np.float32)
    thumb -= thumb.mean()
    norm = np.linalg.norm(thumb)
    record = {"image": image.as_posix(), "image_sha256": sha(image), "size": size,
              "label": label.as_posix(), "label_sha256": sha(label), "boxes": label_count(label)}
    return record, (thumb / norm if norm else thumb).reshape(-1)


def source_files():
    return [ROOT / "scripts" / name for name in (
        "prepare_v5_d.py", "run_v5_d.py", "eval_v5_d.py", "eval_v4_protocol.py", "bootstrap_paired.py")]


def environment():
    return {"python": platform.python_version(), "executable": sys.executable,
            "torch": torch.__version__, "ultralytics": ultralytics.__version__,
            "numpy": np.__version__, "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}


def config_text():
    return ("# Frozen D training input; val=train is diagnostic only.\n"
            f"path: {DATA.as_posix()}\ntrain: {(OUT/'D1085_train.txt').as_posix()}\n"
            f"val: {(OUT/'D1085_train.txt').as_posix()}\n"
            "nc: 1\nnames:\n  0: Placement Issues\n")


def freeze():
    require(not (OUT / "input_manifest.json").exists(), "Inputs already frozen; use --check (do not silently refreeze).")
    require(not (ROOT / "runs/detect" / ARM).exists(), "D run already exists; cannot create a new input freeze.")
    require(ultralytics.__version__ == "8.4.135", "Ultralytics differs from v4 checkpoint version 8.4.135")
    images = sorted((DATA / "images").glob("*.png"))
    require([p.name for p in images] == [f"D_{i:04d}.png" for i in range(1, 1086)], "D image names/count differ")
    require({p.stem for p in (DATA / "labels").glob("*.txt")} == {p.stem for p in images}, "Orphan/missing labels")
    source_path = ROOT / "docs/v5_prompts/d1085_source_mapping.json"
    sources = {row["image_name"]: row for row in json.loads(source_path.read_text(encoding="utf-8"))}
    records, thumbs = [], []
    for image in images:
        record, thumb = image_record(image)
        require(record["image_sha256"] == sources[image.name]["sha256"], f"Reviewed image changed: {image}")
        record["source_set"] = sources[image.name]["source_set"]
        records.append(record)
        thumbs.append(thumb)
    require(len({r["image_sha256"] for r in records}) == 1085, "Duplicate D image hashes")
    dev = [Path(x) for x in ev.DEV_LIST.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    require(len(dev) == 61 and len({p.name for p in dev}) == 61, "Invalid dev61 list")
    dev_records, dev_thumbs = zip(*(image_record(p) for p in dev))
    require(sum(r["boxes"] for r in dev_records) == 72, "dev61 box count changed")
    folds = ev.build_folds(dev)
    protocol = json.loads((V4 / "protocol.json").read_text(encoding="utf-8"))
    require(folds == protocol["folds"], "dev61 folds differ from frozen v4 protocol")
    require(not ({r["image_sha256"] for r in records} & {r["image_sha256"] for r in dev_records}), "D/dev exact overlap")
    d = np.stack(thumbs)
    v = np.stack(dev_thumbs)
    cross, internal = v @ d.T, d @ d.T
    np.fill_diagonal(internal, -1)
    di, dj = np.unravel_index(cross.argmax(), cross.shape)
    pairs = [[images[i].name, images[j].name, round(float(internal[i, j]), 6)]
             for i, j in zip(*np.where(np.triu(internal > .90, k=1)))]
    audit = {"images": len(records), "labels": len(records), "boxes": sum(r["boxes"] for r in records),
             "positive": sum(r["boxes"] > 0 for r in records), "empty": sum(r["boxes"] == 0 for r in records),
             "sources": dict(Counter(r["source_set"] for r in records)),
             "dev61_max_thumbnail_similarity": round(float(cross.max()), 6),
             "most_similar_dev_D_pair": [dev[di].name, images[dj].name],
             "dev61_D_pairs_above_0.90": int((cross > .90).sum()),
             "D_internal_pairs_above_0.90": pairs,
             "method": "48x48 mean-centered grayscale cosine; screening only, not proof of source independence",
             "manual_labels": "Author reports annotations ready; automatic checks verify structure, not semantics."}
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "data_audit.json", audit)
    require(not pairs and not (cross > .90).any(), "Near-duplicate screening flagged pairs; inspect data_audit.json before freezing")
    (OUT / "D1085_train.txt").write_text("\n".join(p.as_posix() for p in images) + "\n", encoding="utf-8")
    (OUT / "data_D1085.yaml").write_text(config_text(), encoding="utf-8")
    config = yaml.safe_load((OUT / "data_D1085.yaml").read_text(encoding="utf-8"))
    require(config["train"] == config["val"] and "test" not in config, "Training must not read dev61")
    controls = [source_path, ev.DEV_LIST, Path(ev.DEV_YAML), V4 / "protocol.json", OUT / "D1085_train.txt", OUT / "data_D1085.yaml"]
    for arm in ev.MAIN_ARMS:
        controls.extend([V4 / f"v4_protocol_{arm}.json", V4 / "per_image" / f"per_image_{arm}.json"])
        cache = json.loads(controls[-1].read_text(encoding="utf-8"))
        require(cache["folds"] == folds and cache["image_names"] == sorted(p.name for p in dev), f"Invalid {arm} cache folds")
        require(set(cache["detectors"]) == set(WEIGHTS) and cache["joint"] is not None, f"Incomplete {arm} cache")
    controls += [ROOT / "weights" / f"{w}.pt" for w in WEIGHTS]
    controls += [ROOT / "runs/detect/gen1085v4" / w / "args.yaml" for w in WEIGHTS]
    manifest = {"created_at": datetime.now().astimezone().isoformat(), "arm": ARM,
                "status": "prepared; training and inference not started", "environment": environment(),
                "images": records, "dev61": list(dev_records), "folds": folds,
                "files": {p.as_posix(): sha(p) for p in controls},
                "scripts": {p.as_posix(): sha(p) for p in source_files()}, "audit": audit}
    write_json(OUT / "input_manifest.json", manifest)
    print(json.dumps(audit, ensure_ascii=False, indent=2))


def check():
    manifest_path = OUT / "input_manifest.json"
    require(manifest_path.exists(), "Missing frozen inputs; run prepare_v5_d.py --freeze first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require({p.name for p in (DATA / "images").glob("*.png")} == {Path(r["image"]).name for r in manifest["images"]}, "D image set changed")
    require({p.name for p in (DATA / "labels").glob("*.txt")} == {Path(r["label"]).name for r in manifest["images"]}, "D label set changed")
    for row in manifest["images"] + manifest["dev61"]:
        for key in ("image", "label"):
            require(sha(row[key]) == row[key + "_sha256"], f"Frozen {key} changed: {row[key]}")
    for path, digest in {**manifest["files"], **manifest["scripts"]}.items():
        require(sha(path) == digest, f"Frozen input/code changed: {path}")
    require(environment() == manifest["environment"], "Python/torch/Ultralytics/GPU environment changed")
    require(torch.cuda.is_available(), "CUDA is unavailable")
    print(f"Frozen inputs OK: 1085 D images + labels, 61 dev images + labels; free disk {shutil.disk_usage(ROOT).free / 2**30:.1f} GiB")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    freeze() if args.freeze else check()


if __name__ == "__main__":
    main()
