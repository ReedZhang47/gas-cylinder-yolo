r"""Phase 1: stratified split of first500 dataset -> D:\yolo\splits\{train,val,test}.txt + data.yaml

Stratification: by name-prefix group (color x group, 25 groups x 20 imgs), 16/2/2 per group.
Empty-label images are forced into train. Seed fixed to 42. Absolute image paths in lists.
"""
import os
import random

SRC = r"D:/gas_cylinders/first500"
OUT = r"D:/yolo/splits"
SEED = 42

rng = random.Random(SEED)

with open(os.path.join(SRC, "train.txt"), encoding="utf-8-sig") as f:  # strip BOM
    lines = [l.strip() for l in f if l.strip()]
assert len(lines) == 500, f"expected 500 lines, got {len(lines)}"

def label_path(img_rel):
    base = os.path.basename(img_rel)          # xxx.png
    stem = os.path.splitext(base)[0]          # xxx
    return os.path.join(SRC, "labels", stem + ".txt")

def is_empty(img_rel):
    lp = label_path(img_rel)
    assert os.path.exists(lp), f"missing label for {img_rel}"
    return os.path.getsize(lp) == 0

empty_flags = {img: is_empty(img) for img in lines}

groups = {}
for img in lines:
    stem = os.path.splitext(os.path.basename(img))[0]   # e.g. blue_gas_cylinders_1_00001_
    parts = stem.split("_")                            # last two: index, trailing ''
    grp = "_".join(parts[:-2])                         # e.g. blue_gas_cylinders_1
    groups.setdefault(grp, []).append(img)
assert len(groups) == 25, f"expected 25 groups, got {len(groups)}"

train, val, test = [], [], []
adjust_records = []
for grp in sorted(groups):
    imgs = groups[grp]
    non_empty = [i for i in imgs if not empty_flags[i]]
    rng.shuffle(non_empty)
    # val=2, test=2 from non-empty; empty images forced into train
    g_val = non_empty[:2]
    g_test = non_empty[2:4]
    g_train = non_empty[4:] + [i for i in imgs if empty_flags[i]]
    for tag, lst in (("train", g_train), ("val", g_val), ("test", g_test)):
        assert len(lst) == 16 if tag == "train" else len(lst) == 2, f"{grp} {tag} {len(lst)}"
    train += g_train
    val += g_val
    test += g_test
    n_empty = sum(1 for i in imgs if empty_flags[i])
    if n_empty:
        adjust_records.append((grp, n_empty, [os.path.basename(i) for i in imgs if empty_flags[i]]))

def abs_lines(imgs):
    return [os.path.join(SRC.replace("/", os.sep), i.replace("/", os.sep)).replace(os.sep, "/") for i in imgs]

train_abs = abs_lines(train)
val_abs = abs_lines(val)
test_abs = abs_lines(test)

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "train.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(train_abs) + "\n")
with open(os.path.join(OUT, "val.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(val_abs) + "\n")
with open(os.path.join(OUT, "test.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(test_abs) + "\n")

yaml = (
    "names:\n"
    "  0: Upside-down\n"
    "train: D:/yolo/splits/train.txt\n"
    "val:   D:/yolo/splits/val.txt\n"
    "test:  D:/yolo/splits/test.txt\n"
)
with open(os.path.join(OUT, "data.yaml"), "w", encoding="utf-8") as f:
    f.write(yaml)

print(f"train={len(train_abs)} val={len(val_abs)} test={len(test_abs)}")
print(f"union={len(set(train_abs) | set(val_abs) | set(test_abs))}")
print(f"overlap_train_val={len(set(train_abs) & set(val_abs))} overlap_val_test={len(set(val_abs) & set(test_abs))} overlap_train_test={len(set(train_abs) & set(test_abs))}")
print(f"groups={len(groups)}")
empty_adjust_total = sum(e for _, e, _ in adjust_records)
print(f"empty-label images forced into train: {empty_adjust_total} in {len(adjust_records)} groups: {adjust_records}")