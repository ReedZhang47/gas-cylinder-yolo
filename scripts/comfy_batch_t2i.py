"""Sequential, resumable ComfyUI text-to-image pilot for v5 Arm D.

Default mode is a dry run. --run is blocked unless the LoRA and model tensor
dimensions match. The script never decides whether an image should be kept or
what its YOLO box should be; those are separate human review steps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = REPO / "docs/v5_prompts/trial_workflow_api.json"
DEFAULT_PROMPTS = REPO / "docs/v5_prompts/new150_prompts.jsonl"
DEFAULT_MODEL = Path(
    r"D:\Comfy-Desktop\ComfyUI-Shared\models\diffusion_models"
    r"\qwen_image_2.1_int8_convrot.safetensors"
)
DEFAULT_LORA = Path(
    r"E:\Comfy-Desktop\ComfyUI-Shared\models\loras"
    r"\construction_sites_gas_cylinders.safetensors"
)
DEFAULT_OUTPUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")
DEFAULT_LOG = Path(
    r"E:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\user\comfyui.log"
)


def safetensors_header(path: Path) -> dict:
    with path.open("rb") as handle:
        size = struct.unpack("<Q", handle.read(8))[0]
        if size > 64 * 1024 * 1024:
            raise ValueError(f"Implausible safetensors header: {path}")
        return json.loads(handle.read(size))


def check_weights(model_path: Path, lora_path: Path) -> tuple[bool, str]:
    model = safetensors_header(model_path)
    lora = safetensors_header(lora_path)
    w = model["transformer_blocks.0.attn.to_q.weight"]["shape"]
    a = lora["transformer.transformer_blocks.0.attn.to_q.lora_A.weight"]["shape"]
    b = lora["transformer.transformer_blocks.0.attn.to_q.lora_B.weight"]["shape"]
    compatible = a[1] == w[1] and b[0] == w[0] and a[0] == b[1]
    detail = f"model to_q={w}; LoRA A={a}, B={b}; compatible={compatible}"
    return compatible, detail


def one_node(graph: dict, class_type: str) -> str:
    ids = [key for key, node in graph.items() if node.get("class_type") == class_type]
    if len(ids) != 1:
        raise ValueError(f"Expected one {class_type} node, found {ids}")
    return ids[0]


def validate_workflow(graph: dict, model_path: Path, lora_path: Path) -> dict:
    ids = {
        "text": one_node(graph, "TextEncodeQwenImage21"),
        "sampler": one_node(graph, "KSampler"),
        "save": one_node(graph, "SaveImage"),
        "model": one_node(graph, "UNETLoader"),
        "lora": one_node(graph, "LoraLoaderModelOnly"),
    }
    if graph[ids["model"]]["inputs"]["unet_name"] != model_path.name:
        raise ValueError("Workflow model filename differs from --model-path")
    if graph[ids["lora"]]["inputs"]["lora_name"] != lora_path.name:
        raise ValueError("Workflow LoRA filename differs from --lora-path")
    text_inputs = graph[ids["text"]]["inputs"]
    if any(key.startswith("images.") for key in text_inputs):
        raise ValueError("Workflow contains reference images; this is not text-to-image")
    return ids


def load_prompts(path: Path) -> list[dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records or len({r["id"] for r in records}) != len(records):
        raise ValueError("Prompt file is empty or contains duplicate IDs")
    for record in records:
        if record.get("review_status") != "approved":
            raise ValueError(
                f"{record['id']} is not approved. Review the image-specific prompt "
                "and change review_status to approved before queueing."
            )
        if not record.get("prompt"):
            raise ValueError(f"Empty prompt: {record['id']}")
    return records


def deterministic_seed(base: int, prompt_id: str, variant: int) -> int:
    digest = hashlib.sha256(f"{base}:{prompt_id}:{variant}".encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big") % (2**63 - 1)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def http_json(url: str, data: dict | None = None) -> dict:
    body = None if data is None else json.dumps(data).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ComfyUI request failed: {url}: {exc}") from exc


def make_graph(template: dict, ids: dict, prompt: str, seed: int, prefix: str) -> dict:
    graph = json.loads(json.dumps(template))
    graph[ids["text"]]["inputs"]["prompt"] = prompt
    graph[ids["sampler"]]["inputs"]["seed"] = seed
    graph[ids["save"]]["inputs"]["filename_prefix"] = prefix
    return graph


def wait_history(server: str, prompt_id: str, timeout: int) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = http_json(f"{server}/history/{prompt_id}")
        if prompt_id in result:
            entry = result[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(f"ComfyUI execution failed: {status}")
            return entry
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for prompt_id={prompt_id}")


def log_offset(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def check_new_log(path: Path, offset: int) -> None:
    if not path.exists():
        raise RuntimeError(f"ComfyUI log unavailable: {path}")
    with path.open("rb") as handle:
        if path.stat().st_size >= offset:
            handle.seek(offset)
        recent = handle.read().decode("utf-8", errors="replace")
    bad = [line for line in recent.splitlines() if "lora key not loaded" in line or "ERROR lora" in line]
    if bad:
        raise RuntimeError(f"LoRA runtime errors ({len(bad)}); first: {bad[0]}")


def completed_keys(manifest: Path) -> set[tuple[str, int]]:
    if not manifest.exists():
        return set()
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {(row["id"], row["variant"]) for row in rows if row.get("status") == "completed"}


def output_records(entry: dict, save_node: str, output_root: Path) -> list[dict]:
    images = entry.get("outputs", {}).get(save_node, {}).get("images", [])
    if len(images) != 1:
        raise RuntimeError(f"Expected one saved image, found {len(images)}")
    result = []
    root = output_root.resolve()
    for image in images:
        if image.get("type") != "output":
            raise RuntimeError(f"Unexpected ComfyUI image type: {image}")
        path = (root / image.get("subfolder", "") / image["filename"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise RuntimeError(f"Output path missing or outside output root: {path}")
        result.append({
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--lora-path", type=Path, default=DEFAULT_LORA)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--comfy-log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--variants", type=int, default=5)
    parser.add_argument("--seed-base", type=int, default=20260926)
    parser.add_argument("--limit", type=int, default=0, help="Limit total new images; 0 means all")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--manifest", type=Path, default=REPO / "docs/v5_prompts/batch_manifest.jsonl")
    parser.add_argument("--run", action="store_true", help="Actually queue; default is preflight only")
    args = parser.parse_args()
    if args.variants < 1 or args.limit < 0:
        parser.error("--variants must be positive and --limit nonnegative")

    template = json.loads(args.workflow.read_text(encoding="utf-8"))
    ids = validate_workflow(template, args.model_path, args.lora_path)
    compatible, detail = check_weights(args.model_path, args.lora_path)
    print(detail)
    print("Workflow nodes:", ids)
    print("Sampler:", template[ids["sampler"]]["inputs"])
    if not compatible:
        print("BLOCKED: LoRA and base model have incompatible dimensions.", file=sys.stderr)
        return 2

    prompts = load_prompts(args.prompts)
    done = completed_keys(args.manifest)
    planned = [(r, v) for r in prompts for v in range(1, args.variants + 1) if (r["id"], v) not in done]
    if args.limit:
        planned = planned[: args.limit]
    print(f"Approved prompts: {len(prompts)}; already complete: {len(done)}; to queue: {len(planned)}")
    if not args.run:
        if planned:
            r, v = planned[0]
            print("First:", r["id"], "variant", v, "seed", deterministic_seed(args.seed_base, r["id"], v))
        print("Dry run only. Add --run after preflight passes and ComfyUI is running.")
        return 0

    http_json(f"{args.server.rstrip('/')}/system_stats")
    workflow_hash = hashlib.sha256(args.workflow.read_bytes()).hexdigest()
    model_hash = sha256_file(args.model_path)
    lora_hash = sha256_file(args.lora_path)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    server = args.server.rstrip("/")
    for index, (record, variant) in enumerate(planned, 1):
        seed = deterministic_seed(args.seed_base, record["id"], variant)
        prefix = f"v5_{record['id']}_v{variant:02d}_s{seed}"
        graph = make_graph(template, ids, record["prompt"], seed, prefix)
        offset = log_offset(args.comfy_log)
        queued = http_json(f"{server}/prompt", {"prompt": graph})
        prompt_id = queued["prompt_id"]
        entry = wait_history(server, prompt_id, args.timeout)
        check_new_log(args.comfy_log, offset)
        outputs = output_records(entry, ids["save"], args.output_root)
        row = {
            "status": "completed",
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "id": record["id"],
            "set": record["set"],
            "source_photo": record.get("source_photo"),
            "group": record.get("group"),
            "intended_cylinder_count": record["intended_cylinder_count"],
            "placement": record["placement"],
            "variant": variant,
            "seed": seed,
            "prompt": record["prompt"],
            "prompt_id": prompt_id,
            "workflow_sha256": workflow_hash,
            "model": args.model_path.name,
            "model_sha256": model_hash,
            "lora": args.lora_path.name,
            "lora_sha256": lora_hash,
            "lora_strength": template[ids["lora"]]["inputs"]["strength_model"],
            "sampler": {
                key: template[ids["sampler"]]["inputs"][key]
                for key in ("steps", "cfg", "sampler_name", "scheduler", "denoise")
            },
            "outputs": outputs,
        }
        with args.manifest.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{index}/{len(planned)} {record['id']} v{variant:02d} -> {outputs[0]['path']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
