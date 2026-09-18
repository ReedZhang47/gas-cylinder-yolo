r"""v3 configs (2026-09-19): test list + per-arm yamls under D:/gas_cylinders/v3.

v3 protocol: test = new_test_set (61 web images, independent of every training
source); arms differ only in training data (A real93 / B real93+classical
augmentation / C Qwen-Image-Edit synthesis).

Outputs (rerunnable, deterministic):
  D:/gas_cylinders/v3/test61.txt         absolute image paths of the v3 test
  D:/gas_cylinders/v3/real93_train.txt   absolute paths of the 93 real photos
  D:/gas_cylinders/v3/data_test61.yaml   eval-only yaml (train=val=test=test61)
  D:/gas_cylinders/v3/data_real93.yaml   arm A yaml (train=val=93, test=test61)
"""
from pathlib import Path

GAS = Path(r"D:/gas_cylinders")
V3 = GAS / "v3"
TEST_DIR = GAS / "new_test_set" / "images"
REAL93_TXT = GAS / "real_photo" / "93_real_photos" / "v1_split" / "all.txt"
NAMES = "names:\n  0: Placement Issues\n"


def main():
    V3.mkdir(parents=True, exist_ok=True)

    imgs = sorted(p for p in TEST_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    assert imgs, f"no test images in {TEST_DIR}"
    (V3 / "test61.txt").write_text(
        "\n".join(str(p).replace("\\", "/") for p in imgs) + "\n", encoding="utf-8")

    real = sorted(l.strip().replace("\\", "/") for l in
                  REAL93_TXT.read_text(encoding="utf-8-sig").splitlines() if l.strip())
    assert len(real) == 93, f"expected 93 real photos, got {len(real)}"
    (V3 / "real93_train.txt").write_text("\n".join(real) + "\n", encoding="utf-8")

    (V3 / "data_test61.yaml").write_text(
        NAMES + "path: D:/gas_cylinders\n"
        "train: v3/test61.txt\nval: v3/test61.txt\ntest: v3/test61.txt\n", encoding="utf-8")
    (V3 / "data_real93.yaml").write_text(
        NAMES + "path: D:/gas_cylinders\n"
        "train: v3/real93_train.txt\nval: v3/real93_train.txt\ntest: v3/test61.txt\n", encoding="utf-8")

    print(f"test61: {len(imgs)} images | real93: {len(real)} photos")
    print(f"wrote {V3}/test61.txt, real93_train.txt, data_test61.yaml, data_real93.yaml")


if __name__ == "__main__":
    main()
