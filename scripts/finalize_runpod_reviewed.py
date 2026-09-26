"""Validate the user-reviewed extracted real93 bundle and make a trainable tar.

This checks machine consistency, not the semantic truth of every caption.
It never changes the user's DRAFT CSV or individual caption files.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import tarfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".tmp/runpod_qwen21"
DATA = BASE / "real93"
ORIGINAL = BASE / "real93_DRAFT.tar"
TRIGGER = "cylsite93, "


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add_bytes(out: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = 0o644
    out.addfile(info, io.BytesIO(data))


def main() -> None:
    expected = {f"real_photo_{i}" for i in range(1, 94)}
    for folder, extension in (("images", ".png"), ("yolo_labels", ".txt"), ("captions", ".txt")):
        present = {p.stem for p in (DATA / folder).glob(f"*{extension}") if p.is_file()}
        if present != expected:
            raise ValueError(f"{folder}: missing={expected-present}, extra={present-expected}")

    csv_path = DATA / "metadata.DRAFT.csv"
    csv_bytes = csv_path.read_bytes()
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != ["image", "prompt"]:
        raise ValueError(f"Unexpected CSV columns: {reader.fieldnames}")
    rows = list(reader)
    if len(rows) != 93:
        raise ValueError(f"Expected 93 CSV rows, got {len(rows)}")
    row_map = {row["image"]: row for row in rows}
    wanted_paths = {f"images/{stem}.png" for stem in expected}
    if set(row_map) != wanted_paths or len(row_map) != len(rows):
        raise ValueError("CSV image paths are missing, duplicated, or extra")
    if any(row.get(None) for row in rows):
        raise ValueError("CSV contains extra unheaded columns")

    changed_captions = []
    changed_csv_rows = []
    mismatches = []
    file_manifest = {}
    with tarfile.open(ORIGINAL, "r") as original:
        old_csv = original.extractfile("real93/metadata.DRAFT.csv")
        assert old_csv is not None
        old_rows = {r["image"]: r["prompt"] for r in csv.DictReader(io.StringIO(old_csv.read().decode()))}
        for index in range(1, 94):
            stem = f"real_photo_{index}"
            image_rel = f"images/{stem}.png"
            caption = " ".join((DATA / "captions" / f"{stem}.txt").read_text(encoding="utf-8-sig").split())
            prompt = " ".join(row_map[image_rel]["prompt"].split())
            if not caption or not prompt.startswith(TRIGGER) or prompt.removeprefix(TRIGGER) != caption:
                mismatches.append({"image": stem, "caption": caption, "csv_prompt": prompt})
            if "black gas cylinder" in caption.lower() or "dark gas cylinder" in caption.lower():
                raise ValueError(f"Ambiguous black/dark cylinder: {stem}")
            with Image.open(DATA / image_rel) as im:
                im.verify()
            for folder, extension in (("images", "png"), ("yolo_labels", "txt")):
                rel = f"{folder}/{stem}.{extension}"
                current = (DATA / rel).read_bytes()
                source = original.extractfile(f"real93/{rel}")
                assert source is not None
                if current != source.read():
                    raise ValueError(f"Image or YOLO label changed unexpectedly: {rel}")
                file_manifest[rel] = sha(current)
            current_cap = (DATA / "captions" / f"{stem}.txt").read_bytes()
            old_cap = original.extractfile(f"real93/captions/{stem}.txt")
            assert old_cap is not None
            if current_cap != old_cap.read():
                changed_captions.append(stem)
            if prompt != " ".join(old_rows[image_rel].split()):
                changed_csv_rows.append(stem)
            file_manifest[f"captions/{stem}.txt"] = sha(current_cap)

    if mismatches:
        report = {"mismatches": mismatches, "changed_caption_ids": changed_captions, "changed_csv_row_ids": changed_csv_rows}
        (BASE / "review_mismatches.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise ValueError(f"{len(mismatches)} CSV/caption mismatches; see {BASE / 'review_mismatches.json'}")

    final_csv = DATA / "metadata.csv"
    if final_csv.exists() and final_csv.read_bytes() != csv_bytes:
        raise ValueError("Existing metadata.csv differs from reviewed DRAFT CSV")
    final_csv.write_bytes(csv_bytes)
    manifest = {
        "status": "user_reviewed_machine_validated",
        "caption_count": 93,
        "trigger": TRIGGER.strip(", "),
        "metadata_sha256": sha(csv_bytes),
        "changed_caption_ids": changed_captions,
        "changed_csv_row_ids": changed_csv_rows,
        "file_sha256": file_manifest,
    }
    target = BASE / "real93_REVIEWED.tar"
    with tarfile.open(target, "w") as out:
        for index in range(1, 94):
            stem = f"real_photo_{index}"
            for folder, extension in (("images", "png"), ("yolo_labels", "txt"), ("captions", "txt")):
                rel = f"{folder}/{stem}.{extension}"
                out.add(DATA / rel, arcname=f"real93/{rel}", recursive=False)
        add_bytes(out, "real93/metadata.csv", csv_bytes)
        add_bytes(out, "real93/MANIFEST_REVIEWED.json", json.dumps(manifest, indent=2).encode())
    report = {
        "archive": str(target),
        "archive_sha256": sha(target.read_bytes()),
        "archive_bytes": target.stat().st_size,
        "changed_caption_ids": changed_captions,
        "changed_csv_row_ids": changed_csv_rows,
        "training_rows": len(rows),
    }
    (BASE / "review_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
