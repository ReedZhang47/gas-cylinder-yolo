r"""Paired cluster bootstrap for the v4 arm comparison (A/B/C).

The cluster unit is the dev61 image. The pre-registered plan resamples images (or known
source-scene groups) with replacement and never treats the 72 boxes as 72 independent
samples. dev61 has no scene-group metadata, so the cluster is the image itself
(61 clusters).

This script imports ``eval_v4_protocol`` instead of reimplementing selection, so the
bootstrap shares one implementation with the official numbers. Two phases:

dump  run the same inference and selection as the official evaluation, then persist the
      per-image detection rows needed to recompute AP. Dumped point estimates are asserted
      against ``v4_protocol_<arm>.json``; any mismatch aborts.
boot  recompute AP on the full sample once (must reproduce the official value), then
      resample images with replacement and recompute AP for both arms on the *same*
      resampled set (paired). Reports observed delta, bootstrap CI and P(delta > 0).

Usage:
  python scripts/bootstrap_paired.py --dump --arm real93v4
  python scripts/bootstrap_paired.py --dump --arm real93v4 --only-detector yolo26s
  python scripts/bootstrap_paired.py --boot --arms real93v4,aug1085v4,gen1085v4
  python scripts/bootstrap_paired.py --self-test

Windows note: __main__ guard + workers=0 are inherited from eval_v4_protocol.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_v4_protocol as ev  # single source of truth for inference and checkpoint selection
from ultralytics.utils.metrics import ap_per_class

OUT_DIR = ev.OUT_DIR
CACHE_DIR = OUT_DIR / "per_image"
KEYS = ("tp", "conf", "pred_cls", "target_cls")
NAMES = {0: "Placement Issues"}
# mAP50-95 stays the primary and selection metric (pre-registered); mAP50 is reported
# alongside it in the same pass, as COCO-style tables normally do.
PRIMARY_METRIC = "mAP50-95"
METRICS = ("mAP50-95", "mAP50")
N_BOOT = 10000
BOOT_SEED = 0
PAIRS = [("real93v4", "aug1085v4"), ("real93v4", "gen1085v4"), ("aug1085v4", "gen1085v4")]
TOL = 5e-7


def enc_row(row: dict) -> dict:
    """Compact lossless encoding of one image's detection rows.

    Each detection's row of `tp` is stored as a 10-bit mask instead of ten booleans. The
    mask is general on purpose: Ultralytics matches predictions to ground truth greedily at
    each IoU threshold independently, so a detection can be correct at an intermediate
    threshold and wrong at a looser one (measured: 325 of 19448 detections on the A arm), and
    a "correct above IoU k" encoding would silently corrupt those rows.

    The dataset has a single class, so `pred_cls` is constant 0 and `target_cls` is stored as
    its length. `conf` is kept at full precision: rounding it could create ties and change AP.
    """
    tp = np.asarray(row["tp"], dtype=bool)
    conf = np.asarray(row["conf"], dtype=float)
    pred_cls = np.asarray(row["pred_cls"], dtype=float)
    target_cls = np.asarray(row["target_cls"], dtype=float)
    n_iou = tp.shape[1] if tp.ndim == 2 else 0
    masks = tp.astype(np.uint16) @ (1 << np.arange(n_iou, dtype=np.uint16)) if tp.size else np.zeros(0, dtype=np.uint16)
    assert not pred_cls.size or pred_cls.max() == 0
    assert not target_cls.size or target_cls.max() == 0
    return {
        "n_iou": int(n_iou),
        "tp_masks": masks.astype(int).tolist(),
        "conf": conf.tolist(),
        "n_gt": int(target_cls.size),
    }


def dec_row(entry: dict) -> dict:
    masks = np.asarray(entry["tp_masks"], dtype=np.uint16)
    conf = np.asarray(entry["conf"], dtype=float)
    n_iou = entry["n_iou"]
    tp = ((masks[:, None] >> np.arange(n_iou, dtype=np.uint16)[None, :]) & 1).astype(bool)
    return {
        "tp": tp,
        "conf": conf,
        "pred_cls": np.zeros(conf.size),
        "target_cls": np.zeros(entry["n_gt"]),
    }


def metrics_of(rows: list[dict]) -> dict[str, float]:
    """mAP50 / mAP50-95 from per-image rows, matching eval_v4_protocol.aggregate."""
    arrays = {key: np.concatenate([row[key] for row in rows], axis=0) for key in KEYS}
    result = ap_per_class(arrays["tp"], arrays["conf"], arrays["pred_cls"], arrays["target_cls"], names=NAMES)
    ap = result[5]
    if ap.size == 0:
        return {"mAP50": 0.0, "mAP50-95": 0.0}
    return {"mAP50": round(float(np.mean(ap[:, 0])), 6), "mAP50-95": round(float(np.mean(ap)), 6)}


def load_folds() -> tuple[list[list[str]], set[str]]:
    images = [Path(line.strip()) for line in ev.DEV_LIST.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    assert len(images) == 61 and len({p.name for p in images}) == 61
    folds = ev.build_folds(images)
    protocol = OUT_DIR / "protocol.json"
    if protocol.exists():
        saved = json.loads(protocol.read_text(encoding="utf-8"))["folds"]
        assert saved == folds, f"fold definition drifted from {protocol}"
    return folds, {path.name for path in images}


def official_arm(arm: str) -> dict | None:
    path = OUT_DIR / f"v4_protocol_{arm}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))["arms"][arm]


def check(arm: str, what: str, got, want) -> None:
    """Abort unless the dumped value reproduces the official one (float tolerance, else equality)."""
    if want is None:
        return
    if isinstance(got, str) or isinstance(want, str):
        if got != want:
            raise RuntimeError(f"{arm} {what}: dumped {got} != official {want}")
    elif abs(got - want) > TOL:
        raise RuntimeError(f"{arm} {what}: dumped {got} != official {want}")


def oof_rows(stats: dict, folds: list[list[str]], fold_records: list[dict]) -> dict[str, dict]:
    """Per-image rows behind the pooled OOF estimate: each fold's held-out images only."""
    rows = {}
    for fold_id, heldout in enumerate(folds):
        epoch = fold_records[fold_id]["selected_epoch"]
        for name in heldout:
            rows[name] = stats[epoch][name]
    return rows


