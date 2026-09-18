r"""Real-photo v2 split (2026-09-17, 方案 A): 93 real photos ->
stratified train 60 (37 pos + 23 neg) / test 33 (20 pos + 13 neg).

Why: the v1 clean subset (val18 = 18 photos / 30 boxes) is too small to
support the three-arm comparison; test33 (~60 boxes) becomes the single
clean test for every arm. v1_split/ is kept untouched.

Protocol (paper-wide, same decision): test33 is never used for training or
checkpoint selection; detectors are reported at the final epoch (last.pt).

Outputs (D:/gas_cylinders/real_photo/93_real_photos/v2_split/):
  train60.txt / test33.txt   ABSOLUTE image paths, one per line
  split_info.json            seed / counts / boxes / notes
  data_real_v2.yaml          train=val=train60.txt, test=test33.txt
                             (trains the real baseline; evaluates ANY arm
                              on test33; val points at the train list on
                              purpose - no real validation data is used)

Does NOT touch v1_split/ or the annotator workspace data.yaml.
"""
import json
import os
import random
from pathlib import Path

ROOT = Path(r"D:/gas_cylinders/real_photo/93_real_photos")
OUT = ROOT / "v2_split"
SEED = 42
N_TRAIN = 60          # 93 x 60/93 ~= 65/35; test power is the binding constraint
EXPECTED = 93

rng = random.Random(SEED)

imgs = sorted(p for p in (ROOT / "images").iterdir()
              if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"})
assert len(imgs) == EXPECTED, f"expected {EXPECTED} images, got {len(imgs)}"

pos, neg = [], []
for p in imgs:
    lp = ROOT / "labels" / (p.stem + ".txt")
    assert lp.exists(), f"missing label for {p.name}"
    (neg if lp.stat().st_size == 0 else pos).append(p)
print(f"pos={len(pos)} neg={len(neg)} total={len(pos)+len(neg)}")

n_pos_tr = min(len(pos), round(len(pos) * N_TRAIN / EXPECTED))
n_neg_tr = N_TRAIN - n_pos_tr
assert n_neg_tr <= len(neg), "not enough negatives for the requested train size"

rng.shuffle(pos)
rng.shuffle(neg)
pos_tr, pos_te = sorted(pos[:n_pos_tr]), sorted(pos[n_pos_tr:])
neg_tr, neg_te = sorted(neg[:n_neg_tr]), sorted(neg[n_neg_tr:])

train = sorted(str(p).replace(os.sep, "/") for p in pos_tr + neg_tr)
test = sorted(str(p).replace(os.sep, "/") for p in pos_te + neg_te)
assert len(set(train) & set(test)) == 0
assert len(train) == N_TRAIN and len(train) + len(test) == EXPECTED


def n_boxes(paths):
    n = 0
    for p in paths:
        lp = ROOT / "labels" / (Path(p).stem + ".txt")
        n += sum(1 for line in lp.read_text(encoding="utf-8").splitlines() if line.strip())
    return n


info = {
    "seed": SEED,
    "rule": f"shuffle within class (random.Random({SEED})), take train counts first",
    "revision": "2026-09-17 方案 A: v2 replaces v1 val18 as the single clean test",
    "train": {"total": len(train), "pos": len(pos_tr), "neg": len(neg_tr), "boxes": n_boxes(train)},
    "test": {"total": len(test), "pos": len(pos_te), "neg": len(neg_te), "boxes": n_boxes(test),
             "note": "clean test - no arm trains or selects on these 33 photos"},
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "train60.txt").write_text("\n".join(train) + "\n", encoding="utf-8")
(OUT / "test33.txt").write_text("\n".join(test) + "\n", encoding="utf-8")
(OUT / "split_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

yaml_text = (
    "names:\n"
    "  0: Placement Issues\n"
    f"path: {str(ROOT).replace(os.sep, '/')}\n"
    "train: v2_split/train60.txt\n"
    "val: v2_split/train60.txt\n"
    "test: v2_split/test33.txt\n"
)
(OUT / "data_real_v2.yaml").write_text(yaml_text, encoding="utf-8")

print(f"train={len(train)} (pos {len(pos_tr)} / neg {len(neg_tr)}), boxes={info['train']['boxes']}")
print(f"test ={len(test)} (pos {len(pos_te)} / neg {len(neg_te)}), boxes={info['test']['boxes']}")
print(f"wrote {OUT}/train60.txt, test33.txt, split_info.json, data_real_v2.yaml")
