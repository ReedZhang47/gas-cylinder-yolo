r"""gen500 split of the 500 generated placement-issue images -> stratified
train/val (80/20, seed=42).

Purpose: PLAN.md 2026-09-11 step 1-2. Positives = label file non-empty,
negatives = empty label file; stratified so val keeps the pos/neg ratio.
Test set by design = all 93 real photos (v1_split/all.txt), never trained on.

Outputs (does NOT touch the workspace's own data.yaml, which stays in
annotator format for the GUI):
  D:/gas_cylinders/Placement_Issues/gen500_split/train.txt   (abs paths)
  D:/gas_cylinders/Placement_Issues/gen500_split/val.txt     (abs paths)
  D:/gas_cylinders/Placement_Issues/gen500_split/split_info.json
  D:/gas_cylinders/Placement_Issues/gen500_split/data.yaml   (abs path key,
    train/val -> these txt manifests, test -> 93 real photos all.txt)
"""
import json
import os
import random
from pathlib import Path

ROOT = Path(r"D:/gas_cylinders/Placement_Issues")
OUT = ROOT / "gen500_split"
TEST_TXT = r"D:/gas_cylinders/real_photo/93_real_photos/v1_split/all.txt"
SEED = 42
VAL_RATIO = 0.2

rng = random.Random(SEED)

imgs = sorted((ROOT / "images").glob("*.png")) + sorted((ROOT / "images").glob("*.jpg"))
assert imgs, "no images found"
assert len(imgs) == 500, f"expected 500 images, got {len(imgs)}"

pos, neg = [], []
for p in imgs:
    lp = ROOT / "labels" / (p.stem + ".txt")
    assert lp.exists(), f"missing label for {p.name}"
    (neg if lp.stat().st_size == 0 else pos).append(p)
print(f"pos={len(pos)} neg={len(neg)} total={len(pos)+len(neg)}")


def take(lst):
    """Round-half-up share for val, at least 1 element when lst non-empty."""
    k = min(len(lst), int(len(lst) * VAL_RATIO + 0.5))
    rng.shuffle(lst)
    return sorted(lst[k:]), sorted(lst[:k])  # (train_part, val_part)


pos_tr, pos_va = take(pos)
neg_tr, neg_va = take(neg)
train = sorted(str(p).replace(os.sep, "/") for p in pos_tr + neg_tr)
val = sorted(str(p).replace(os.sep, "/") for p in pos_va + neg_va)
assert len(set(train) & set(val)) == 0
assert len(train) + len(val) == 500

test_lines = [l.strip().replace("\\", "/") for l in Path(TEST_TXT).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
assert len(test_lines) == 93, f"expected 93 test lines, got {len(test_lines)}"
assert not (set(test_lines) & set(train + val)), "test images leaked into train/val"

os.makedirs(OUT, exist_ok=True)
(OUT / "train.txt").write_text("\n".join(train) + "\n", encoding="utf-8")
(OUT / "val.txt").write_text("\n".join(val) + "\n", encoding="utf-8")


def n_boxes(paths):
    n = 0
    for p in paths:
        lp = ROOT / "labels" / (Path(p).stem + ".txt")
        n += sum(1 for line in lp.read_text(encoding="utf-8").splitlines() if line.strip())
    return n


info = {
    "seed": SEED,
    "val_ratio": VAL_RATIO,
    "train": {"total": len(train), "pos": len(pos_tr), "neg": len(neg_tr), "boxes": n_boxes(train)},
    "val": {"total": len(val), "pos": len(pos_va), "neg": len(neg_va), "boxes": n_boxes(val)},
    "test": {"total": len(test_lines), "source": TEST_TXT,
             "note": "93 real photos, all.txt, never trained on"},
    "val_images": val,
}
(OUT / "split_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

yaml_text = (
    "names:\n"
    "  0: Placement Issues\n"
    f"path: {str(ROOT).replace(os.sep, '/')}\n"
    "train: gen500_split/train.txt\n"
    "val: gen500_split/val.txt\n"
    f"test: {TEST_TXT.replace(os.sep, '/')}\n"
)
(OUT / "data.yaml").write_text(yaml_text, encoding="utf-8")

print(f"train={len(train)} (pos {len(pos_tr)} / neg {len(neg_tr)}), boxes={info['train']['boxes']}")
print(f"val={len(val)} (pos {len(pos_va)} / neg {len(neg_va)}), boxes={info['val']['boxes']}")
print(f"test=93 real photos (all.txt), data.yaml written to {OUT / 'data.yaml'}")
