"""D detector pipeline. Default is a plan only; --execute is required to run."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml

from prepare_v5_d import ROOT, OUT, ARM, WEIGHTS, check, require, sha, write_json

RUNS = ROOT / "runs/detect" / ARM
LOGS = ROOT / "logs/v5_d"


def train_args(weight):
    # Freeze the actual C-arm settings, including optimizer and augmentation defaults.
    args = yaml.safe_load((ROOT / "runs/detect/gen1085v4" / weight / "args.yaml").read_text(encoding="utf-8"))
    args.pop("save_dir", None)
    args.update(model=str(ROOT / "weights" / f"{weight}.pt"), data=str(OUT / "data_D1085.yaml"),
                project=str(RUNS), name=weight, exist_ok=True, resume=False,
                epochs=300, patience=0, save_period=10, imgsz=640, batch=16,
                device="0", seed=0, deterministic=True, close_mosaic=10)
    return args


def checkpoint_paths(weight):
    folder = RUNS / weight / "weights"
    return [folder / f"epoch{e}.pt" for e in range(10, 300, 10)] + [folder / "last.pt"]


def validate_finished(weight):
    folder = RUNS / weight
    with (folder / "results.csv").open(encoding="utf-8-sig") as stream:
        rows = [{k.strip(): v.strip() for k, v in r.items()} for r in csv.DictReader(stream)]
    require(len(rows) == 300 and [int(r["epoch"]) for r in rows] == list(range(1, 301)), f"{weight}: expected all 300 epochs")
    for path in checkpoint_paths(weight):
        require(path.is_file() and path.stat().st_size > 1000000, f"Missing/incomplete snapshot: {path}")


def is_complete(weight):
    path = RUNS / weight / "completed.json"
    if not path.exists():
        return False
    record = json.loads(path.read_text(encoding="utf-8"))
    require(record["input_manifest_sha256"] == sha(OUT / "input_manifest.json"), f"{weight}: completion input differs")
    validate_finished(weight)
    for file, digest in record["files"].items():
        require(sha(file) == digest, f"Completed artifact changed: {file}")
    return True


def record_batch(trainer, events, event_file):
    batch = int(trainer.batch_size)
    require(batch in (16, 8), f"Protocol allows only batch 16 or 8; trainer reduced to {batch}; stopping")
    if not events or events[-1]["batch"] != batch:
        events.append({"at": datetime.now().astimezone().isoformat(),
                       "epoch_internal": getattr(trainer, "epoch", trainer.start_epoch),
                       "batch": batch, "note": "Ultralytics first-epoch OOM fallback" if batch == 8 else "configured"})
        write_json(event_file, events)


def worker(weight, resume):
    from ultralytics import YOLO

    folder = RUNS / weight
    stamp = folder / "started.json"
    manifest_hash = sha(OUT / "input_manifest.json")
    if resume:
        require(stamp.exists(), f"No run provenance to resume: {stamp}")
        started = json.loads(stamp.read_text(encoding="utf-8"))
        require(started["input_manifest_sha256"] == manifest_hash, "Cannot resume with changed inputs")
        last = folder / "weights/last.pt"
        require(last.exists(), f"No resumable last.pt: {last}")
        import torch
        checkpoint = torch.load(last, map_location="cpu", weights_only=False)
        require(checkpoint.get("epoch", -1) >= 0 and checkpoint.get("optimizer") is not None,
                "last.pt has been finalized/stripped; inspect this run before retrying")
        del checkpoint
    else:
        require(not folder.exists(), f"Incomplete run exists: {folder}; inspect, then use --resume if appropriate")
        folder.mkdir(parents=True)
        write_json(stamp, {"started_at": datetime.now().astimezone().isoformat(),
                           "input_manifest_sha256": manifest_hash, "args": train_args(weight)})
    events = []
    event_file = folder / "batch_events.json"
    if event_file.exists():
        events = json.loads(event_file.read_text(encoding="utf-8"))

    def batch_guard(trainer):
        record_batch(trainer, events, event_file)

    model = YOLO(str(last) if resume else str(ROOT / "weights" / f"{weight}.pt"))
    model.add_callback("on_train_start", batch_guard)
    model.add_callback("on_train_batch_start", batch_guard)
    model.add_callback("on_train_batch_end", batch_guard)
    if resume:
        model.train(resume=True)
    else:
        model.train(**train_args(weight))
    validate_finished(weight)
    files = checkpoint_paths(weight) + [folder / "args.yaml", folder / "results.csv", event_file]
    write_json(folder / "completed.json", {"finished_at": datetime.now().astimezone().isoformat(),
               "input_manifest_sha256": manifest_hash, "batch_events": events,
               "files": {p.as_posix(): sha(p) for p in files}})


def run_logged(command, name):
    LOGS.mkdir(parents=True, exist_ok=True)
    path = LOGS / f"{datetime.now():%Y%m%d_%H%M%S}_{name}.log"
    print(f"START {name}; log: {path}", flush=True)
    with path.open("w", encoding="utf-8") as log:
        log.write(subprocess.list2cmdline(command) + "\n")
        log.flush()
        proc = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    require(proc.returncode == 0, f"{name} failed (exit {proc.returncode}); see {path}")
    print(f"DONE {name}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--stage", choices=["all", "train", "eval", "bootstrap"], default="all")
    parser.add_argument("--only", choices=WEIGHTS, nargs="+")
    parser.add_argument("--resume", action="store_true", help="Explicitly resume incomplete runs with a usable last.pt")
    parser.add_argument("--worker", choices=WEIGHTS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    require(not args.only or args.stage == "train", "--only is allowed only with --stage train")
    require(not args.resume or args.stage in ("all", "train"), "--resume applies to training only")
    if args.worker:
        require(args.execute, "Worker requires --execute")
        worker(args.worker, args.resume)
        return
    check()
    weights = args.only or WEIGHTS
    plan = {"execute": args.execute, "stage": args.stage, "detectors": weights,
            "training": {w: {k: train_args(w)[k] for k in ("epochs", "imgsz", "batch", "seed", "save_period", "data", "project", "name")}
                         for w in weights},
            "evaluation": "frozen dev61 five folds; fixed endpoint + pooled OOF + deployment; 30 snapshots/detector",
            "bootstrap": "D-A, D-B, D-C; joint + six fixed + six OOF; 10000 paired image draws, seed 0",
            "run_root": str(RUNS), "result_root": str(OUT)}
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if not args.execute:
        print("PLAN ONLY. No training, inference or bootstrap started.")
        return
    # Exclusive lock prevents two launchers from sharing a run/cache directory.
    lock = OUT / "pipeline.lock"
    with lock.open("x", encoding="utf-8") as stream:
        import os
        stream.write(f"pid={os.getpid()} start={datetime.now().astimezone().isoformat()}\n")
    try:
        if args.stage in ("all", "train"):
            todo = [w for w in weights if not is_complete(w)]
            # Observed v4 C snapshots total ~22.4 GiB; allow 40 GiB for a fresh D run.
            require(not todo or shutil.disk_usage(ROOT).free >= 40 * 2**30, "Need at least 40 GiB free before training")
            for w in todo:
                require(not (RUNS / w).exists() or args.resume, f"Incomplete {w}; inspect before explicit --resume")
            for w in todo:
                cmd = [sys.executable, str(Path(__file__).resolve()), "--execute", "--worker", w]
                if args.resume and (RUNS / w).exists():
                    cmd.append("--resume")
                run_logged(cmd, f"train_{w}")
        if args.stage in ("all", "eval"):
            run_logged([sys.executable, str(ROOT / "scripts/eval_v5_d.py"), "--execute", "--stage", "eval"], "eval")
        if args.stage in ("all", "bootstrap"):
            run_logged([sys.executable, str(ROOT / "scripts/eval_v5_d.py"), "--execute", "--stage", "bootstrap"], "bootstrap")
    finally:
        lock.unlink()


if __name__ == "__main__":
    main()
