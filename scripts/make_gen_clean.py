r"""Audit generated-image provenance and build the leak-free pool (2026-09-18).

Finding this script exists for: the "generated" images are NOT text-to-image
outputs. Every PNG carries a ComfyUI workflow in its 'prompt' chunk showing
Qwen-Image-Edit edits of the 93 real inspection photos
(LoadImage -> TextEncodeQwenImageEditPlus -> KSampler). Any generated sample
whose SOURCE photo belongs to the held-out test set leaks test content into
training and must never enter a training pool.

This script:
  1. reads every generated PNG's metadata and records its edit source(s)
     -> D:\gas_cylinders\gen_sources.json
  2. COPIES the leak-free subset (source(s) do NOT intersect v2 test33) to
     D:\gas_cylinders\gen_clean\ (images/ labels/ manifest.json)
  The originals in Placement_Issues\ and Placement_Issues_2\ are never
  modified or deleted.

Re-run whenever new generated batches arrive, before building any split.
"""
import json
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image

GEN_DIRS = {
    "b1": Path(r"D:\gas_cylinders\Placement_Issues"),
    "b2": Path(r"D:\gas_cylinders\Placement_Issues_2"),
}
REAL = Path(r"D:\gas_cylinders\real_photo\93_real_photos")
TEST33_TXT = REAL / "v2_split" / "test33.txt"
SOURCES_JSON = Path(r"D:\gas_cylinders\gen_sources.json")
CLEAN = Path(r"D:\gas_cylinders\gen_clean")


def load_list(p: Path):
    return [Path(x.strip()).stem for x in p.read_text(encoding="utf-8-sig").splitlines() if x.strip()]


def scan_sources() -> dict:
    recs = {}
    for batch, root in GEN_DIRS.items():
        for p in sorted((root / "images").glob("*.png")):
            try:
                info = json.loads(Image.open(p).info.get("prompt", "{}"))
            except Exception:
                info = {}
            srcs = [Path(n["inputs"]["image"]).stem for n in info.values()
                    if n.get("class_type") == "LoadImage" and n.get("inputs", {}).get("image")]
            recs[p.stem] = {"batch": batch, "sources": srcs}
    return recs


def main():
    if not TEST33_TXT.exists():
        raise SystemExit(f"missing {TEST33_TXT} - run make_split_real_v2.py first")
    test33 = set(load_list(TEST33_TXT))

    recs = scan_sources()
    n = len(recs)
    no_src = [k for k, v in recs.items() if not v["sources"]]
    kept = {k: v for k, v in recs.items() if not (set(v["sources"]) & test33)}
    dropped = {k: v for k, v in recs.items() if set(v["sources"]) & test33}
    src_counter = Counter(s for v in recs.values() for s in v["sources"])

    print(f"generated images        : {n}")
    print(f"  without edit source   : {len(no_src)} (kept)")
    print(f"  source in test33      : {len(dropped)} ({len(dropped)/n:.0%})  -> excluded from training")
    print(f"  leak-free pool        : {len(kept)}  (b1 {sum(1 for v in kept.values() if v['batch']=='b1')} / "
          f"b2 {sum(1 for v in kept.values() if v['batch']=='b2')})")
    print(f"  distinct sources used : {len(src_counter)} (of 93 real photos)")

    SOURCES_JSON.write_text(json.dumps({"records": recs, "source_counter": dict(src_counter)},
                                       ensure_ascii=False, indent=1), encoding="utf-8")

    (CLEAN / "images").mkdir(parents=True, exist_ok=True)
    (CLEAN / "labels").mkdir(parents=True, exist_ok=True)
    copied = 0
    for stem, rec in sorted(kept.items()):
        root = GEN_DIRS[rec["batch"]]
        for sub, ext in (("images", ".png"), ("labels", ".txt")):
            dst = CLEAN / sub / (stem + ext)
            if not dst.exists():
                shutil.copy2(root / sub / (stem + ext), dst)
                copied += 1
    (CLEAN / "manifest.json").write_text(json.dumps({
        "built": "2026-09-18",
        "rule": "kept = generated images whose edit source(s) do NOT intersect v2 test33; "
                "originals untouched in the two batch folders",
        "test33": sorted(test33),
        "counts": {"kept": len(kept), "dropped": len(dropped),
                   "kept_b1": sum(1 for v in kept.values() if v["batch"] == "b1"),
                   "kept_b2": sum(1 for v in kept.values() if v["batch"] == "b2")},
        "kept": {k: {"batch": v["batch"], "sources": v["sources"]} for k, v in sorted(kept.items())},
        "dropped": {k: {"batch": v["batch"], "sources": v["sources"]} for k, v in sorted(dropped.items())},
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nwrote {SOURCES_JSON}")
    print(f"clean pool -> {CLEAN} (images {len(list((CLEAN/'images').glob('*.png')))}, "
          f"labels {len(list((CLEAN/'labels').glob('*.txt')))}, copied {copied} files this run)")


if __name__ == "__main__":
    main()
