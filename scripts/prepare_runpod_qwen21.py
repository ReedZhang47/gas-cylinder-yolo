"""Build a local, auditable Runpod transfer bundle without starting cloud billing.

The default bundle is deliberately a DRAFT: it has no metadata.csv, so the
training launch script will refuse it. Pass --reviewed-captions after the 93
captions have been checked against the photographs to build a trainable bundle.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
IMAGES = Path(r"D:\gas_cylinders\real_photo\93_real_photos\images")
YOLO_LABELS = Path(r"D:\gas_cylinders\real_photo\93_real_photos\labels")
DRAFT_CAPTIONS = ROOT / "docs/v5_prompts/captions_from_original_draft"
FRAMEWORK = Path(r"D:\DiffSynth-Studio\DiffSynth-Studio")
OUTPUT = ROOT / ".tmp/runpod_qwen21"
TRIGGER = "cylsite93"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_bytes(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = 0o644
    archive.addfile(info, io.BytesIO(data))


def check_names(directory: Path, suffix: str, expected: set[str]) -> dict[str, Path]:
    files = {p.stem: p for p in directory.glob(f"*{suffix}") if p.is_file()}
    if set(files) != expected:
        raise ValueError(
            f"{directory}: missing={sorted(expected - set(files))}, "
            f"extra={sorted(set(files) - expected)}"
        )
    return files


def framework_archive(out: Path) -> tuple[Path, str]:
    safe = f"safe.directory={FRAMEWORK.as_posix()}"
    git = ["git", "-c", safe, "-C", str(FRAMEWORK)]
    status = subprocess.check_output(git + ["status", "--porcelain"], text=True).strip()
    if status:
        raise ValueError("DiffSynth-Studio checkout has local changes; archive only a clean revision")
    revision = subprocess.check_output(git + ["rev-parse", "HEAD"], text=True).strip()
    target = out / f"DiffSynth-Studio_{revision[:12]}.tar"
    if not target.exists():
        subprocess.run(git + ["archive", "--format=tar", f"--output={target}", "HEAD"], check=True)
    return target, revision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-captions", type=Path, help="93 human-reviewed .txt files")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    reviewed = args.reviewed_captions is not None
    captions_dir = args.reviewed_captions if reviewed else DRAFT_CAPTIONS
    if reviewed and captions_dir.resolve() == DRAFT_CAPTIONS.resolve():
        raise ValueError("Reviewed captions must live in a separate reviewed directory")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)

    expected = {f"real_photo_{i}" for i in range(1, 94)}
    images = check_names(IMAGES, ".png", expected)
    labels = check_names(YOLO_LABELS, ".txt", expected)
    captions = check_names(captions_dir, ".txt", expected)

    rows: list[tuple[str, str]] = []
    manifest: dict[str, object] = {
        "status": "reviewed" if reviewed else "DRAFT_NOT_FOR_TRAINING",
        "count": 93,
        "trigger_word": TRIGGER,
        "files": {},
    }
    for index in range(1, 94):
        stem = f"real_photo_{index}"
        with Image.open(images[stem]) as im:
            im.verify()
        caption = " ".join(captions[stem].read_text(encoding="utf-8-sig").split())
        if not caption or "[trigger]" in caption or TRIGGER in caption:
            raise ValueError(f"Invalid or already-triggered caption: {stem}")
        if "black gas cylinder" in caption.lower() or "dark gas cylinder" in caption.lower():
            raise ValueError(f"Ambiguous black/dark cylinder colour: {stem}")
        rows.append((f"images/{stem}.png", f"{TRIGGER}, {caption}"))
        for role, path in (("image", images[stem]), ("yolo_label", labels[stem]), ("caption", captions[stem])):
            manifest["files"][f"{role}/{path.name}"] = {"sha256": digest(path), "bytes": path.stat().st_size}

    csv_text = io.StringIO(newline="")
    writer = csv.writer(csv_text, lineterminator="\n")
    writer.writerow(("image", "prompt"))
    writer.writerows(rows)
    metadata_name = "metadata.csv" if reviewed else "metadata.DRAFT.csv"
    manifest["metadata_sha256"] = hashlib.sha256(csv_text.getvalue().encode()).hexdigest()
    readme = (
        "real93 Qwen-Image-2.1 LoRA dataset. The YOLO labels are provenance and are NOT used by DiffSynth.\n"
        + ("Captions were supplied as reviewed; verify again before launch.\n" if reviewed else
           "DRAFT ONLY: captions have not been approved. No metadata.csv is included.\n")
    )
    target = out / ("real93_REVIEWED.tar" if reviewed else "real93_DRAFT.tar")
    with tarfile.open(target, "w") as archive:
        for index in range(1, 94):
            stem = f"real_photo_{index}"
            archive.add(images[stem], arcname=f"real93/images/{stem}.png", recursive=False)
            archive.add(labels[stem], arcname=f"real93/yolo_labels/{stem}.txt", recursive=False)
            archive.add(captions[stem], arcname=f"real93/captions/{stem}.txt", recursive=False)
        add_bytes(archive, f"real93/{metadata_name}", csv_text.getvalue().encode("utf-8"))
        add_bytes(archive, "real93/README.txt", readme.encode("utf-8"))
        add_bytes(archive, "real93/MANIFEST.json", json.dumps(manifest, indent=2).encode("utf-8"))

    framework_tar, revision = framework_archive(out)
    receipt = {
        "dataset_archive": str(target),
        "dataset_sha256": digest(target),
        "dataset_bytes": target.stat().st_size,
        "framework_archive": str(framework_tar),
        "framework_sha256": digest(framework_tar),
        "framework_revision": revision,
        "trainable": reviewed,
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
