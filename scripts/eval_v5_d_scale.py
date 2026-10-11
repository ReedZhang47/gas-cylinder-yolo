"""D493 evaluation and D1085-minus-D493 scale bootstrap; safe plan-only default."""
from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import bootstrap_paired as bp
import eval_v4_protocol as ev
import eval_v5_d as inference
import prepare_v5_d as parent
from prepare_v5_d_scale import ROOT, OUT, ARM, RUNS, WEIGHTS, check, read, require, sha, write_json
from run_v5_d_scale import configure_training, training

RESULT = OUT / f"v5_protocol_{ARM}.json"
CACHE = OUT / "per_image" / f"per_image_{ARM}.json"


def evaluate(manifest):
    configure_training()
    for w in WEIGHTS:
        require(training.is_complete(w), f"No verified 300-epoch completion: {w}")
        require(set(ev.checkpoints(RUNS / w).values()) == set(training.checkpoint_paths(w)), f"Invalid snapshots: {w}")
    inference.OUT, inference.ARM, inference.RAW = OUT, ARM, RUNS / "eval_cache"
    ev.infer_checkpoint = inference.cached_inference
    folds = manifest["folds"]
    names = {Path(r["image"]).name for r in manifest["dev61"]}
    stats_all, detectors = {}, {}
    cache = {"arm": ARM, "label": "D_LoRA493", "image_names": sorted(names), "folds": folds,
             "input_manifest_sha256": sha(OUT / "input_manifest.json"), "detectors": {}, "joint": None}
    for w in WEIGHTS:
        record, stats = ev.evaluate_weight(ARM, w, folds, names)
        require(stats is not None and "error" not in record, f"Incomplete detector: {w}")
        detectors[w], stats_all[w] = record, stats
        cache["detectors"][w] = {
            "fixed_endpoint_epoch": 300,
            "fixed_endpoint_rows": {n: bp.enc_row(r) for n, r in stats[300].items()},
            "oof_selected_epochs": [f["selected_epoch"] for f in record["cross_fitted"]["folds"]],
            "oof_rows": {n: bp.enc_row(r) for n, r in bp.oof_rows(stats, folds, record["cross_fitted"]["folds"]).items()}}
    joint = ev.joint_model_selection(stats_all, folds, names)
    joint_folds = joint["cross_fitted_model_selection"]["folds"]
    rows = {n: stats_all[f["selected_detector"]][f["selected_epoch"]][n]
            for f in joint_folds for n in folds[f["fold"]]}
    cache["joint"] = {"folds": joint_folds, "oof_rows": {n: bp.enc_row(r) for n, r in rows.items()}}
    protocol = ev.protocol_record(folds)
    protocol.update(version="v5_D_scale_extension", status="D493 added after D1085 results; frozen v4 selection rules",
                    checkpoint_file_mapping="epoch10.pt..epoch290.pt (zero-based labels), last.pt (300 completed epochs); identical to C493/D1085",
                    sampling=manifest["sampling"])
    fixed_med = float(np.median([d["fixed_endpoint"]["metrics"]["mAP50-95"] for d in detectors.values()]))
    oof_med = float(np.median([d["cross_fitted"]["official_pooled_oof_metrics"]["mAP50-95"] for d in detectors.values()]))
    for w, record in detectors.items():
        record["non_convergent"] = (record["fixed_endpoint"]["metrics"]["mAP50-95"] < fixed_med / 2 and
                                    record["cross_fitted"]["official_pooled_oof_metrics"]["mAP50-95"] < oof_med / 2)
        record["training_diagnostic_csv"] = (RUNS / w / "results.csv").as_posix()
    write_json(OUT / "protocol.json", protocol)
    write_json(RESULT, {"protocol": protocol, "input_manifest_sha256": sha(OUT / "input_manifest.json"),
                        "arms": {ARM: {"arm": ARM, "label": "D_LoRA493", "train_images": 493,
                                        "detectors": detectors, "joint_detector_and_checkpoint_selection": joint}}})
    write_json(CACHE, cache)
    print(f"Saved {RESULT} and {CACHE}", flush=True)


def official(arm):
    path = RESULT if arm == ARM else parent.OUT / f"v5_protocol_{parent.ARM}.json"
    return read(path)["arms"][arm]


def load_cache(arm):
    path = CACHE if arm == ARM else parent.OUT / "per_image" / f"per_image_{parent.ARM}.json"
    cache = read(path)
    require(cache["folds"] == read(OUT / "input_manifest.json")["folds"], f"{arm}: fold mismatch")
    require(set(cache["detectors"]) == set(WEIGHTS) and cache["joint"] is not None, f"{arm}: incomplete cache")
    return cache


def bootstrap():
    require(RESULT.exists() and CACHE.exists(), "D493 evaluation/cache missing")
    manifest_hash = sha(OUT / "input_manifest.json")
    require(read(RESULT)["input_manifest_sha256"] == load_cache(ARM)["input_manifest_sha256"] == manifest_hash,
            "D493 cache/result inputs mismatch")
    bp.load_cache, bp.official_arm, bp.OUT_DIR = load_cache, official, OUT
    output = OUT / "bootstrap_D1085_minus_D493.json"
    provenance = {"input_manifest_sha256": manifest_hash, "D493_result_sha256": sha(RESULT), "D493_cache_sha256": sha(CACHE),
                  "D1085_result_sha256": sha(parent.OUT / f"v5_protocol_{parent.ARM}.json"),
                  "D1085_cache_sha256": sha(parent.OUT / "per_image" / f"per_image_{parent.ARM}.json")}
    if output.exists():
        saved = read(output)
        require(saved.get("provenance") == provenance and len(saved["comparisons"]) == 13, "Stale/incomplete scale bootstrap")
        print(f"SKIP complete {output}", flush=True)
        return
    bp.boot([ARM, parent.ARM], SimpleNamespace(targets="all", n_boot=10000, out=str(output)))
    saved = read(output)
    saved.update(provenance=provenance, status="v5 scale extension after D1085 results; one subset and one training seed")
    require(len(saved["comparisons"]) == 13, "Missing scale comparison")
    write_json(output, saved)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--stage", choices=["eval", "bootstrap"], default="eval")
    args = parser.parse_args()
    if not args.execute:
        print(f"PLAN ONLY: {args.stage}; run_v5_d_scale.py handles input checks and execution lock.")
        return
    manifest = check()
    evaluate(manifest) if args.stage == "eval" else bootstrap()


if __name__ == "__main__":
    main()
