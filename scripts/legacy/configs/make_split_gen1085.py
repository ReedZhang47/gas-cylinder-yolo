r"""Legacy v3 gen1085 train/val split generator. Originally merged the two
reviewed generated batches (Placement_Issues 493 + Placement_Issues_2 592) ->
stratified train/val (80/20, seed=42); test = the v3 independent web-image test
(`v3/test61.txt`, 61 images that share neither source nor scene with the seed
photos or with any image edited from them).

Second point of the quantity-vs-performance curve (first point: gen493).

Positives = non-empty label file, negatives = empty (stratified so both
splits keep the pos/neg ratio). ABSOLUTE paths in manifests (COMMANDS.md
pitfall 1), one data.yaml covering train/val/test.

Outputs (D:/gas_cylinders/gen1085_split/):
  train.txt / val.txt / split_info.json
  data.yaml   (train/val lists; test = v3/test61.txt, the 61 web images)

Does NOT touch either annotator workspace data.yaml.
"""
import json
import os
import random
from pathlib import Path

ROOTS = [Path(r"D:/gas_cylinders/Placement_Issues"),
         Path(r"D:/gas_cylinders/Placement_Issues_2")]
OUT = Path(r"D:/gas_cylinders/gen1085_split")
GAS_ROOT = Path(r"D:/gas_cylinders")
TEST_TXT = r"D:/gas_cylinders/v3/test61.txt"   # v3: independent web-image test
SEED = 42
VAL_RATIO = 0.2
EXPECTED = 1085

rng = random.Random(SEED)

imgs = []
for root in ROOTS:
    imgs += sorted(root.glob("images/*.png")) + sorted(root.glob("images/*.jpg"))
assert len(imgs) == EXPECTED, f"expected {EXPECTED} images, got {len(imgs)}"
stems = [p.stem for p in imgs]
assert len(set(stems)) == len(stems), "duplicate image stems across batches"

pos, neg = [], []
for p in imgs:
    lp = p.parent.parent / "labels" / (p.stem + ".txt")
    assert lp.exists(), f"missing label for {p}"
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
assert len(test_lines) == 61, f"expected 61 test lines, got {len(test_lines)}"
assert not (set(test_lines) & set(train + val)), "test images leaked into train/val"

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "train.txt").write_text("\n".join(train) + "\n", encoding="utf-8")
(OUT / "val.txt").write_text("\n".join(val) + "\n", encoding="utf-8")


def n_boxes(paths):
    n = 0
    for p in paths:
        lp = Path(p).parent.parent / "labels" / (Path(p).stem + ".txt")
        n += sum(1 for line in lp.read_text(encoding="utf-8").splitlines() if line.strip())
    return n


info = {
    "seed": SEED,
    "val_ratio": VAL_RATIO,
    "sources": [str(r).replace(os.sep, "/") for r in ROOTS],
    "revision": "2026-09-18 merge of the two reviewed generated batches (493 + 592)",
    "train": {"total": len(train), "pos": len(pos_tr), "neg": len(neg_tr), "boxes": n_boxes(train)},
    "val": {"total": len(val), "pos": len(pos_va), "neg": len(neg_va), "boxes": n_boxes(val)},
    "test": {"total": len(test_lines), "source": TEST_TXT,
             "note": "v3 test: 61 independent web images, never in any training source"},
}
(OUT / "split_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

yaml_text = (
    "names:\n"
    "  0: Placement Issues\n"
    f"path: {str(GAS_ROOT).replace(os.sep, '/')}\n"
    "train: gen1085_split/train.txt\n"
    "val: gen1085_split/val.txt\n"
    f"test: {TEST_TXT.replace(os.sep, '/')}\n"
)(OUT / "data.yaml").write_text(yaml_text, encoding="utf-8")

print(f"train={len(train)} (pos {len(pos_tr)} / neg {len(neg_tr)}), boxes={info['train']['boxes']}")
print(f"val  ={len(val)} (pos {len(pos_va)} / neg {len(neg_va)}), boxes={info['val']['boxes']}")
print(f"test = v3 test61 ({len(test_lines)} images), data.yaml written to {OUT / 'data.yaml'}")
