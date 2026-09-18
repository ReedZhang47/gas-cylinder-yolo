r"""gen_clean split (2026-09-18): stratified train/val from the leak-free
generated pool (D:/gas_cylinders/gen_clean, 474 images = batch-1 143 +
batch-2 331; every source photo is outside v2 test33).

test key = v2 test33 (the 33 held-out real photos) so one yaml serves both
training and the clean evaluation.

Outputs (D:/gas_cylinders/gen_clean/split/):
  train.txt / val.txt / split_info.json / data.yaml
"""
import json
import os
import random
from pathlib import Path

POOL = Path(r"D:/gas_cylinders/gen_clean")
OUT = POOL / "split"
TEST33_TXT = r"D:/gas_cylinders/real_photo/93_real_photos/v2_split/test33.txt"
SEED = 42
VAL_RATIO = 0.2

rng = random.Random(SEED)

imgs = sorted(POOL.glob("images/*.png")) + sorted(POOL.glob("images/*.jpg"))
assert imgs, f"empty pool: {POOL / 'images'}"

pos, neg = [], []
for p in imgs:
    lp = POOL / "labels" / (p.stem + ".txt")
    assert lp.exists(), f"missing label for {p}"
    (neg if lp.stat().st_size == 0 else pos).append(p)
print(f"pool: pos={len(pos)} neg={len(neg)} total={len(pos)+len(neg)}")


def take(lst):
    k = min(len(lst), int(len(lst) * VAL_RATIO + 0.5))
    rng.shuffle(lst)
    return sorted(lst[k:]), sorted(lst[:k])


pos_tr, pos_va = take(pos)
neg_tr, neg_va = take(neg)
train = sorted(str(p).replace(os.sep, "/") for p in pos_tr + neg_tr)
val = sorted(str(p).replace(os.sep, "/") for p in pos_va + neg_va)
assert len(set(train) & set(val)) == 0
assert len(train) + len(val) == len(imgs)

test_lines = [l.strip().replace("\\", "/") for l in Path(TEST33_TXT).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
assert len(test_lines) == 33, f"expected 33 test lines, got {len(test_lines)}"
assert not (set(test_lines) & set(train + val)), "test photos leaked into train/val"


def n_boxes(paths):
    n = 0
    for p in paths:
        lp = POOL / "labels" / (Path(p).stem + ".txt")
        n += sum(1 for line in lp.read_text(encoding="utf-8").splitlines() if line.strip())
    return n


OUT.mkdir(parents=True, exist_ok=True)
(OUT / "train.txt").write_text("\n".join(train) + "\n", encoding="utf-8")
(OUT / "val.txt").write_text("\n".join(val) + "\n", encoding="utf-8")
info = {
    "seed": SEED,
    "val_ratio": VAL_RATIO,
    "pool": str(POOL).replace(os.sep, "/"),
    "note": "leak-free pool: every generated image's edit source is outside v2 test33",
    "train": {"total": len(train), "pos": len(pos_tr), "neg": len(neg_tr), "boxes": n_boxes(train)},
    "val": {"total": len(val), "pos": len(pos_va), "neg": len(neg_va), "boxes": n_boxes(val)},
    "test": {"total": len(test_lines), "source": TEST33_TXT, "note": "v2 clean test"},
}
(OUT / "split_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(OUT / "data.yaml").write_text(
    "names:\n"
    "  0: Placement Issues\n"
    f"path: {str(POOL).replace(os.sep, '/')}\n"
    "train: split/train.txt\n"
    "val: split/val.txt\n"
    f"test: {TEST33_TXT.replace(os.sep, '/')}\n",
    encoding="utf-8",
)
print(f"train={len(train)} (pos {len(pos_tr)} / neg {len(neg_tr)}), boxes={info['train']['boxes']}")
print(f"val  ={len(val)} (pos {len(pos_va)} / neg {len(neg_va)}), boxes={info['val']['boxes']}")
print(f"test = v2 test33 (33 real photos); data.yaml -> {OUT / 'data.yaml'}")
