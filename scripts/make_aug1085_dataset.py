r"""B arm dataset: classical offline augmentation of 93 real photos -> 1085 images.

Purpose (L1 main experiment): the B arm answers "why not just use free classical
augmentation instead of state-editing synthesis". It must therefore start from the
SAME seed material as the other arms (real93) and reach the same total size as the
C arm (1085 generated images), differing only in HOW the data was expanded.

Recipe:
  - geometric: horizontal flip, rotation +-10 deg, scale 0.8..1.2, translate +-10%
  - photometric: HSV jitter (hue +-0.015, sat 0.7..1.3, val 0.7..1.3), matching the
    ranges ultralytics uses online
  - NO vertical flip (construction sites have a gravity direction)
  - boxes are carried through every geometric transform, clipped to the image and
    dropped when they degenerate (<2 px or <0.001 normalized area)
  - deterministic: seed 42, so the dataset can be rebuilt byte-for-byte

Counts (93 seed photos -> exactly 1085 = the C arm's size):
  every one of the 93 seed photos yields 12 augmented variants: 93 * 12 = 1116
  then 31 of those 1116 are dropped at random (seed 42) -> 1085
  (the originals are NOT added separately: every image in the pool is an augmented
  variant, so the pool is uniform and the trim is a plain random sample)

No boxed/empty split: one image may hold BOTH compliant and violating cylinders (a
mixed sample), and the annotation unit is the box - so classifying whole images and
augmenting the two classes differently would be meaningless. All 93 seeds are treated
identically (12 variants each) and the surplus is trimmed at random. The script
verifies afterwards that every seed photo is still represented in the final 1085.

Output (D:\gas_cylinders\aug1085\):
  images\aug1085_XXXX.png    augmented images (all 1085 are augments of the seed set)
  labels\aug1085_XXXX.txt    YOLO labels, 1:1 with images
  train.txt                  absolute image paths for all 1085
  data_aug1085.yaml          ultralytics config: train=val=train.txt, test=v4 dev61

Run with the venv python; needs write access to D:\gas_cylinders (cross-drive).
"""
import random
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

SEED = 42
GAS = Path(r"D:/gas_cylinders")
SRC = GAS / "real_photo" / "93_real_photos"
SRC_IMAGES = SRC / "images"
SRC_LABELS = SRC / "labels"
OUT = GAS / "aug1085"
DEV_TXT = "D:/gas_cylinders/v4/dev61.txt"
TARGET = 1085

ROT_DEG = 10.0
SCALE_RANGE = (0.80, 1.20)
TRANS_FRAC = 0.10
HUE_JITTER = 0.015
SAT_RANGE = (0.70, 1.30)
VAL_RANGE = (0.70, 1.30)
MIN_BOX_PX = 2.0
MIN_BOX_AREA = 0.001


def read_label(p: Path):
    """YOLO rows -> list of [cls, cx, cy, w, h] (normalized)."""
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        t = line.split()
        if len(t) == 5:
            rows.append([int(t[0])] + [float(x) for x in t[1:]])
    return rows


def corners(cx, cy, w, h):
    return np.array([[cx - w / 2, cy - h / 2], [cx + w / 2, cy - h / 2],
                     [cx + w / 2, cy + h / 2], [cx - w / 2, cy + h / 2]], dtype=np.float64)


def transform_points(pts, M):
    ones = np.ones((len(pts), 1))
    hom = np.hstack([pts, ones]) @ M.T
    return hom[:, :2]


def hsv_jitter(img: np.ndarray, rng: random.Random) -> np.ndarray:
    hsv = np.asarray(Image.fromarray(img).convert("HSV"), dtype=np.float32) / 255.0
    hsv[..., 0] = (hsv[..., 0] + rng.uniform(-HUE_JITTER, HUE_JITTER)) % 1.0
    hsv[..., 1] = np.clip(hsv[..., 1] * rng.uniform(*SAT_RANGE), 0, 1)
    hsv[..., 2] = np.clip(hsv[..., 2] * rng.uniform(*VAL_RANGE), 0, 1)
    back = Image.fromarray((hsv * 255).astype(np.uint8), mode="HSV").convert("RGB")
    return np.asarray(back)


