"""Run the authorized v5 candidate budget sequentially in a background process."""

from __future__ import annotations

import argparse
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_state(path: Path, state: dict) -> None:
    state["updated_utc"] = timestamp()
    temporary = path.with_suffix(".writing")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def count_completed(path: Path) -> int:
    if not path.exists():
        return 0
    return len({(r["id"], r["variant"]) for r in (
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ) if r.get("status") == "completed"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    state_path = Path(config["state_file"])
    state_path.parent.mkdir(parents=True, exist_ok=True)
    # The OS releases this lock if the runner exits or is interrupted.
    with state_path.with_suffix(".lock").open("a+b") as lock:
        if lock.seek(0, 2) == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            print("This batch already has a running controller.", flush=True)
            return 2
        state = {
            "status": "running", "pid": os.getpid(), "started_utc": timestamp(),
            "expected_total": sum(b["expected"] for b in config["batches"]),
            "batches": [{"set": b["set"], "expected": b["expected"],
                         "completed": count_completed(Path(b["manifest"]))} for b in config["batches"]],
            "stop_file": config["stop_file"], "output_prefix": config["output_prefix"],
        }
        save_state(state_path, state)
        try:
            for index, batch in enumerate(config["batches"]):
                if Path(config["stop_file"]).exists():
                    state["status"] = "stopped"
                    save_state(state_path, state)
                    return 0
                state["active_set"] = batch["set"]
                save_state(state_path, state)
                command = [sys.executable, "-u", str(REPO / "scripts/comfy_batch_t2i.py"),
                           "--server", config["server"], "--workflow", config["workflow"],
                           "--prompts", batch["prompts"], "--variants", str(batch["variants"]),
                           "--seed-mode", "random", "--filename-prefix", config["output_prefix"] + "/" + batch["set"],
                           "--manifest", batch["manifest"], "--stop-file", config["stop_file"], "--run"]
                print(f"Starting {batch['set']}: target {batch['expected']} images", flush=True)
                with subprocess.Popen(command, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, encoding="utf-8", errors="replace") as child:
                    state["child_pid"] = child.pid
                    save_state(state_path, state)
                    for line in child.stdout:
                        print(line, end="", flush=True)
                        if " -> " in line:
                            state["batches"][index]["completed"] = count_completed(Path(batch["manifest"]))
                            save_state(state_path, state)
                    return_code = child.wait()
                state["batches"][index]["completed"] = count_completed(Path(batch["manifest"]))
                if return_code:
                    state.update(status="failed", exit_code=return_code)
                    save_state(state_path, state)
                    return return_code
                if state["batches"][index]["completed"] != batch["expected"]:
                    state["status"] = "stopped" if Path(config["stop_file"]).exists() else "incomplete"
                    save_state(state_path, state)
                    return 0 if state["status"] == "stopped" else 1
            state.update(status="completed", finished_utc=timestamp())
            state.pop("child_pid", None)
            save_state(state_path, state)
            print("All authorized candidate images completed.", flush=True)
            return 0
        except Exception as exc:
            state.update(status="failed", error=str(exc))
            save_state(state_path, state)
            raise


if __name__ == "__main__":
    raise SystemExit(main())
