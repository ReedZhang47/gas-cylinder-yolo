"""Reconcile five image-checked real93 captions before the Runpod archive audit."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".tmp/runpod_qwen21/real93"
BACKUP = ROOT / ".tmp/runpod_qwen21/review_before_reconcile"
TRIGGER = "cylsite93, "
CORRECTIONS = {
    20: (
        "A documentary photograph at a muddy construction site in daylight. "
        "A worker wearing a high-visibility vest and hard hat stands in the doorway of a small corrugated metal shed. "
        "A weathered off-white gas cylinder stands upright beside the worker, with a red fire extinguisher nearby. "
        "The foreground contains muddy puddles, scattered planks, metal sheets, hoses, and construction debris, "
        "with fencing and a crane in the background."
    ),
    23: (
        "A candid documentary photograph at a construction site in daylight. "
        "A worker wearing a camouflage shirt, bright blue reflective safety vest, and dark pants stands beside "
        "a blue RONGYI NBC-500 welding machine. A weathered off-white gas cylinder with a regulator stands upright "
        "behind the machine; red hoses run from it across the concrete floor. A red fire extinguisher hangs nearby. "
        "Heavy steel beams, cardboard boxes, cables, and a water bottle surround the work area."
    ),
    30: (
        "A documentary photograph of a messy outdoor construction site floor under bright daylight. "
        "Two large, weathered blue industrial gas cylinders lie on their sides on unfinished concrete. "
        "Several long pieces of rebar rest across the cylinders. Scattered construction debris, including "
        "woven sacks, loose metal parts, a piece of wood, and dirt, covers the ground. "
        "A large steel rebar framework is under construction in the background."
    ),
}


def main() -> None:
    csv_path = DATA / "metadata.DRAFT.csv"
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        assert reader.fieldnames == ["image", "prompt"]
        rows = list(reader)
    assert len(rows) == 93
    if BACKUP.exists():
        raise FileExistsError(f"Review backup already exists; refusing to overwrite: {BACKUP}")
    BACKUP.mkdir(parents=True)
    shutil.copy2(csv_path, BACKUP / csv_path.name)
    record = []
    for row in rows:
        stem = Path(row["image"]).stem
        number = int(stem.removeprefix("real_photo_"))
        if number not in (20, 23, 30, 71, 77):
            continue
        caption_path = DATA / "captions" / f"{stem}.txt"
        old_caption = caption_path.read_text(encoding="utf-8-sig").strip()
        shutil.copy2(caption_path, BACKUP / caption_path.name)
        new_caption = CORRECTIONS.get(number, old_caption)
        caption_path.write_text(new_caption + "\n", encoding="utf-8")
        record.append({"image": stem, "old_caption": old_caption, "old_csv_prompt": row["prompt"], "new_caption": new_caption})
        row["prompt"] = TRIGGER + new_caption
    with csv_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["image", "prompt"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (BACKUP / "reconciliation.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Reconciled {len(record)} image captions; backup: {BACKUP}")


if __name__ == "__main__":
    main()
