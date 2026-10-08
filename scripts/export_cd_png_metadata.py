"""Read PNG execution graphs, audit D source mapping, prepare lossless exports.

This script only reads external image directories. Final CSV authoring is separate.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re

from PIL import Image


def natural_key(path):
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", str(path))]


def read_record(path: Path) -> dict:
    with Image.open(path) as image:
        graph = json.loads(image.info["prompt"])
        size = list(image.size)
        gui = image.info.get("workflow")

    def ancestors(node_ids):
        found = set()
        stack = list(node_ids)
        while stack:
            nid = str(stack.pop())
            if nid in found:
                continue
            found.add(nid)
            for value in graph[nid].get("inputs", {}).values():
                if isinstance(value, list) and len(value) == 2 and str(value[0]) in graph:
                    stack.append(str(value[0]))
        return found

    saves = [nid for nid, n in graph.items() if n["class_type"].startswith("SaveImage")]
    active = ancestors(saves)
    samplers = [nid for nid in active if graph[nid]["class_type"] in ("KSampler", "KSamplerAdvanced")]
    if len(samplers) != 1:
        raise ValueError(f"{path}: expected one active sampler, got {samplers}")
    sampler_id = samplers[0]
    sampler = graph[sampler_id]["inputs"]

    def scalar(value):
        if not isinstance(value, list):
            return value
        upstream = graph[str(value[0])]["inputs"]
        if graph[str(value[0])]["class_type"] == "ComfySwitchNode":
            enabled = scalar(upstream["switch"])
            return scalar(upstream["on_true" if enabled else "on_false"])
        values = [upstream[k] for k in ("value", "seed", "noise_seed", "steps", "cfg", "boolean", "int", "float") if k in upstream]
        if len(values) != 1:
            raise ValueError(f"{path}: ambiguous linked scalar: {value}")
        return scalar(values[0])

    seed = scalar(sampler.get("seed", sampler.get("noise_seed")))
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError(f"{path}: invalid seed {seed!r}")
    positive_ids = ancestors([sampler["positive"][0]])
    text_nodes = []
    for nid in sorted(positive_ids, key=natural_key):
        node = graph[nid]
        if "TextEncode" in node["class_type"]:
            inp = node["inputs"]
            text = inp.get("prompt", inp.get("text"))
            if isinstance(text, str) and text:
                text_nodes.append((nid, text))
    if len(text_nodes) != 1:
        raise ValueError(f"{path}: expected one active positive text, got {len(text_nodes)}")
    model_ids = ancestors([sampler["model"][0]])
    loras = []
    for nid in sorted(model_ids, key=natural_key):
        node = graph[nid]
        if "LoraLoader" in node["class_type"]:
            inp = node["inputs"]
            loras.append({"name": inp.get("lora_name"), "strength": scalar(inp.get("strength_model", 0))})
    return {
        "path": str(path), "image_name": path.name, "seed": str(seed),
        "prompt": text_nodes[0][1], "sampler_node": sampler_id,
        "positive_node": text_nodes[0][0], "size": size,
        "loras": loras, "steps": scalar(sampler["steps"]), "cfg": scalar(sampler["cfg"]),
        "sampler": sampler["sampler_name"], "scheduler": sampler["scheduler"],
        "save_prefixes": [graph[n]["inputs"]["filename_prefix"] for n in saves],
        "graph": graph, "gui": json.loads(gui) if gui else None,
    }


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path(r"D:\gas_cylinders"))
    parser.add_argument("--output", type=Path, default=Path(".tmp/cd_metadata_20261008.json"))
    args = parser.parse_args()
    root = args.data_root
    c_dirs = [root / "Placement_Issues/images", root / "Placement_Issues_2/images"]
    d_dir = root / "D1085/images"
    source_dirs = {s: root / "D" / s for s in ("real93", "new150", "new24")}
    c_paths = [p for folder in c_dirs for p in sorted(folder.glob("*.png"), key=natural_key)]
    d_paths = sorted(d_dir.glob("*.png"), key=natural_key)
    assert len(c_paths) == len(d_paths) == 1085
    assert len({p.name for p in c_paths}) == 1085
    assert len({p.name for p in d_paths}) == 1085
    source_paths = [p for folder in source_dirs.values() for p in sorted(folder.glob("*.png"), key=natural_key)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(read_record, c_paths + d_paths + source_paths))
        hashes = list(pool.map(sha256, d_paths + source_paths))
    c_records = records[:1085]
    d_records = records[1085:2170]
    sources = records[2170:]
    source_by_hash = defaultdict(list)
    for record, digest in zip(sources, hashes[1085:]):
        record["sha256"] = digest
        record["set"] = Path(record["path"]).parent.name
        source_by_hash[digest].append(record)
    mapping = []
    for record, digest in zip(d_records, hashes[:1085]):
        matches = source_by_hash[digest]
        if len(matches) != 1:
            raise ValueError(f"{record['path']}: expected unique source hash match, got {len(matches)}")
        source = matches[0]
        assert (record["seed"], record["prompt"]) == (source["seed"], source["prompt"])
        record["set"] = source["set"]
        mapping.append({"image_name": record["image_name"], "source_set": source["set"],
                        "source_image": source["image_name"], "sha256": digest})
    assert len({r["sha256"] for r in mapping}) == 1085
    assert len(source_paths) == len(mapping)

    new_prompts = {}
    for record in sorted((r for r in sources if r["set"] == "new24"), key=lambda r: natural_key(r["image_name"])):
        item = new_prompts.setdefault(record["prompt"], {"prompt": record["prompt"], "examples": []})
        item["examples"].append(record["image_name"])
    assert len(new_prompts) == 24, f"new24 has {len(new_prompts)} unique exact prompts"
    new_items = []
    for n, item in enumerate(new_prompts.values(), 151):
        new_items.append({"id": f"N{n:03d}", "set": "new24", "prompt": item["prompt"],
                          "review_status": "approved", "source": "PNG execution prompt metadata",
                          "retained_images": len(item["examples"]), "example_image": item["examples"][0]})
    catalog = []
    for name in ("real93", "new150"):
        for line in Path(f"docs/v5_prompts/{name}_prompts.jsonl").read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            count = sum(r["prompt"] == item["prompt"] for r in sources if r["set"] == name)
            catalog.append({"id": item["id"], "set": name, "prompt": item["prompt"], "retained_images": count})
        known = {r["prompt"] for r in catalog if r["set"] == name}
        assert all(r["prompt"] in known for r in sources if r["set"] == name), f"unmatched {name} text"
    catalog += [{k: r[k] for k in ("id", "set", "prompt", "retained_images")} for r in new_items]
    assert len(catalog) == 267 and sum(r["retained_images"] for r in catalog) == 1085
    runs = []
    for r in mapping:
        if not runs or runs[-1]["set"] != r["source_set"]:
            runs.append({"set": r["source_set"], "first": r["image_name"], "last": r["image_name"], "count": 1})
        else:
            runs[-1]["last"] = r["image_name"]
            runs[-1]["count"] += 1
    lora_groups = {}
    for name in source_dirs:
        group = [r for r in sources if r["set"] == name]
        lora_groups[name] = dict(Counter(json.dumps(r["loras"], sort_keys=True) for r in group))
    rename_logs = list(d_dir.glob("rename-log-*.csv"))
    rename_matches = None
    if len(rename_logs) == 1:
        with rename_logs[0].open(encoding="utf-8-sig", newline="") as f:
            old_names = {r["NewName"]: r["OldName"] for r in csv.DictReader(f)}
        rename_matches = all(old_names.get(r["image_name"]) == r["source_image"] for r in mapping)
    report = {
        "checked_date": "2026-10-08", "c_counts": {str(f): len(list(f.glob('*.png'))) for f in c_dirs},
        "d_source_counts": dict(Counter(r["set"] for r in sources)), "d_final_png_count": len(d_records),
        "d_final_txt_count": len(list((root / 'D1085').rglob('*.txt'))),
        "metadata_rows": len(c_records) + len(d_records), "missing_seed_or_prompt": 0,
        "d_numbered_filename_count": sum(bool(re.fullmatch(r"D_\d{4}\.png", p.name)) for p in d_paths),
        "d_other_filenames": [p.name for p in d_paths if not re.fullmatch(r"D_\d{4}\.png", p.name)],
        "exact_new24_prompts": len(new_items), "d_unique_sha256": 1085,
        "d_copy_hash_matches": len(mapping), "d_actual_filename_source_runs": runs,
        "rename_log": str(rename_logs[0]) if len(rename_logs) == 1 else None,
        "rename_log_matches_hash_sources": rename_matches,
        "effective_loras_by_source": lora_groups,
        "d_sizes": dict(Counter(str(r["size"]) for r in d_records)),
    }
    # Large seeds stay strings throughout JSON/JS authoring (no float conversion).
    export_rows = [[r["image_name"], r["seed"], r["prompt"]] for r in c_records + d_records]
    out = {"report": report, "rows": export_rows, "new24": new_items, "catalog": catalog, "mapping": mapping}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Capture newly encountered execution/UI workflows without changing images.
    workflow_dir = Path("docs/v5_prompts/new24_workflows")
    workflow_dir.mkdir(exist_ok=True)
    variants = {}
    for r in sources:
        if r["set"] != "new24":
            continue
        normalized = json.loads(json.dumps(r["graph"]))
        for node in normalized.values():
            for k in ("seed", "noise_seed", "prompt", "negative_prompt", "filename_prefix"):
                if k in node["inputs"]:
                    node["inputs"][k] = "<per-image>"
        signature = json.dumps(normalized, sort_keys=True)
        variants.setdefault(signature, r)
    for i, r in enumerate(variants.values(), 1):
        (workflow_dir / f"variant_{i:02d}_api.json").write_text(json.dumps(r["graph"], ensure_ascii=False, indent=2), encoding="utf-8")
        if r["gui"]:
            (workflow_dir / f"variant_{i:02d}_ui.json").write_text(json.dumps(r["gui"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(variants)} new24 workflow variants")


if __name__ == "__main__":
    main()
