"""Queue the 51 existing LoRA comparison graphs with seeds 88888 and 77777.

Uses PNG API graphs unchanged except KSampler seed and SaveImage filename_prefix.
Records submission IDs; does not inspect generated images or Comfy Desktop logs.
ComfyUI itself processes the full queue after this script exits.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
import uuid

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (88888, 77777)
GROUPS = {1: "new150_010", 2: "new24_001", 3: "new24_010"}
STEPS = (500, 1000, 1500, 1860)
STRENGTHS = ("0.2", "0.5", "0.8", "1.0")


def jobs(source):
    result = []
    # Base first, then group each LoRA checkpoint together to limit model switching.
    configurations = ["no-lora"] + [f"{step}-{s}" for step in STEPS for s in STRENGTHS]
    for config in configurations:
        for group, label in GROUPS.items():
            path = source / f"{config}_{group:05d}_.png"
            with Image.open(path) as image:
                graph = json.loads(image.info["prompt"])
            samplers = [n for n in graph.values() if n["class_type"] == "KSampler"]
            saves = [n for n in graph.values() if n["class_type"] == "SaveImage"]
            if len(samplers) != 1 or len(saves) != 1:
                raise RuntimeError(f"Expected one KSampler and one SaveImage: {path}")
            for seed in SEEDS:
                changed = deepcopy(graph)
                prefix = f"lora-compare/{config}_{label}_seed{seed}"
                for node in changed.values():
                    if node["class_type"] == "KSampler":
                        node["inputs"]["seed"] = seed
                    elif node["class_type"] == "SaveImage":
                        node["inputs"]["filename_prefix"] = prefix
                digest = hashlib.sha256(json.dumps(changed, sort_keys=True).encode()).hexdigest()
                result.append({"id": prefix, "source": str(path), "seed": seed,
                               "filename_prefix": prefix, "graph_sha256": digest, "graph": changed})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(r"D:\gas_cylinders\lora-compare"))
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--manifest", type=Path, default=ROOT / "logs/lora_compare_seeds/submissions.jsonl")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    planned = jobs(args.source)
    if len(planned) != 102 or len({j["id"] for j in planned}) != 102:
        raise RuntimeError("Expected exactly 102 distinct jobs")
    print(f"Jobs: {len(planned)}; seeds: {SEEDS}; server: {args.server}", flush=True)
    print("Output: ComfyUI default output directory / lora-compare", flush=True)
    if not args.execute:
        print("PLAN ONLY. Add --execute to submit all graphs.")
        return
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    known = {}
    if args.manifest.exists():
        for line in args.manifest.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            known[record["id"]] = record
    client_id = str(uuid.uuid4())
    submitted = 0
    with args.manifest.open("a", encoding="utf-8") as stream:
        for index, job in enumerate(planned, 1):
            if job["id"] in known:
                if known[job["id"]]["graph_sha256"] != job["graph_sha256"]:
                    raise RuntimeError(f"Previously submitted graph changed: {job['id']}")
                print(f"{index}/102 already submitted: {job['id']}", flush=True)
                continue
            payload = json.dumps({"prompt": job["graph"], "client_id": client_id}).encode()
            request = urllib.request.Request(args.server.rstrip("/") + "/prompt", data=payload,
                                             headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    accepted = json.load(response)
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f"ComfyUI rejected {job['id']}: {exc.read().decode('utf-8', errors='replace')}") from exc
            if not accepted.get("prompt_id") or accepted.get("node_errors"):
                raise RuntimeError(f"Invalid submission response for {job['id']}: {accepted}")
            record = {k: v for k, v in job.items() if k != "graph"}
            record.update(submitted_at=datetime.now().astimezone().isoformat(),
                          prompt_id=accepted["prompt_id"], queue_number=accepted.get("number"), server=args.server)
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            submitted += 1
            print(f"{index}/102 queued: {job['id']} [{accepted['prompt_id']}]", flush=True)
    print(f"DONE: {submitted} newly submitted; {len(planned)} jobs recorded. ComfyUI processes them automatically.", flush=True)


if __name__ == "__main__":
    main()
