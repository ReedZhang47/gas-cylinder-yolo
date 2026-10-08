"""Build reviewable, machine-readable v5 Arm D prompt sets.

The TSV files are the editable source. The JSONL files are the exact text to send
to ComfyUI after human review. This script never queues a generation.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STYLE = (
    "A realistic, unstaged construction-site inspection photograph with natural "
    "camera perspective and believable materials. "
)
STYLE_OVERRIDES = {
    "R001": "A realistic full-frame construction-site camera photograph, one continuous edge-to-edge photographic scene with natural perspective and believable materials. ",
}
COUNT_RULES = {
    0: "No gas cylinders are visible anywhere in the frame.",
    1: (
        "Exactly one complete industrial gas cylinder is visible; its full body "
        "has a clear outline, with no object crossing it. No other gas cylinders."
    ),
    2: (
        "Exactly two complete industrial gas cylinders are visible, clearly "
        "separated from each other, with no overlap or object crossing either "
        "body. No other gas cylinders."
    ),
}
FINISH = "No collage, illustration, watermark, captions, or legible brand text."
VALID_PLACEMENT = {"none", "unsecured", "rack", "trolley", "mixed", "secured"}


def build(stem: str, expected: int, prefix: str) -> list[dict[str, object]]:
    source = ROOT / f"{stem}_cores.tsv"
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert len(rows) == expected, (stem, len(rows), expected)
    assert len({row["id"] for row in rows}) == expected
    assert len({row["prompt_core"] for row in rows}) == expected

    result = []
    for index, row in enumerate(rows, 1):
        assert row["id"] == f"{prefix}{index:03d}", row["id"]
        count = int(row["count"])
        assert count in COUNT_RULES, row
        assert row["placement"] in VALID_PLACEMENT, row
        if count == 0:
            assert row["placement"] == "none", row
        else:
            assert row["placement"] != "none", row
        prompt = STYLE_OVERRIDES.get(row["id"], STYLE) + row["prompt_core"].strip() + " " + COUNT_RULES[count] + " " + FINISH
        item: dict[str, object] = {
            "id": row["id"],
            "set": stem,
            "intended_cylinder_count": count,
            "placement": row["placement"],
            "prompt": prompt,
            "review_status": "draft",
        }
        if stem == "real93":
            assert row["source_photo"] == f"real_photo_{index}.png", row
            item["source_photo"] = row["source_photo"]
        else:
            item["group"] = row["group"]
        result.append(item)

    destination = ROOT / f"{stem}_prompts.jsonl"
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for item in result:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(destination)
    print("count:", len(result))
    print("placement:", dict(Counter(item["placement"] for item in result)))
    print("cylinder count:", dict(Counter(item["intended_cylinder_count"] for item in result)))
    return result


if __name__ == "__main__":
    build("real93", 93, "R")
    build("new150", 150, "N")