def write_cache(arm: str, cache: dict) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"per_image_{arm}.json"
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def dump(arm: str, only_detector: str | None) -> None:
    folds, all_names = load_folds()
    official = official_arm(arm)
    if official is None:
        print(f"WARNING no official JSON for {arm}; point estimates will not be asserted")
    weights = [only_detector] if only_detector else list(ev.WEIGHTS)
    cache = {
        "arm": arm,
        "label": ev.ARM_LABELS[arm],
        "image_names": sorted(all_names),
        "folds": folds,
        "detectors": {},
        "joint": None,
    }
    stats_all: dict[str, dict] = {}
    for weight in weights:
        print(f"== dump {arm}/{weight} ==", flush=True)
        record, stats = ev.evaluate_weight(arm, weight, folds, all_names)
        if "error" in record:
            raise RuntimeError(f"{arm}/{weight}: {record['error']}")
        stats_all[weight] = stats
        if official is not None:
            ref = official["detectors"][weight]
            for metric in METRICS:
                check(arm, f"{weight} fixed endpoint {metric}",
                      record["fixed_endpoint"]["metrics"][metric], ref["fixed_endpoint"]["metrics"][metric])
                check(arm, f"{weight} pooled OOF {metric}",
                      record["cross_fitted"]["official_pooled_oof_metrics"][metric],
                      ref["cross_fitted"]["official_pooled_oof_metrics"][metric])
            check(arm, f"{weight} deployment epoch",
                  record["deployment"]["selected_epoch"], ref["deployment"]["selected_epoch"])
        cache["detectors"][weight] = {
            "fixed_endpoint_epoch": 300,
            "fixed_endpoint_rows": {name: enc_row(row) for name, row in stats[300].items()},
            "oof_selected_epochs": [fold["selected_epoch"] for fold in record["cross_fitted"]["folds"]],
            "oof_rows": {name: enc_row(row)
                         for name, row in oof_rows(stats, folds, record["cross_fitted"]["folds"]).items()},
        }
        print(f"saved -> {write_cache(arm, cache)}", flush=True)

    if only_detector or not stats_all:
        return
    joint = ev.joint_model_selection(stats_all, folds, all_names)
    joint_folds = joint["cross_fitted_model_selection"]["folds"]
    if official is not None:
        ref = official["joint_detector_and_checkpoint_selection"]
        for metric in METRICS:
            check(arm, f"joint pooled OOF {metric}",
                  joint["cross_fitted_model_selection"]["official_pooled_oof_metrics"][metric],
                  ref["cross_fitted_model_selection"]["official_pooled_oof_metrics"][metric])
        check(arm, "joint deployment detector",
              joint["deployment_model"]["detector"], ref["deployment_model"]["detector"])
        check(arm, "joint deployment epoch",
              joint["deployment_model"]["epoch"], ref["deployment_model"]["epoch"])
    rows = {}
    for fold in joint_folds:
        for name in folds[fold["fold"]]:
            rows[name] = stats_all[fold["selected_detector"]][fold["selected_epoch"]][name]
    cache["joint"] = {
        "folds": joint_folds,
        "oof_rows": {name: enc_row(row) for name, row in rows.items()},
    }
    print(f"saved -> {write_cache(arm, cache)}", flush=True)


