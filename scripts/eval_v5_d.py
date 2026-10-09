"""D-only inference and D-minus-A/B/C statistics, reusing the v4 implementation.

No computation starts without --execute. Inference is cached per checkpoint with
weight and frozen-input hashes. Existing v4 JSONs/caches are read only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import bootstrap_paired as bp
import eval_v4_protocol as ev
from prepare_v5_d import ROOT, OUT, ARM, V4, WEIGHTS, check, require, sha, write_json
from run_v5_d import RUNS, is_complete, checkpoint_paths

RESULT = OUT / f"v5_protocol_{ARM}.json"
CACHE = OUT / "per_image" / f"per_image_{ARM}.json"
RAW = RUNS / "eval_cache"


def cached_inference(path, tag):
    from ultralytics import YOLO

    key = {"checkpoint_sha256": sha(path), "input_manifest_sha256": sha(OUT / "input_manifest.json")}
    cache_path = RAW / f"{tag}.json"
    if cache_path.exists():
        saved = json.loads(cache_path.read_text(encoding="utf-8"))
        require(saved["provenance"] == key, f"Stale inference cache: {cache_path}")
        return {name: bp.dec_row(row) for name, row in saved["rows"].items()}
    ev.CaptureValidator.latest = None
    YOLO(str(path)).val(validator=ev.CaptureValidator, data=ev.DEV_YAML, split="test",
                       imgsz=640, batch=16, device=0, workers=0, verbose=False, plots=False,
                       project=str(ROOT / "runs/detect/v5_protocol"), name=tag, exist_ok=True)
    validator = ev.CaptureValidator.latest
    require(validator is not None and len(validator.per_image) == 61, f"Incomplete predictions: {path}")
    rows = validator.per_image
    write_json(cache_path, {"provenance": key, "rows": {n: bp.enc_row(r) for n, r in rows.items()}})
    return rows


def evaluate(manifest):
    for weight in WEIGHTS:
        require(is_complete(weight), f"No verified 300-epoch completion for {weight}")
        require(set(ev.checkpoints(RUNS / weight).values()) == set(checkpoint_paths(weight)),
                f"Unexpected checkpoint candidate set: {weight}")
    folds = manifest["folds"]
    names = {Path(r["image"]).name for r in manifest["dev61"]}
    ev.infer_checkpoint = cached_inference
    stats_all, detectors = {}, {}
    cache = {"arm": ARM, "label": "D_LoRA1085", "image_names": sorted(names), "folds": folds,
             "input_manifest_sha256": sha(OUT / "input_manifest.json"), "detectors": {}, "joint": None}
    for weight in WEIGHTS:
        record, stats = ev.evaluate_weight(ARM, weight, folds, names)
        require(stats is not None and "error" not in record, f"Incomplete detector: {weight}")
        detectors[weight], stats_all[weight] = record, stats
        cache["detectors"][weight] = {
            "fixed_endpoint_epoch": 300,
            "fixed_endpoint_rows": {n: bp.enc_row(r) for n, r in stats[300].items()},
            "oof_selected_epochs": [f["selected_epoch"] for f in record["cross_fitted"]["folds"]],
            "oof_rows": {n: bp.enc_row(r) for n, r in bp.oof_rows(stats, folds, record["cross_fitted"]["folds"]).items()},
        }
    joint = ev.joint_model_selection(stats_all, folds, names)
    joint_folds = joint["cross_fitted_model_selection"]["folds"]
    rows = {n: stats_all[f["selected_detector"]][f["selected_epoch"]][n]
            for f in joint_folds for n in folds[f["fold"]]}
    cache["joint"] = {"folds": joint_folds, "oof_rows": {n: bp.enc_row(r) for n, r in rows.items()}}
    protocol = ev.protocol_record(folds)
    protocol.update(version="v5_D_extension", status="D extension after v4 results; inherits frozen v4 selection rules",
                    checkpoint_file_mapping="epoch10.pt..epoch290.pt (internal zero-based labels), last.pt (300 completed epochs); identical to v4")
    output = {"protocol": protocol, "input_manifest_sha256": sha(OUT / "input_manifest.json"),
              "arms": {ARM: {"arm": ARM, "label": "D_LoRA1085", "train_images": 1085,
                              "detectors": detectors, "joint_detector_and_checkpoint_selection": joint}}}
    # Apply the original non-convergence criterion without excluding any model.
    import numpy as np
    fixed_median = float(np.median([d["fixed_endpoint"]["metrics"]["mAP50-95"] for d in detectors.values()]))
    oof_median = float(np.median([d["cross_fitted"]["official_pooled_oof_metrics"]["mAP50-95"] for d in detectors.values()]))
    for weight, record in detectors.items():
        record["non_convergent"] = (record["fixed_endpoint"]["metrics"]["mAP50-95"] < fixed_median / 2
                                    and record["cross_fitted"]["official_pooled_oof_metrics"]["mAP50-95"] < oof_median / 2)
        record["training_diagnostic_csv"] = (RUNS / weight / "results.csv").as_posix()
    write_json(OUT / "protocol.json", protocol)
    write_json(RESULT, output)
    write_json(CACHE, cache)
    print(f"Saved {RESULT} and {CACHE}", flush=True)


def official(arm):
    path = RESULT if arm == ARM else V4 / f"v4_protocol_{arm}.json"
    return json.loads(path.read_text(encoding="utf-8"))["arms"][arm]


def load_cache(arm):
    path = CACHE if arm == ARM else V4 / "per_image" / f"per_image_{arm}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "input_manifest.json").read_text(encoding="utf-8"))
    require(value["folds"] == manifest["folds"], f"{arm}: fold mismatch")
    require(set(value["detectors"]) == set(WEIGHTS) and value["joint"] is not None, f"{arm}: incomplete cache")
    return value


def bootstrap():
    require(RESULT.exists() and CACHE.exists(), "D evaluation/cache missing; run evaluation first")
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    require(result["input_manifest_sha256"] == sha(OUT / "input_manifest.json"), "D results belong to different inputs")
    require(load_cache(ARM)["input_manifest_sha256"] == result["input_manifest_sha256"], "D cache/result input mismatch")
    # Redirect only the bootstrap module's I/O; A/B/C remain in the original directory.
    bp.load_cache, bp.official_arm, bp.OUT_DIR = load_cache, official, OUT
    for arm in ev.MAIN_ARMS:
        output = OUT / f"bootstrap_D_minus_{arm}.json"
        if output.exists():
            saved = json.loads(output.read_text(encoding="utf-8"))
            expected = {"input_manifest_sha256": sha(OUT / "input_manifest.json"), "D_result_sha256": sha(RESULT), "D_cache_sha256": sha(CACHE)}
            require(saved.get("provenance") == expected and len(saved["comparisons"]) == 13,
                    f"Existing bootstrap result is stale/incomplete: {output}")
            print(f"SKIP complete {output}", flush=True)
            continue
        args = SimpleNamespace(targets="all", n_boot=10000, out=str(output))
        bp.boot([arm, ARM], args)  # existing routine computes arm_b - arm_a
        saved = json.loads(output.read_text(encoding="utf-8"))
        saved["provenance"] = {"input_manifest_sha256": sha(OUT / "input_manifest.json"),
                               "D_result_sha256": sha(RESULT), "D_cache_sha256": sha(CACHE)}
        saved["status"] = "v5 added comparison; not retrospectively v4 preregistered"
        write_json(output, saved)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--stage", choices=["eval", "bootstrap"], default="eval")
    args = parser.parse_args()
    if not args.execute:
        print(f"PLAN ONLY: {args.stage}; use run_v5_d.py after authorization to execute with input checks and a lock.")
        return
    manifest = check()
    evaluate(manifest) if args.stage == "eval" else bootstrap()


if __name__ == "__main__":
    main()
