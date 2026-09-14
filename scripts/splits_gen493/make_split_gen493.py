r"""gen493 split: the 493 reviewed generated images -> stratified train/val
(80/20, seed=42), test = all 93 real photos (never used in training).

2026-09-14: the user's review deleted 7 unusable images from the original
500-image batch (4 positives with 10 boxes + 3 negatives) -> 493 images.

Positives = non-empty label file, negatives = empty (stratified so val keeps
the pos/neg ratio). ABSOLUTE paths in manifests (COMMANDS.md pitfall), one
data.yaml covering train/val/test.

Outputs:
  D:/gas_cylinders/Placement_Issues/gen493_split/train.txt
  D:/gas_cylinders/Placement_Issues/gen493_split/val.txt
  D:/gas_cylinders/Placement_Issues/gen493_split/split_info.json
  D:/gas_cylinders/Placement_Issues/gen493_split/data.yaml   (train+val+test)

Does NOT touch the annotator workspace data.yaml at Placement_Issues root.
"""
import json
import os
import random
from pathlib import Path

ROOT = Path(r"D:/gas_cylinders/Placement_Issues")
OUT = ROOT / "gen493_split"
TEST_TXT = r"D:/gas_cylinders/real_photo/93_real_photos/v1_split/all.txt"
SEED = 42
VAL_RATIO = 0.2
EXPECTED = 493

rng = random.Random(SEED)

imgs = sorted((ROOT / "images").glob("*.png")) + sorted((ROOT / "images").glob("*.jpg"))
assert len(imgs) == EXPECTED, f"expected {EXPECTED} images, got {len(imgs)}"

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
assert len(train) + len(val) == EXPECTED

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
    "revision": "2026-09-14 review deleted 7 images (4 pos/10 boxes + 3 neg) from the 500 batch",
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
    "train: gen493_split/train.txt\n"
    "val: gen493_split/val.txt\n"
    f"test: {TEST_TXT.replace(os.sep, '/')}\n"
)
(OUT / "data.yaml").write_text(yaml_text, encoding="utf-8")

print(f"train={len(train)} (pos {len(pos_tr)} / neg {len(neg_tr)}), boxes={info['train']['boxes']}")
print(f"val={len(val)} (pos {len(pos_va)} / neg {len(neg_va)}), boxes={info['val']['boxes']}")
print(f"test=93 real photos (all.txt), data.yaml written to {OUT / 'data.yaml'}")
