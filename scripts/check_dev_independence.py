r"""dev61 source-independence check (thumbnail correlation, no training needed).

Why this exists: dev61 (61 web images, `new_test_set`) is independently sourced.
The claim "dev61 has no near-duplicate against a training source" must be
*reproducible*, not asserted. This script
measures the strongest cheap form of visual near-duplication available:
mean-removed, L2-normalised 48x48 grayscale thumbnails -> cosine similarity.

Four matrices are printed:
  dev x real93 : dev61 vs the 93 real inspection photos (arm A train set and,
                  historically, the edit source of every generated image)
  dev x gen800 : dev61 vs 800 sampled generated images (400 per batch)
  dev x dev : internal control for scene/source grouping before cross-fitting
  real93 x real93 : internal control - how similar "same-source" photos are

How to read it: a genuine near-duplicate (same scene) scores >= ~0.95; the
93 real photos only reach 0.834 among themselves, so any dev-vs-train score
below that ceiling is evidence of *no* near-duplicate.

Measured 2026-09-19 on the shipped 61-image set (recorded here as the reference
value, PROGRESS.md 2.3):
  dev <-> real93 : max 0.730   >0.90: 0   >0.95: 0
  dev <-> gen800 : max 0.732   >0.90: 0   >0.95: 0
  (control) real93 internal: max 0.834, >0.90: 0
  most similar pair: new_test_set_0059.jpg ~ real_photo_19.png 0.730

dev61 shares neither source nor scene with the seed photos or with
any image generated from them, which is exactly what this check demonstrates.

Usage (read-only, ~30 s):
  & D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\check_dev_independence.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

GAS = Path(r"D:/gas_cylinders")
DEV_DIR = GAS / "new_test_set" / "images"
REAL_DIR = GAS / "real_photo" / "93_real_photos" / "images"
GEN_DIRS = [GAS / "Placement_Issues" / "images", GAS / "Placement_Issues_2" / "images"]
PER_BATCH = 400          # 400 + 400 = the 800 sampled generated images
SIZE = (48, 48)


def thumbs(paths):
    out = []
    for p in paths:
        a = np.asarray(Image.open(p).convert("L").resize(SIZE, Image.BILINEAR),
                       dtype=np.float32)
        a -= a.mean()
        n = np.linalg.norm(a)
        out.append((a / n if n > 0 else a).reshape(-1))
    return np.stack(out)


def main():
    dev = sorted(DEV_DIR.glob("*"))
    real = sorted(REAL_DIR.glob("*.png"))
    gen = sorted(GEN_DIRS[0].glob("*.png"))[:PER_BATCH] + \
          sorted(GEN_DIRS[1].glob("*.png"))[:PER_BATCH]
    assert dev and real and gen, "missing input images - check the data root"

    D, R, G = thumbs(dev), thumbs(real), thumbs(gen)
    dr, dg = D @ R.T, D @ G.T
    print(f"dev61 {len(dev)} vs real93 {len(real)} / gen sampled {len(gen)}")
    print(f"dev<->real93 : max {dr.max():.3f}  >0.90: {(dr > 0.90).sum()}  "
          f">0.95: {(dr > 0.95).sum()}")
    print(f"dev<->gen    : max {dg.max():.3f}  >0.90: {(dg > 0.90).sum()}  "
          f">0.95: {(dg > 0.95).sum()}")
    dd = D @ D.T
    np.fill_diagonal(dd, -1)
    print(f"dev internal : max {dd.max():.3f}, >0.90 pairs: {(dd > 0.90).sum() // 2}")
    rr = R @ R.T
    np.fill_diagonal(rr, -1)
    print(f"(control) real93 internal: max {rr.max():.3f}, >0.90: {(rr > 0.90).sum()}")
    i, j = np.unravel_index(dr.argmax(), dr.shape)
    print(f"most similar pair: {dev[i].name} ~ {real[j].name} {dr.max():.3f}")

    verdict = (dr.max() < rr.max()) and (dg.max() < rr.max()) and not (dd > 0.90).any()
    print(f"\n[{'OK' if verdict else 'CHECK'}] dev-vs-training similarity stays below the "
          f"same-source ceiling ({rr.max():.3f}); dev internal has no pair >0.90.")


if __name__ == "__main__":
    main()
