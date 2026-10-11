"""Freeze a simple random 493-image subset of the accepted D1085 pool; no training."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import random
import shutil

import yaml

import prepare_v5_d as parent
from prepare_v5_d import ROOT, WEIGHTS, require, sha, write_json

OUT = ROOT / "experiments/v5_d_scale"
ARM = "D493v5"
RUNS = ROOT / "runs/detect" / ARM
SEED = 42
SIZE = 493


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sample_records(records):
    """One equal-probability draw without replacement; labels never enter the draw."""
    population = sorted(records, key=lambda r: Path(r["image"]).name)
    require(len(population) == 1085 and len({r["image"] for r in population}) == 1085,
            "Expected 1085 unique parent images")
    return random.Random(SEED).sample(population, SIZE)


def config_text():
    listing = (OUT / "D493_train.txt").as_posix()
    return ("# Frozen random D493 subset; val=train is diagnostic only.\n"
            f"path: {parent.DATA.as_posix()}\ntrain: {listing}\nval: {listing}\n"
            "nc: 1\nnames:\n  0: Placement Issues\n")


def aligned_args(weight):
    c = yaml.safe_load((ROOT / "runs/detect/gen493v4" / weight / "args.yaml").read_text(encoding="utf-8"))
    d = yaml.safe_load((parent.ROOT / "runs/detect" / parent.ARM / weight / "args.yaml").read_text(encoding="utf-8"))
    # Only dataset/output locations differ. Fail rather than silently change training settings.
    excluded = {"data", "project", "name", "save_dir"}
    require({k: v for k, v in c.items() if k not in excluded} ==
            {k: v for k, v in d.items() if k not in excluded}, f"C493/D1085 training settings differ: {weight}")
    c.pop("save_dir", None)
    c.update(model=str(ROOT / "weights" / f"{weight}.pt"), data=str(OUT / "data_D493.yaml"),
             project=str(RUNS), name=weight, exist_ok=True, resume=False)
    require(tuple(c[k] for k in ("epochs", "imgsz", "batch", "seed", "patience", "save_period", "close_mosaic")) ==
            (300, 640, 16, 0, 0, 10, 10), f"Unexpected training protocol: {weight}")
    return c


def source_files():
    return [ROOT / "scripts" / name for name in (
        "prepare_v5_d_scale.py", "run_v5_d_scale.py", "eval_v5_d_scale.py",
        "prepare_v5_d.py", "run_v5_d.py", "eval_v5_d.py", "eval_v4_protocol.py", "bootstrap_paired.py")]


def freeze():
    require(not (OUT / "input_manifest.json").exists(), "Already frozen; use --check, never redraw")
    require(not RUNS.exists(), "D493 run already exists; cannot freeze new inputs")
    full = parent.check()
    require(read(parent.OUT / "acceptance.json")["status"] == "passed_with_notes", "D1085 acceptance missing")
    draws = sample_records(full["images"])
    records = sorted(draws, key=lambda r: Path(r["image"]).name)
    configs = {w: aligned_args(w) for w in WEIGHTS}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "D493_train.txt").write_text("\n".join(r["image"] for r in records) + "\n", encoding="utf-8")
    (OUT / "data_D493.yaml").write_text(config_text(), encoding="utf-8")
    write_json(OUT / "training_args.json", configs)
    audit = {"images": SIZE, "labels": SIZE, "positive": sum(r["boxes"] > 0 for r in records),
             "empty": sum(r["boxes"] == 0 for r in records), "boxes": sum(r["boxes"] for r in records),
             "sources": dict(Counter(r["source_set"] for r in records)),
             "unique_image_hashes": len({r["image_sha256"] for r in records}),
             "composition_role": "observed after the single random draw; no quotas, filtering or redraw",
             "parent_audit": (parent.OUT / "data_audit.json").as_posix()}
    write_json(OUT / "data_audit.json", audit)
    controls = [parent.OUT / "input_manifest.json", parent.OUT / "acceptance.json",
                parent.OUT / f"v5_protocol_{parent.ARM}.json",
                parent.OUT / "per_image" / f"per_image_{parent.ARM}.json",
                OUT / "D493_train.txt", OUT / "data_D493.yaml", OUT / "training_args.json", OUT / "data_audit.json",
                parent.V4 / "v4_protocol_gen493v4.json", parent.V4 / "per_image/per_image_gen493v4.json",
                ROOT / "scripts/splits_gen1085/gen493_full_train.txt",
                ROOT / "scripts/splits_gen1085/data_gen493_full_v4.yaml"]
    for w in WEIGHTS:
        controls += [ROOT / "runs/detect/gen493v4" / w / "args.yaml",
                     ROOT / "runs/detect" / parent.ARM / w / "args.yaml"]
    manifest = {"created_at": datetime.now().astimezone().isoformat(), "arm": ARM,
                "status": "prepared; awaiting user continue; training and inference not started",
                "parent_arm": parent.ARM, "parent_manifest_sha256": sha(parent.OUT / "input_manifest.json"),
                "environment": full["environment"], "sampling": {
                    "method": "simple random sample without replacement", "algorithm": "Python random.Random(seed).sample",
                    "population_order": "ascending image filename", "seed": SEED, "population_size": 1085,
                    "sample_size": SIZE, "draw_order": [Path(r["image"]).name for r in draws],
                    "stratified": False, "repeated_draws": False,
                    "C493_difference": "C493 is the earlier generated batch, not a simple random sample"},
                "images": records, "dev61": full["dev61"], "folds": full["folds"], "audit": audit,
                "files": {p.as_posix(): sha(p) for p in controls},
                "scripts": {p.as_posix(): sha(p) for p in source_files()},
                "statistics": {"pair": [ARM, parent.ARM], "delta": "D1085 minus D493",
                               "targets": "joint + six fixed endpoint + six OOF", "n_boot": 10000, "seed": 0,
                               "primary_metric": "mAP50-95", "status": "v5 extension decided after D1085 results"}}
    write_json(OUT / "input_manifest.json", manifest)
    write_json(OUT / "execution.json", {"status": "prepared_awaiting_continue", "prepared_at": manifest["created_at"],
                                        "started_at": None, "finished_at": None})
    print(json.dumps(audit, ensure_ascii=False, indent=2))


def check():
    require((OUT / "input_manifest.json").exists(), "Missing D493 freeze; use --freeze first")
    full = parent.check()  # validates all parent data, dev61, controls, code and environment
    manifest = read(OUT / "input_manifest.json")
    require(manifest["arm"] == ARM and manifest["environment"] == full["environment"], "Arm/environment changed")
    require(sha(parent.OUT / "input_manifest.json") == manifest["parent_manifest_sha256"], "Parent freeze changed")
    expected = sorted(sample_records(full["images"]), key=lambda r: Path(r["image"]).name)
    require(manifest["images"] == expected and len(expected) == SIZE, "D493 differs from the one frozen random draw")
    require(manifest["sampling"]["draw_order"] == [Path(r["image"]).name for r in sample_records(full["images"])],
            "Draw order changed")
    require(manifest["folds"] == full["folds"] and manifest["dev61"] == full["dev61"], "dev61/folds changed")
    for file, digest in {**manifest["files"], **manifest["scripts"]}.items():
        require(sha(file) == digest, f"Frozen scale input/code changed: {file}")
    cfg = yaml.safe_load((OUT / "data_D493.yaml").read_text(encoding="utf-8"))
    require(cfg["train"] == cfg["val"] and "test" not in cfg, "Training must not read dev61")
    require(read(OUT / "training_args.json") == {w: aligned_args(w) for w in WEIGHTS}, "Training args drift")
    require(not (parent.OUT / "pipeline.lock").exists(), "D1085 pipeline still running")
    print(f"Frozen D493 OK: seed {SEED}, {SIZE}/1085; free disk {shutil.disk_usage(ROOT).free / 2**30:.1f} GiB", flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    freeze() if args.freeze else check()


if __name__ == "__main__":
    main()
