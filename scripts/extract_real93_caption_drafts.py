"""Extract the original per-photo descriptions into draft LoRA caption sidecars.

This preserves the Gemini descriptions verbatim. It never modifies source photos,
YOLO labels, or any reviewed caption folder.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "Prompts_Based_on_real93.md"
IMAGES = Path(r"D:\gas_cylinders\real_photo\93_real_photos\images")
OUTPUT = ROOT / "docs" / "v5_prompts" / "captions_from_original_draft"


def parse_descriptions(text: str) -> dict[str, str]:
    pattern = re.compile(r"^```(real_photo_(\d+)\.png)\s*\n(.*?)\n```\s*$", re.M | re.S)
    found: dict[str, str] = {}
    for match in pattern.finditer(text):
        filename, number, body = match.groups()
        if filename in found:
            raise ValueError(f"Duplicate source description: {filename}")
        if not body.strip():
            raise ValueError(f"Empty source description: {filename}")
        found[filename] = " ".join(body.split())
    expected = {f"real_photo_{i}.png" for i in range(1, 94)}
    if set(found) != expected:
        raise ValueError(
            f"Descriptions mismatch: missing={sorted(expected - set(found))}, "
            f"extra={sorted(set(found) - expected)}"
        )
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    descriptions = parse_descriptions(SOURCE.read_text(encoding="utf-8"))
    image_names = {path.name for path in IMAGES.glob("*.png")}
    if image_names != set(descriptions):
        raise SystemExit("Real-photo images differ from description IDs; no output written")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    existing = list(output.glob("*.txt"))
    if existing:
        raise SystemExit(f"Output already has {len(existing)} .txt files; refusing to overwrite: {output}")

    for image_name in sorted(descriptions, key=lambda name: int(re.search(r"\d+", name).group())):
        (output / Path(image_name).with_suffix(".txt").name).write_text(
            descriptions[image_name] + "\n", encoding="utf-8"
        )
    print(f"Extracted {len(descriptions)} draft captions to {output}")


if __name__ == "__main__":
    main()
