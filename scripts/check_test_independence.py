r"""v3 test-set independence check (thumbnail correlation, no training needed).

Why this exists: the v3 test set (61 web images, `new_test_set`) is the single
evaluation protocol of the paper. The claim "the test set is independent of
every training source" must be *reproducible*, not asserted. This script
measures the strongest cheap form of visual near-duplication available:
mean-removed, L2-normalised 48x48 grayscale thumbnails -> cosine similarity.

Three matrices are printed:
  test x real93 : test vs the 93 real inspection photos (arm A train set and,
                  historically, the edit source of every generated image)
  test x gen800 : test vs 800 sampled generated images (400 per batch)
  real93 x real93 : internal control - how similar "same-source" photos are

How to read it: a genuine near-duplicate (same scene) scores >= ~0.95; the
93 real photos only reach 0.834 among themselves, so any test-vs-train score
below that ceiling is evidence of *no* near-duplicate.

Measured 2026-09-19 on the shipped v3 test set (recorded here as the reference
value, PROGRESS.md 2.3):
  test <-> real93 : max 0.730   >0.90: 0   >0.95: 0
  test <-> gen800 : max 0.732   >0.90: 0   >0.95: 0
  (control) real93 internal: max 0.834, >0.90: 0
  most similar pair: new_test_set_0059.jpg ~ real_photo_19.png 0.730

Depth-2 provenance note: the superseded v2-era scheme audited ComfyUI metadata
to find generated images derived from a held-out test photo (611/1085). That
scheme was abandoned together with the v2 test set; the v3 web test set shares
neither source nor scene with the training data, so only the check below is
used as evidence. Do not resurrect the audit framing as a contribution.

Usage (read-only, ~30 s):
  & D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\check_test_independence.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

GAS = Path(r"D:/gas_cylinders")
TEST_DIR = GAS / "new_test_set" / "images"
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
    test = sorted(TEST_DIR.glob("*"))
    real = sorted(REAL_DIR.glob("*.png"))
    gen = sorted(GEN_DIRS[0].glob("*.png"))[:PER_BATCH] + \
          sorted(GEN_DIRS[1].glob("*.png"))[:PER_BATCH]
    assert test and real and gen, "missing input images - check the data root"

    T, R, G = thumbs(test), thumbs(real), thumbs(gen)
    tr, tg = T @ R.T, T @ G.T
    print(f"test {len(test)} vs real93 {len(real)} / gen sampled {len(gen)}")
    print(f"test<->real93 : max {tr.max():.3f}  >0.90: {(tr > 0.90).sum()}  "
          f">0.95: {(tr > 0.95).sum()}")
    print(f"test<->gen    : max {tg.max():.3f}  >0.90: {(tg > 0.90).sum()}  "
          f">0.95: {(tg > 0.95).sum()}")
    rr = R @ R.T
    np.fill_diagonal(rr, -1)
    print(f"(control) real93 internal: max {rr.max():.3f}, >0.90: {(rr > 0.90).sum()}")
    i, j = np.unravel_index(tr.argmax(), tr.shape)
    print(f"most similar pair: {test[i].name} ~ {real[j].name} {tr.max():.3f}")

    verdict = (tr.max() < rr.max()) and (tg.max() < rr.max())
    print(f"\n[{'OK' if verdict else 'CHECK'}] test-vs-training similarity stays below the "
          f"same-source ceiling ({rr.max():.3f}) -> no near-duplicate in the test set.")


if __name__ == "__main__":
    main()