def augment(img: Image.Image, rows, rng: random.Random):
    W, H = img.size
    arr = np.asarray(img.convert("RGB"))
    # affine in normalized coords: (x_norm, y_norm) -> shifted/scaled/rotated/flipped
    s = rng.uniform(*SCALE_RANGE)
    angle = np.deg2rad(rng.uniform(-ROT_DEG, ROT_DEG))
    ca, sa = np.cos(angle), np.sin(angle)
    tx, ty = rng.uniform(-TRANS_FRAC, TRANS_FRAC), rng.uniform(-TRANS_FRAC, TRANS_FRAC)
    flip = rng.random() < 0.5

    def apply(pts):
        p = pts - 0.5                      # centre
        p = p * np.array([1.0 if not flip else -1.0, 1.0])   # hflip
        p = p * s                          # scale
        p = p @ np.array([[ca, -sa], [sa, ca]])              # rotate
        return p + 0.5 + np.array([tx, ty])                  # translate

    # Labels use the forward transform above. Pillow samples output pixels from input,
    # so it needs the inverse transform expressed in pixel coordinates.
    basis = apply(np.array([[0, 0], [1, 0], [0, 1]], dtype=np.float64))
    norm_forward = np.array([
        [basis[1, 0] - basis[0, 0], basis[2, 0] - basis[0, 0], basis[0, 0]],
        [basis[1, 1] - basis[0, 1], basis[2, 1] - basis[0, 1], basis[0, 1]],
        [0.0, 0.0, 1.0],
    ])
    to_pixels = np.diag([W, H, 1.0])
    to_normalized = np.diag([1.0 / W, 1.0 / H, 1.0])
    pixel_inverse = np.linalg.inv(to_pixels @ norm_forward @ to_normalized)
    out = Image.fromarray(arr).transform(
        (W, H), Image.AFFINE, tuple(pixel_inverse[:2].ravel()),
        resample=Image.BILINEAR, fillcolor=(114, 114, 114))
    out = Image.fromarray(hsv_jitter(np.asarray(out), rng))

    new_rows = []
    for cls, cx, cy, w, h in rows:
        c = apply(corners(cx, cy, w, h))
        x1, y1 = c.min(axis=0)
        x2, y2 = c.max(axis=0)
        x1, y1, x2, y2 = max(0.0, x1), max(0.0, y1), min(1.0, x2), min(1.0, y2)
        nw, nh = (x2 - x1) * W, (y2 - y1) * H
        if nw < MIN_BOX_PX or nh < MIN_BOX_PX or (x2 - x1) * (y2 - y1) < MIN_BOX_AREA:
            continue
        new_rows.append([cls, (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1])
    return out, new_rows


def main():
    rng = random.Random(SEED)
    originals = sorted(SRC_IMAGES.glob("*.png"))
    assert len(originals) == 93, f"expected 93 real photos, got {len(originals)}"

    for sub in ("images", "labels"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
        for old in (OUT / sub).glob("*"):
            old.unlink()

    # Select omitted pool positions first, then stream kept images to disk. This keeps
    # memory bounded to one source image and one augmented image at a time.
    total_before = 93 * 12
    drop_idx = set(random.Random(SEED).sample(range(total_before), total_before - TARGET))
    dropped_boxes = 0
    kept_count = 0
    pool_index = 0
    per_source = Counter()
    for p in originals:
        rows = read_label(SRC_LABELS / f"{p.stem}.txt")
        with Image.open(p) as base:
            for _ in range(12):
                img, new_rows = augment(base, rows, rng)
                dropped_boxes += max(0, len(rows) - len(new_rows))
                if pool_index not in drop_idx:
                    name = f"aug1085_{kept_count:04d}"
                    img.save(OUT / "images" / f"{name}.png")
                    (OUT / "labels" / f"{name}.txt").write_text(
                        "".join(f"{int(c)} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n"
                                for c, x, y, w, h in new_rows),
                        encoding="utf-8")
                    kept_count += 1
                    per_source[p.stem] += 1
                pool_index += 1

    assert pool_index == total_before == 1116, f"unexpected pre-trim count {pool_index}"
    assert kept_count == TARGET, f"expected {TARGET} after trim, got {kept_count}"

    print(f"generated {total_before} (93 x 12 augmented variants), "
          f"trimmed {total_before - TARGET} at random -> {kept_count} (target {TARGET})")
    print(f"boxes dropped by clipping: {dropped_boxes}")

    # every source photo must still be represented after the trim
    missing = [p.stem for p in originals if p.stem not in per_source]
    print(f"sources represented: {len(per_source)}/93  min per source: "
          f"{min(per_source.values())}  max: {max(per_source.values())}")
    assert not missing, f"sources lost in the trim: {missing[:5]}"

    imgs = sorted((OUT / "images").glob("*.png"))
    lines = [str(p).replace("\\", "/") for p in imgs]
    (OUT / "train.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "data_aug1085.yaml").write_text(
        "names:\n  0: Placement Issues\npath: D:/gas_cylinders/aug1085\n"
        "train: train.txt\nval: train.txt\n"
        f"test: {DEV_TXT}\n", encoding="utf-8")

    n_empty = sum(1 for p in imgs if not (OUT / "labels" / f"{p.stem}.txt").read_text(
        encoding="utf-8").strip())
    print(f"final: {len(imgs)} images  ({len(imgs) - n_empty} with boxes, {n_empty} empty)")
    print(f"wrote {OUT}/train.txt and data_aug1085.yaml")


if __name__ == "__main__":
    main()
