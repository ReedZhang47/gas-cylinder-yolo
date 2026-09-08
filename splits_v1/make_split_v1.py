r"""v1 split of the 93 real photos -> stratified train/val (80/20, seed=42).

Purpose: labeler-model training (Prompt.md 2026-09-02). Positives = label file
non-empty (Placement Issues boxes), negatives = empty label file. Stratified so
val keeps the pos/neg ratio. No test split by design (see PROGRESS.md section 5).

Outputs (does NOT touch the dataset's own train.txt manifest of all 93):
  D:/gas_cylinders/real_photo/93_real_photos/v1_split/train.txt   (abs paths)
  D:/gas_cylinders/real_photo/93_real_photos/v1_split/val.txt     (abs paths)
  D:/gas_cylinders/real_photo/93_real_photos/v1_split/split_info.json
and rewrites data.yaml in place to point train/val at v1_split (adds the
missing val key required by ultralytics).
"""
import json
import os
import random

ROOT = r"D:/gas_cylinders/real_photo/93_real_photos"
OUT = os.path.join(ROOT, "v1_split")
SEED = 42
VAL_RATIO = 0.2

rng = random.Random(SEED)

with open(os.path.join(ROOT, "train.txt"), encoding="utf-8-sig") as f:
    rels = [l.strip().replace("\\", "/") for l in f if l.strip()]
assert len(rels) == 93, f"expected 93 lines, got {len(rels)}"


def label_path(rel: str) -> str:
    return os.path.join(ROOT, "labels", os.path.splitext(os.path.basename(rel))[0] + ".txt")


pos, neg = [], []
for rel in rels:
    lp = label_path(rel)
    assert os.path.exists(lp), f"missing label for {rel}"
    (neg if os.path.getsize(lp) == 0 else pos).append(rel)
print(f"pos={len(pos)} neg={len(neg)} total={len(pos)+len(neg)}")


def take(lst):
    """Round-half-up share for val, at least 1 element when lst non-empty."""
    k = min(len(lst), int(len(lst) * VAL_RATIO + 0.5))
    rng.shuffle(lst)
    return sorted(lst[k:]), sorted(lst[:k])  # (train_part, val_part)


def abs_path(rel: str) -> str:
    return os.path.join(ROOT, rel).replace(os.sep, "/")


pos_tr, pos_va = take(pos)
neg_tr, neg_va = take(neg)
train = sorted(abs_path(r) for r in pos_tr + neg_tr)
val = sorted(abs_path(r) for r in pos_va + neg_va)
assert len(set(train) & set(val)) == 0
assert len(train) + len(val) == 93

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "train.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(train) + "\n")
with open(os.path.join(OUT, "val.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(val) + "\n")

n_boxes = sum(sum(1 for _ in open(label_path(r), encoding="utf-8")) for r in val)
info = {
    "seed": SEED,
    "val_ratio": VAL_RATIO,
    "train": {"total": len(train), "pos": len(pos_tr), "neg": len(neg_tr)},
    "val": {"total": len(val), "pos": len(pos_va), "neg": len(neg_va), "boxes": n_boxes},
    "val_images": val,
}
with open(os.path.join(OUT, "split_info.json"), "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=2)

yaml_text = (
    "names:\n"
    "  0: Placement Issues\n"
    f"path: {ROOT}\n"
    "train: v1_split/train.txt\n"
    "val: v1_split/val.txt\n"
)
with open(os.path.join(ROOT, "data.yaml"), "w", encoding="utf-8") as f:
    f.write(yaml_text)

print(f"train={len(train)} (pos {len(pos_tr)} / neg {len(neg_tr)})")
print(f"val={len(val)} (pos {len(pos_va)} / neg {len(neg_va)}), val boxes={n_boxes}")
print("val images:")
for r in val:
    print(" ", os.path.basename(r))
