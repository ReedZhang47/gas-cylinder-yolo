r"""Render each arm's deployment predictions on every dev61 image as a standalone PNG.

Working asset for the qualitative detection figure: 61 dev61 images x 3 arms = 183 files,
outside the repo in D:\gas_cylinders\detection_dev61\<arm>\, so panels can be hand-picked and
laid out. Every box carries the confidence. No ground-truth overlay here: make_figures.py
--fig detections draws the label panel next to the arms; a renderer that baked it in would
duplicate the same dashed boxes in all three arm folders.

Predictions come from the qualitative_detections.json cache (written by make_figures.py), so
this renderer never runs inference and cannot disagree with the composed figure. The cached
checkpoint paths are checked against the recorded deployment models before anything is drawn.

Colours are intentionally *not* make_figures.ARM_COLOR: the class is a placement violation,
so all three arms use hazard colours rather than a categorical palette whose cool slots read
as "fine" next to a fault. See ALERT_COLOR.

Line width and font size scale with the image width so the result survives being placed in a
figure at any size: det_panel draws a 1.4 pt box and 5.5 pt confidence text on a 2.69 in
panel, i.e. about 0.7% and 3.1% of the panel width, and those ratios are what --scale keeps.

Usage:
  python paper/render_dev61_detections.py
  python paper/render_dev61_detections.py --scale 1.3
  python paper/render_dev61_detections.py --conf 0.5 --out D:\gas_cylinders\detection_dev61_050
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPER_DIR))
import make_figures as mf  # palette, arm order, detection cache, deployment checkpoints

OUT_DEFAULT = Path(r"D:/gas_cylinders/detection_dev61")
ARM_DIR = {"real93v4": "A_real93", "aug1085v4": "B_aug1085", "gen1085v4": "C_gen1085"}
# Hazard palette for this figure, deliberately not make_figures.ARM_COLOR: the labelled class is
# a placement violation, so a cool categorical hue reads as "fine" next to a fault. Red -> orange
# -> yellow also ramps lightness (darkest -> mid -> brightest), so the arms stay separable in
# greyscale as well as in colour.
ALERT_COLOR = {"real93v4": "#d03b3b", "aug1085v4": "#f2c200", "gen1085v4": "#ff7f0e"}
BOX_FRACTION = 0.0072   # of image width, from det_panel's 1.4 pt on a 2.69 in panel
TEXT_FRACTION = 0.031   # of image width, from det_panel's 5.5 pt on the same panel
FONT_PATH = Path(__import__("matplotlib").font_manager.findfont("DejaVu Sans"))


def verify_cache(cache: dict) -> None:
    for arm in mf.ARM_ORDER:
        expected = str(mf.deploy_weights(arm).relative_to(mf.ROOT)).replace("\\", "/")
        recorded = cache["weights"][arm].replace("\\", "/")
        if recorded != expected:
            raise SystemExit(f"{arm}: cache was built from {recorded}, deployment model is now "
                             f"{expected}; re-run make_figures.py --fig detections --refresh")


def draw(picture: Image.Image, detections: list[dict], color: str, conf: float, scale: float) -> int:
    width, height = picture.size
    line = max(2, round(width * BOX_FRACTION * scale))
    halo = max(1, round(line * 0.45))
    font = ImageFont.truetype(str(FONT_PATH), max(11, round(width * TEXT_FRACTION * scale)))
    pen = ImageDraw.Draw(picture)
    drawn = 0
    for detection in detections:
        if detection["conf"] < conf:
            continue
        x1, y1, x2, y2 = detection["xyxy"]
        x1, y1 = max(0.0, x1), max(0.0, y1)
        x2, y2 = min(width - 1.0, x2), min(height - 1.0, y2)
        if x2 <= x1 or y2 <= y1:
            continue
        # Pillow strokes a rectangle inwards from the given box, so the dark relief is drawn on an
        # outward-expanded box: it then sits outside the coloured line instead of showing up as a
        # second black frame inside the box.
        pen.rectangle((x1 - halo, y1 - halo, x2 + halo, y2 + halo), outline="black", width=halo)
        pen.rectangle((x1, y1, x2, y2), outline=color, width=line)
        text = f"{detection['conf']:.2f}"
        if y1 - font.size - halo >= 2:
            pen.text((x1 + halo, y1 - halo), text, font=font, fill=color, anchor="ls",
                     stroke_width=halo, stroke_fill="black")
        else:
            pen.text((x1 + halo, y1 + halo), text, font=font, fill=color, anchor="la",
                     stroke_width=halo, stroke_fill="black")
        drawn += 1
    return drawn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT_DEFAULT))
    parser.add_argument("--conf", type=float, default=mf.DET_CONF,
                        help="display threshold; the cache itself holds every box above its "
                             f"recorded conf_floor (default {mf.DET_CONF})")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="multiply box width and font size (default 1.0)")
    parser.add_argument("--arms", default=",".join(mf.ARM_ORDER))
    args = parser.parse_args()

    arms = [arm for arm in args.arms.split(",") if arm]
    unknown = [arm for arm in arms if arm not in mf.ARM_ORDER]
    if unknown:
        raise SystemExit(f"unknown arm(s) {unknown}; expected {mf.ARM_ORDER}")

    cache = mf.load_detections()
    verify_cache(cache)
    out_root = Path(args.out)
    totals: Counter[str] = Counter()
    blank: Counter[str] = Counter()

    for arm in arms:
        folder = out_root / ARM_DIR[arm]
        folder.mkdir(parents=True, exist_ok=True)
        for name, entry in sorted(cache["images"].items()):
            source = Path(entry["path"])
            with Image.open(source) as handle:
                picture = handle.convert("RGB")
            drawn = draw(picture, entry["arms"][arm], ALERT_COLOR[arm], args.conf, args.scale)
            picture.save(folder / f"{source.stem}.png")
            totals[arm] += drawn
            if drawn == 0:
                blank[arm] += 1
        print(f"{ARM_DIR[arm]:<12} -> {folder}  boxes={totals[arm]}  "
              f"images without a box={blank[arm]}/{len(cache['images'])}", flush=True)

    print(f"\nconf>={args.conf}  scale={args.scale}  images={len(cache['images'])}  arms={len(arms)}  "
          f"files={len(cache['images']) * len(arms)}  boxes={sum(totals.values())}")
    print("colours: " + "  ".join(f"{ARM_DIR[a]}={ALERT_COLOR[a]}" for a in arms))


if __name__ == "__main__":
    main()