def load_cache(arm: str) -> dict:
    path = CACHE_DIR / f"per_image_{arm}.json"
    if not path.exists():
        raise SystemExit(f"missing cache {path}; run --dump --arm {arm} first")
    return json.loads(path.read_text(encoding="utf-8"))


def target_rows(cache: dict, target: str, detector: str | None) -> dict[str, dict]:
    if target == "joint":
        entry = cache["joint"]
        if entry is None:
            raise SystemExit(f"{cache['arm']}: joint rows missing (re-run dump without --only-detector)")
        return entry["oof_rows"]
    return cache["detectors"][detector][f"{target}_rows"]


def targets_of(args) -> list[tuple[str, str | None]]:
    items: list[tuple[str, str | None]] = []
    if args.targets in ("all", "joint"):
        items.append(("joint", None))
    if args.targets in ("all", "fixed"):
        items.extend(("fixed_endpoint", weight) for weight in ev.WEIGHTS)
    if args.targets in ("all", "oof"):
        items.extend(("oof", weight) for weight in ev.WEIGHTS)
    return items


def bootstrap_pair(ordered_a, ordered_b, names: list[str], n_boot: int, seed: int) -> dict:
    """Paired cluster bootstrap over images; both arms see the same resampled clusters.

    Every reported metric is accumulated in the same pass, so carrying a secondary metric
    costs no extra resampling.
    """
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(names), size=(n_boot, len(names)))
    deltas = {metric: np.empty(n_boot, dtype=float) for metric in METRICS}
    degenerate = 0
    for step, draw in enumerate(draws):
        rows_a = [ordered_a[i] for i in draw]
        rows_b = [ordered_b[i] for i in draw]
        ma = metrics_of(rows_a)
        mb = metrics_of(rows_b)
        if ma[PRIMARY_METRIC] == 0.0 and mb[PRIMARY_METRIC] == 0.0:
            degenerate += 1
        for metric in METRICS:
            deltas[metric][step] = mb[metric] - ma[metric]
    out = {"n_boot": n_boot, "n_degenerate_resamples": degenerate}
    for metric in METRICS:
        values = deltas[metric]
        low, high = (float(x) for x in np.percentile(values, [2.5, 97.5]))
        out[metric] = {
            "mean_delta": round(float(values.mean()), 6),
            "ci95": [round(low, 6), round(high, 6)],
            "prob_delta_gt0": round(float((values > 0).mean()), 6),
        }
    return out


