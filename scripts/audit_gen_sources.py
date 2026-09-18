r"""Generated-image provenance audit (v3, 2026-09-19).

Every generated image is a Qwen-Image-Edit edit of a real photo; the ComfyUI
workflow in each PNG's 'prompt' chunk names the source photo(s). The v3 red
line is: **no training/validation pool may contain an image derived from a
test image**. This script checks that automatically and is meant to be run
after every new generated batch, before any split is built.

Outputs:
  D:\gas_cylinders\gen_sources.json   per-image sources + aggregates + verdict

Exit: prints a clear OK/VIOLATION verdict against the v3 test set.
"""
import json
from collections import Counter
from pathlib import Path

from PIL import Image

GEN_DIRS = {
    "b1": Path(r"D:\gas_cylinders\Placement_Issues"),
    "b2": Path(r"D:\gas_cylinders\Placement_Issues_2"),
}
TEST_TXT = Path(r"D:\gas_cylinders\v3\test61.txt")     # v3 test (must never be an edit source)
OUT = Path(r"D:\gas_cylinders\gen_sources.json")


def main():
    test_stems = {Path(l.strip()).stem for l in TEST_TXT.read_text(encoding="utf-8-sig").splitlines() if l.strip()}
    print(f"v3 test images: {len(test_stems)} (from {TEST_TXT})")

    recs = {}
    for batch, root in GEN_DIRS.items():
        imgs = sorted((root / "images").glob("*.png"))
        for p in imgs:
            try:
                info = json.loads(Image.open(p).info.get("prompt", "{}"))
            except Exception as e:
                recs[p.stem] = {"batch": batch, "sources": [], "meta_error": str(e)[:120]}
                continue
            srcs = [Path(n["inputs"]["image"]).stem for n in info.values()
                    if n.get("class_type") == "LoadImage" and n.get("inputs", {}).get("image")]
            recs[p.stem] = {"batch": batch, "sources": srcs}
        print(f"  {batch}: {len(imgs)} images scanned under {root.name}")

    n = len(recs)
    src_counter = Counter(s for v in recs.values() for s in v["sources"])
    with_test = {k: v for k, v in recs.items() if set(v["sources"]) & test_stems}
    no_src = [k for k, v in recs.items() if not v["sources"]]

    print(f"\ntotal generated: {n} | distinct sources: {len(src_counter)} | no source: {len(no_src)}")
    print("edits per source: min %d / median %d / max %d" % (
        min(src_counter.values()), sorted(src_counter.values())[len(src_counter) // 2], max(src_counter.values())))

    if with_test:
        print(f"\n[VIOLATION] {len(with_test)} generated images derive from a v3 test image:")
        for k in sorted(with_test)[:20]:
            print(f"   {k}  <- {with_test[k]['sources']}")
        print("   -> exclude them from every training/validation pool before building splits.")
    else:
        print("\n[OK] no generated image derives from a v3 test image - "
              "all generated data is safe to train on.")

    OUT.write_text(json.dumps({
        "date": "2026-09-19", "test_set": str(TEST_TXT),
        "verdict": "violation" if with_test else "ok",
        "counts": {"total": n, "no_source": len(no_src), "derived_from_test": len(with_test)},
        "source_counter": dict(src_counter),
        "records": recs,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
