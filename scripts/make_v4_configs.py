r"""v4 configs: development list and per-arm YAMLs under D:/gas_cylinders/v4.

The 61 independently sourced web images are a development benchmark in v4. They
support fixed-endpoint reporting, cross-fitted checkpoint selection, and final
deployment-model selection. They are not described as a sealed final test set.

Outputs (rerunnable, deterministic):
  D:/gas_cylinders/v4/dev61.txt          absolute paths of the v4 development set
  D:/gas_cylinders/v4/real93_train.txt   absolute paths of the 93 real photos
  D:/gas_cylinders/v4/data_dev61.yaml    eval-only yaml
  D:/gas_cylinders/v4/data_real93.yaml   arm A yaml (test key points to dev61)
"""
from pathlib import Path

GAS = Path(r"D:/gas_cylinders")
V4 = GAS / "v4"
DEV_DIR = GAS / "new_test_set" / "images"
REAL93_TXT = GAS / "real_photo" / "93_real_photos" / "v1_split" / "all.txt"
NAMES = "names:\n  0: Placement Issues\n"


def main():
    V4.mkdir(parents=True, exist_ok=True)

    imgs = sorted(p for p in DEV_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    assert len(imgs) == 61, f"expected 61 development images in {DEV_DIR}, got {len(imgs)}"
    (V4 / "dev61.txt").write_text(
        "\n".join(str(p).replace("\\", "/") for p in imgs) + "\n", encoding="utf-8")

    real = sorted(l.strip().replace("\\", "/") for l in
                  REAL93_TXT.read_text(encoding="utf-8-sig").splitlines() if l.strip())
    assert len(real) == 93, f"expected 93 real photos, got {len(real)}"
    (V4 / "real93_train.txt").write_text("\n".join(real) + "\n", encoding="utf-8")

    (V4 / "data_dev61.yaml").write_text(
        NAMES + "path: D:/gas_cylinders\n"
        "train: v4/dev61.txt\nval: v4/dev61.txt\ntest: v4/dev61.txt\n", encoding="utf-8")
    (V4 / "data_real93.yaml").write_text(
        NAMES + "path: D:/gas_cylinders\n"
        "train: v4/real93_train.txt\nval: v4/real93_train.txt\ntest: v4/dev61.txt\n", encoding="utf-8")

    print(f"dev61: {len(imgs)} images | real93: {len(real)} photos")
    print(f"wrote {V4}/dev61.txt, real93_train.txt, data_dev61.yaml, data_real93.yaml")


if __name__ == "__main__":
    main()