def boot(arms: list[str], args) -> None:
    caches = {arm: load_cache(arm) for arm in arms}
    names = caches[arms[0]]["image_names"]
    for arm in arms[1:]:
        assert caches[arm]["image_names"] == names, f"{arm} image set differs from {arms[0]}"
    result = {
        "params": {
            "primary_metric": PRIMARY_METRIC,
            "reported_metrics": list(METRICS),
            "n_boot": args.n_boot,
            "seed": BOOT_SEED,
            "cluster": "dev61 image (no scene-group metadata available; boxes are never resampled alone)",
            "design": "paired: both arms scored on the same resampled image set",
        },
        "arms": {arm: caches[arm]["label"] for arm in arms},
        "comparisons": [],
    }
    for target, detector in targets_of(args):
        rows = {arm: {name: dec_row(entry) for name, entry in target_rows(caches[arm], target, detector).items()}
                for arm in arms}
        ordered = {arm: [rows[arm][name] for name in names] for arm in arms}
        point = {arm: metrics_of(ordered[arm]) for arm in arms}
        for arm in arms:
            official = official_arm(arm)
            if official is not None:
                for metric in METRICS:
                    want = (official["joint_detector_and_checkpoint_selection"]["cross_fitted_model_selection"]
                            ["official_pooled_oof_metrics"][metric] if target == "joint"
                            else official["detectors"][detector][
                                "fixed_endpoint" if target == "fixed_endpoint" else "cross_fitted"
                            ][("metrics" if target == "fixed_endpoint" else "official_pooled_oof_metrics")][metric])
                    check(arm, f"{target} {detector or ''} point estimate {metric}", point[arm][metric], want)
        for arm_a, arm_b in [(a, b) for i, a in enumerate(arms) for b in arms[i + 1:]]:
            entry = {
                "target": target,
                "detector": detector,
                "arm_a": arm_a,
                "arm_b": arm_b,
                "point_a": {metric: point[arm_a][metric] for metric in METRICS},
                "point_b": {metric: point[arm_b][metric] for metric in METRICS},
                "observed_delta": {metric: round(point[arm_b][metric] - point[arm_a][metric], 6)
                                   for metric in METRICS},
            }
            entry.update(bootstrap_pair(ordered[arm_a], ordered[arm_b], names, args.n_boot, BOOT_SEED))
            result["comparisons"].append(entry)
            detail = "  ".join(f"{metric} {entry['observed_delta'][metric]:+.4f} {entry[metric]['ci95']}"
                               for metric in METRICS)
            print(f"{target:<15} {str(detector):<8} {arm_b} - {arm_a}: {detail}", flush=True)
    out = Path(args.out) if Path(args.out).is_absolute() else OUT_DIR / args.out
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"saved -> {out}")


def self_test() -> None:
    """Identical arms must give delta 0 and a degenerate CI; catches pairing/indexing bugs."""
    rng = np.random.default_rng(0)
    names = [f"img{i:02d}.jpg" for i in range(61)]
    rows = {}
    for i, name in enumerate(names):
        n = int(rng.integers(0, 8))
        tp = (rng.random((n, 10)) > 0.5).astype(bool)
        rows[name] = {"tp": tp, "conf": rng.random(n), "pred_cls": np.zeros(n), "target_cls": np.zeros(int(rng.integers(0, 3)))}
    ordered = [rows[name] for name in names]
    point = metrics_of(ordered)
    for name in names:
        back = dec_row(enc_row(rows[name]))
        assert np.array_equal(back["tp"], rows[name]["tp"]), f"tp round-trip changed {name}"
        assert np.array_equal(back["conf"], rows[name]["conf"]), f"conf round-trip changed {name}"
        assert back["target_cls"].size == rows[name]["target_cls"].size, name
        assert back["pred_cls"].size == rows[name]["pred_cls"].size, name
    assert metrics_of([dec_row(enc_row(row)) for row in ordered]) == point
    stats = bootstrap_pair(ordered, ordered, names, 200, 0)
    shuffled = list(reversed(ordered))
    for metric in METRICS:
        assert stats[metric]["ci95"] == [0.0, 0.0], stats
        assert stats[metric]["prob_delta_gt0"] == 0.0, stats
        assert abs(metrics_of(shuffled)[metric] - point[metric]) < 1e-12, "row order must not change AP"
    print(f"self-test OK (synthetic {PRIMARY_METRIC}={point[PRIMARY_METRIC]}, mAP50={point['mAP50']})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", action="store_true", help="run official inference and cache per-image rows")
    parser.add_argument("--boot", action="store_true", help="run the paired cluster bootstrap from caches")
    parser.add_argument("--self-test", action="store_true", help="offline check of the resampling machinery")
    parser.add_argument("--arm", choices=list(ev.ARM_LABELS))
    parser.add_argument("--arms", default="real93v4,aug1085v4,gen1085v4")
    parser.add_argument("--only-detector", default=None, help="dump a single detector (cheap integration test)")
    parser.add_argument("--targets", default="all", choices=["all", "joint", "fixed", "oof"])
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument("--out", default="bootstrap_paired.json", help="output name under experiments/v4_protocol/, or an absolute path")
    args = parser.parse_args()

    if args.self_test:
        self_test()
    if args.dump:
        if not args.arm:
            raise SystemExit("--dump requires --arm")
        dump(args.arm, args.only_detector)
    if args.boot:
        boot([a for a in args.arms.split(",") if a], args)
    if not (args.self_test or args.dump or args.boot):
        parser.print_help()


if __name__ == "__main__":
    main()
