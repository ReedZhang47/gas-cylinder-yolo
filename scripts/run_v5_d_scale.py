"""D493 scale pipeline. Default checks/prints only; --execute is an explicit gate."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys

import run_v5_d as training
from prepare_v5_d_scale import ROOT, OUT, ARM, RUNS, WEIGHTS, check, read, require, sha, write_json

LOGS = ROOT / "logs/v5_d_scale"


def train_args(weight):
    return read(OUT / "training_args.json")[weight]


def configure_training():
    # Reuse the accepted worker unchanged, with isolated dataset/provenance/output globals.
    training.OUT, training.ARM, training.RUNS, training.LOGS = OUT, ARM, RUNS, LOGS
    training.train_args = train_args


def plan(args):
    return {"execute": args.execute, "stage": args.stage, "detectors": args.only or WEIGHTS,
            "sampling": "one simple random draw: seed 42; 493/1085; no stratification or redraw",
            "training": {w: {k: train_args(w)[k] for k in (
                "epochs", "imgsz", "batch", "seed", "patience", "save_period", "close_mosaic", "data", "project", "name")}
                         for w in (args.only or WEIGHTS)},
            "evaluation": "frozen dev61 five folds; fixed endpoint + pooled OOF + deployment; 180 snapshots",
            "bootstrap": "D1085 minus D493; joint + six fixed + six OOF; 10000 paired image draws, seed 0",
            "run_root": str(RUNS), "result_root": str(OUT)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--stage", choices=["all", "train", "eval", "bootstrap"], default="all")
    parser.add_argument("--only", choices=WEIGHTS, nargs="+")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--worker", choices=WEIGHTS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    require(not args.only or args.stage == "train", "--only requires --stage train")
    require(not args.resume or args.stage in ("all", "train"), "--resume applies to training only")
    require(not args.worker or args.execute, "Worker requires --execute")
    check()
    configure_training()
    if args.worker:
        training.worker(args.worker, args.resume)
        return
    proposal = plan(args)
    print(json.dumps(proposal, ensure_ascii=False, indent=2), flush=True)
    if not args.execute:
        print("PLAN ONLY. No training, inference or bootstrap started.")
        return
    lock = OUT / "pipeline.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(f"pid={os.getpid()} start={datetime.now().astimezone().isoformat()}\n")
    record = read(OUT / "execution.json")
    record.update(status="running", stage=args.stage, started_at=record.get("started_at") or datetime.now().astimezone().isoformat(),
                  last_launch_at=datetime.now().astimezone().isoformat(), input_manifest_sha256=sha(OUT / "input_manifest.json"))
    try:
        write_json(OUT / "execution.json", record)
        if args.stage in ("all", "train"):
            todo = [w for w in (args.only or WEIGHTS) if not training.is_complete(w)]
            require(not todo or shutil.disk_usage(ROOT).free >= 40 * 2**30, "Need at least 40 GiB free before training")
            for w in todo:
                require(not (RUNS / w).exists() or args.resume, f"Incomplete {w}; inspect before explicit --resume")
            for w in todo:
                cmd = [sys.executable, str(Path(__file__).resolve()), "--execute", "--worker", w]
                if args.resume and (RUNS / w).exists():
                    cmd.append("--resume")
                training.run_logged(cmd, f"train_{w}")
        for stage in ("eval", "bootstrap"):
            if args.stage in ("all", stage):
                record["current_stage"] = stage
                write_json(OUT / "execution.json", record)
                training.run_logged([sys.executable, str(ROOT / "scripts/eval_v5_d_scale.py"),
                                     "--execute", "--stage", stage], stage)
        record.update(status="completed" if args.stage == "all" else "stage_completed",
                      last_finished_stage=args.stage, finished_at=datetime.now().astimezone().isoformat())
        record.pop("error", None)
        write_json(OUT / "execution.json", record)
    except BaseException as exc:
        record.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                      error=str(exc), stopped_at=datetime.now().astimezone().isoformat())
        write_json(OUT / "execution.json", record)
        raise
    finally:
        lock.unlink()


if __name__ == "__main__":
    main()
