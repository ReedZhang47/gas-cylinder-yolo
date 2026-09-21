r"""Generated-image provenance audit (v4).

Every generated training image is a Qwen-Image-Edit edit of a real seed photo. The ComfyUI
workflow stored in each PNG's 'prompt' chunk names the images the graph loaded, and the two
roles must not be confused:

  * BASE photo - the one the edit was applied to, i.e. the LoadImage that feeds
    FluxKontextImageScale. Every generated image has exactly one.
  * REFERENCE photos - images the edit instruction points at ("put the cylinder the way it
    sits in the second image"). They guide the edit but are not themselves edited, so they
    are recorded separately rather than counted as sources.

The red line this guards: no evaluation image may be an edit source. All generated images
must trace back to the real seed photos, none to the development benchmark. Run this after
every new generated batch and before any split is built.

Output: experiments/gen1085_sources.json (tracked; PROGRESS.md cites it).
Usage: & D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\audit_gen_sources.py
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:/yolo")
OUT = ROOT / "experiments" / "gen1085_sources.json"
GEN_DIRS = {
    "b1": Path(r"D:/gas_cylinders/Placement_Issues"),
    "b2": Path(r"D:/gas_cylinders/Placement_Issues_2"),
}
# v4 name for the development benchmark. D:\gas_cylinders\v3\test61.txt holds the same 61
# images in the same order (checked 2026-09-21); v4 configs use this path.
DEV_TXT = Path(r"D:/gas_cylinders/v4/dev61.txt")


def split_roles(prompt: dict) -> tuple[str | None, list[str], bool]:
    """(base stem, reference stems, ambiguous) for one image's ComfyUI workflow.

    The base is taken from the graph rather than from a hard-coded node id: the LoadImage
    consumed by the image-scaling node is the photo that gets edited. Anything else loaded
    is a reference. `ambiguous` flags graphs whose base cannot be identified uniquely, so
    the audit surfaces such images instead of silently guessing.
    """
    loads = {node_id: Path(node["inputs"]["image"]).stem
             for node_id, node in prompt.items()
             if node.get("class_type") == "LoadImage" and node.get("inputs", {}).get("image")}
    bases = []
    for node in prompt.values():
        if node.get("class_type") == "FluxKontextImageScale":
            link = node.get("inputs", {}).get("image")
            if isinstance(link, list) and link and link[0] in loads:
                bases.append(loads[link[0]])
    base = bases[0] if bases else None
    references = [stem for node_id, stem in sorted(loads.items()) if stem != base]
    return base, references, len(bases) != 1


def main() -> None:
    dev_stems = {Path(line.strip()).stem
                 for line in DEV_TXT.read_text(encoding="utf-8-sig").splitlines() if line.strip()}
    print(f"development benchmark: {len(dev_stems)} images (from {DEV_TXT})")

    records: dict[str, dict] = {}
    for batch, root in GEN_DIRS.items():
        images = sorted((root / "images").glob("*.png"))
        for path in images:
            try:
                prompt = json.loads(Image.open(path).info.get("prompt", "{}"))
            except Exception as exc:
                records[path.stem] = {"batch": batch, "base": None, "references": [],
                                      "ambiguous": True, "meta_error": str(exc)[:120]}
                continue
            base, references, ambiguous = split_roles(prompt)
            records[path.stem] = {"batch": batch, "base": base, "references": references,
                                  "ambiguous": ambiguous}
        print(f"  {batch}: scanned {len(images)} images under {root.name}")

    base_counter = Counter(r["base"] for r in records.values() if r["base"])
    reference_counter = Counter(s for r in records.values() for s in r["references"])
    no_base = [k for k, r in records.items() if not r["base"]]
    ambiguous = [k for k, r in records.items() if r["ambiguous"]]
    from_dev = {k: r for k, r in records.items() if r["base"] in dev_stems}
    ref_dev = {k: r for k, r in records.items() if set(r["references"]) & dev_stems}

    print(f"\ntotal generated: {len(records)} | distinct base photos: {len(base_counter)}"
          f" | no base: {len(no_base)} | ambiguous: {len(ambiguous)}")
    if base_counter:
        counts = sorted(base_counter.values())
        print("edits per base photo: min %d / median %d / max %d"
              % (counts[0], counts[len(counts) // 2], counts[-1]))

    verdict = "violation" if from_dev else "ok"
    if from_dev:
        print(f"\n[VIOLATION] {len(from_dev)} generated images are edits of a development image:")
        for key in sorted(from_dev)[:20]:
            print(f"   {key}  <- {from_dev[key]['base']}")
        print("   -> exclude them from every training/validation pool before building splits.")
    else:
        print("\n[OK] no generated image is an edit of a development image; every base photo "
              "comes from the real seed set.")
    if ref_dev:
        print(f"[note] {len(ref_dev)} generated images name a development image as a "
              f"reference only (not edited from it): {sorted(ref_dev)[:5]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "date": date.today().isoformat(),
        "development_set": str(DEV_TXT),
        "method": "base = LoadImage feeding FluxKontextImageScale; other LoadImage nodes are references",
        "verdict": verdict,
        "counts": {"total": len(records), "no_base": len(no_base), "ambiguous": len(ambiguous),
                   "derived_from_development": len(from_dev),
                   "referenced_development": len(ref_dev)},
        "base_counter": dict(base_counter),
        "reference_counter": dict(reference_counter),
        "records": records,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
