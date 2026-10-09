"""Accept D artifacts from disk without training, GPU inference or new bootstrap draws."""
from __future__ import annotations

import csv
from datetime import datetime
import json
import math
from pathlib import Path

import bootstrap_paired as bp
import eval_v4_protocol as ev
from prepare_v5_d import ROOT, OUT, ARM, V4, WEIGHTS, check, require, sha, write_json
from run_v5_d import RUNS, is_complete


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def same(actual, expected, context="result"):
    if isinstance(expected, dict):
        require(set(actual) == set(expected), f"{context}: keys differ")
        for key in expected:
            same(actual[key], expected[key], f"{context}.{key}")
    elif isinstance(expected, list):
        require(len(actual) == len(expected), f"{context}: list length differs")
        for i, (a, b) in enumerate(zip(actual, expected)):
            same(a, b, f"{context}[{i}]")
    elif isinstance(expected, float):
        require(math.isfinite(actual) and abs(actual - expected) <= 5e-7, f"{context}: {actual} != {expected}")
    else:
        require(actual == expected, f"{context}: {actual} != {expected}")


def main():
    manifest = check()
    require(not (OUT / "pipeline.lock").exists(), "Pipeline still holds its execution lock")
    result_path = OUT / f"v5_protocol_{ARM}.json"
    cache_path = OUT / "per_image" / f"per_image_{ARM}.json"
    result, cache = read(result_path), read(cache_path)
    manifest_hash = sha(OUT / "input_manifest.json")
    require(result["input_manifest_sha256"] == cache["input_manifest_sha256"] == manifest_hash, "Result/cache provenance mismatch")
    same(result["protocol"]["folds"], manifest["folds"], "protocol folds")
    same(cache["folds"], manifest["folds"], "cache folds")
    names = {Path(r["image"]).name for r in manifest["dev61"]}
    same(cache["image_names"], sorted(names), "cache images")
    official = result["arms"][ARM]
    require(set(official["detectors"]) == set(cache["detectors"]) == set(WEIGHTS), "Missing detector")
    raw_files = list((RUNS / "eval_cache").glob("*.json"))
    require(len(raw_files) == 180, f"Expected 180 raw prediction caches, found {len(raw_files)}")
    raw_by_path, training, metrics_table, notes = {}, {}, [], []
    for weight in WEIGHTS:
        require(is_complete(weight), f"Incomplete {weight}")  # verifies every checkpoint/args/curve/event SHA256
        completed = read(RUNS / weight / "completed.json")
        with (RUNS / weight / "results.csv").open(encoding="utf-8-sig") as stream:
            rows = [{k.strip(): v.strip() for k, v in r.items()} for r in csv.DictReader(stream)]
        nonfinite = [{"epoch": int(r["epoch"]), "fields": {k: v for k, v in r.items() if not math.isfinite(float(v))}}
                     for r in rows if any(not math.isfinite(float(v)) for v in r.values())]
        diagnostic_losses = {"val/box_loss", "val/cls_loss", "val/dfl_loss"}
        require(all(set(r["fields"]) <= diagnostic_losses for r in nonfinite), f"Nonfinite training loss/metric: {weight}")
        require(all(math.isfinite(float(v)) for v in rows[-1].values()), f"Nonfinite terminal curve: {weight}")
        if nonfinite:
            notes.append({"detector": weight, "issue": "transient nonfinite train-set validation losses",
                          "rows": nonfinite, "resolution": "training losses and metrics finite; terminal self-validation losses finite; diagnostic self-val never used for selection; retain original run"})
        batches = [event["batch"] for event in completed["batch_events"]]
        require(batches and all(b in (16, 8) for b in batches), f"Invalid batch history: {weight}")
        checkpoints = ev.checkpoints(RUNS / weight)
        require(set(checkpoints) == set(range(10, 301, 10)), f"Incomplete candidate list: {weight}")
        for epoch, path in checkpoints.items():
            raw = read(RUNS / "eval_cache" / f"{ARM}_{weight}_e{epoch}.json")
            same(raw["provenance"], {"checkpoint_sha256": completed["files"][path.as_posix()],
                                     "input_manifest_sha256": manifest_hash}, f"{weight} e{epoch} provenance")
            require(set(raw["rows"]) == names, f"Missing dev image: {weight} e{epoch}")
            for row in manifest["dev61"]:
                require(raw["rows"][Path(row["image"]).name]["n_gt"] == row["boxes"], "Ground truth differs")
            raw_by_path[path] = {n: bp.dec_row(r) for n, r in raw["rows"].items()}
        training[weight] = {"epochs": len(rows), "batch_history": batches,
                            "training_hours": round(float(rows[-1]["time"]) / 3600, 4),
                            "finished_at": completed["finished_at"], "checkpoint_candidates": len(checkpoints)}
    # Reconstruct all selection curves from exact saved predictions; never loads a model.
    ev.infer_checkpoint = lambda path, tag: raw_by_path[path]
    all_stats = {}
    for weight in WEIGHTS:
        recalculated, stats = ev.evaluate_weight(ARM, weight, manifest["folds"], names)
        ref = {k: v for k, v in official["detectors"][weight].items()
               if k not in ("non_convergent", "training_diagnostic_csv")}
        same(recalculated, ref, weight)
        all_stats[weight] = stats
        entry = cache["detectors"][weight]
        same(bp.metrics_of([bp.dec_row(entry["fixed_endpoint_rows"][n]) for n in sorted(names)]),
             {m: ref["fixed_endpoint"]["metrics"][m] for m in bp.METRICS}, weight + " fixed cache")
        same(bp.metrics_of([bp.dec_row(entry["oof_rows"][n]) for n in sorted(names)]),
             {m: ref["cross_fitted"]["official_pooled_oof_metrics"][m] for m in bp.METRICS}, weight + " OOF cache")
        metrics_table.append({"detector": weight, "fixed_mAP50_95": ref["fixed_endpoint"]["metrics"]["mAP50-95"],
                              "fixed_mAP50": ref["fixed_endpoint"]["metrics"]["mAP50"],
                              "oof_mAP50_95": ref["cross_fitted"]["official_pooled_oof_metrics"]["mAP50-95"],
                              "oof_mAP50": ref["cross_fitted"]["official_pooled_oof_metrics"]["mAP50"],
                              "deployment_epoch_label": ref["deployment"]["selected_epoch"],
                              "non_convergent": official["detectors"][weight]["non_convergent"]})
    joint = ev.joint_model_selection(all_stats, manifest["folds"], names)
    same(joint, official["joint_detector_and_checkpoint_selection"], "joint selection")
    same(bp.metrics_of([bp.dec_row(cache["joint"]["oof_rows"][n]) for n in sorted(names)]),
         {m: joint["cross_fitted_model_selection"]["official_pooled_oof_metrics"][m] for m in bp.METRICS}, "joint cache")
    joint_comparisons = []
    for arm in ev.MAIN_ARMS:
        boot_path = OUT / f"bootstrap_D_minus_{arm}.json"
        boot = read(boot_path)
        same(boot["provenance"], {"input_manifest_sha256": manifest_hash,
                                 "D_result_sha256": sha(result_path), "D_cache_sha256": sha(cache_path)}, "bootstrap provenance")
        require(boot["params"]["n_boot"] == 10000 and boot["params"]["seed"] == 0, "Bootstrap params drift")
        require(boot["params"]["primary_metric"] == "mAP50-95", "Bootstrap primary metric drift")
        expected_targets = {(t, d) for t, d in [("joint", None)] + [(t, w) for t in ("fixed_endpoint", "oof") for w in WEIGHTS]}
        require({(c["target"], c["detector"]) for c in boot["comparisons"]} == expected_targets and len(boot["comparisons"]) == 13,
                "Missing/duplicate bootstrap target")
        control = bp.load_cache(arm)
        same(control["folds"], manifest["folds"], "ABC folds")
        for comparison in boot["comparisons"]:
            target, detector = comparison["target"], comparison["detector"]
            require(comparison["arm_a"] == arm and comparison["arm_b"] == ARM and comparison["n_boot"] == 10000, "Comparison mismatch")
            for name, selected_cache in [("a", control), ("b", cache)]:
                rows = bp.target_rows(selected_cache, target, detector)
                point = bp.metrics_of([bp.dec_row(rows[n]) for n in sorted(names)])
                same(point, comparison[f"point_{name}"], "bootstrap point")
            for metric in bp.METRICS:
                same(round(comparison["point_b"][metric] - comparison["point_a"][metric], 6), comparison["observed_delta"][metric], "bootstrap delta")
                ci = comparison[metric]["ci95"]
                require(len(ci) == 2 and all(math.isfinite(x) for x in ci) and ci[0] <= ci[1], "Invalid confidence interval")
            if target == "joint":
                joint_comparisons.append(comparison)
    logs = ROOT / "logs/v5_d"
    eval_logs = list(logs.glob("*_eval.log"))
    require(len(eval_logs) == 1, "Inspect multiple evaluation logs before acceptance")
    eval_text = eval_logs[0].read_text(encoding="utf-8", errors="replace")
    require(not any(x in eval_text for x in ("Traceback", "out of memory")), "Evaluation error needs investigation")
    nms_warnings = [line for line in eval_text.splitlines() if "NMS time limit" in line]
    # AutoBackend.warmup uses one dummy image: 2+.05*1 = 2.050s.
    # Real validation batches contain 16/13 images: their budgets are 2.800/2.650s.
    require(all("NMS time limit 2.050s exceeded" in line for line in nms_warnings), "Real validation NMS timeout needs investigation")
    if nms_warnings:
        notes.append({"issue": "single-image dummy NMS warmup timeout", "count": len(nms_warnings),
                      "resolution": "budget 2.050s identifies AutoBackend warmup; real dev61 batches use 16/13 images; no real-batch timeout",
                      "source": "ultralytics/nn/autobackend.py:AutoBackend.warmup; ultralytics/utils/nms.py:time_limit"})
    execution = read(OUT / "execution.json")
    stdout = (ROOT / execution["stdout"]).read_text(encoding="utf-8", errors="replace")
    stderr = (ROOT / execution["stderr"]).read_text(encoding="utf-8", errors="replace")
    require("DONE bootstrap" in stdout and not stderr.strip(), "Pipeline did not finish cleanly")
    finish = datetime.fromtimestamp((ROOT / execution["stdout"]).stat().st_mtime).astimezone().isoformat()
    acceptance = {"status": "passed_with_notes" if notes else "passed", "audited_at": datetime.now().astimezone().isoformat(),
                  "pipeline_finished_at": finish, "training": training, "raw_prediction_caches": 180,
                  "bootstrap_comparisons": 39, "bootstrap_draws_per_comparison": 10000,
                  "selection_and_AP_recomputed_from_cached_predictions": True,
                  "checkpoint_and_frozen_input_hashes_verified": True, "v4_controls_unchanged": True,
                  "metrics": metrics_table, "joint": joint, "joint_comparisons": joint_comparisons, "diagnostic_notes": notes,
                  "limitations": "dev61 is a reused development benchmark; one detector-training seed; no new frozen external test yet."}
    write_json(OUT / "acceptance.json", acceptance)
    with (OUT / "detector_metrics.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(metrics_table[0]))
        writer.writeheader()
        writer.writerows(metrics_table)
    print(f"ACCEPTED: six complete runs, 180 predictions, 39 paired comparisons; pipeline finished {finish}")
    print(json.dumps(joint, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
