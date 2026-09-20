r"""Evaluate the v4 three-layer reporting protocol on dev61.

For every arm and detector, each checkpoint is inferred on all 61 development
images once. Per-image detection statistics are retained so the same inference can
support three distinct reports without mixing their statistical roles:

1. fixed_endpoint: last.pt at epoch 300 on all dev61 (transparent benchmark);
2. cross_fitted: five stratified outer folds. Each fold selects a checkpoint on
   the other four folds using a pre-registered 3-point-smoothed mAP50-95 curve,
   then contributes predictions only for its held-out images. The five held-out
   prediction sets are pooled before AP is computed;
3. deployment: select on all dev61 with the same rule. Its score is a development
   score, not a generalization estimate.

The script also performs arm-level nested selection over both detector family and
checkpoint. That is the honest estimate to cite if the final model is chosen from
all six detectors. Fold mAP values are diagnostic only and are never averaged as
the official cross-fitted score.

Fold definition: seed 42, five folds, stratified by non-empty/empty label file.
Selection ties resolve to the earlier epoch, then the earlier detector in WEIGHTS.

Usage:
  python scripts/eval_v4_protocol.py --arm all
  python scripts/eval_v4_protocol.py --arm real93v4

Windows note: __main__ guard + workers=0.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
from ultralytics import YOLO
from ultralytics.models.yolo.detect import DetectionValidator
from ultralytics.utils.metrics import ap_per_class

ROOT = Path(r"D:\yolo")
RUNS = ROOT / "runs" / "detect"
OUT_DIR = ROOT / "experiments" / "v4_protocol"
DEV_LIST = Path(r"D:\gas_cylinders\v4\dev61.txt")
DEV_YAML = r"D:\gas_cylinders\v4\data_dev61.yaml"
FOLD_SEED = 42
N_FOLDS = 5
WEIGHTS = ["yolov8s", "yolov8m", "yolo11s", "yolo11m", "yolo26s", "yolo26m"]
ARM_LABELS = {
    "real93v4": "A_real93",
    "aug1085v4": "B_aug1085",
    "gen1085v4": "C_gen1085",
    "gen493v4": "scale_gen493",
}
MAIN_ARMS = ["real93v4", "aug1085v4", "gen1085v4"]
TRAIN_SIZES = {"real93v4": 93, "aug1085v4": 1085, "gen1085v4": 1085, "gen493v4": 493}


class CaptureValidator(DetectionValidator):
    """Retain the per-image arrays that Ultralytics normally clears after AP."""

    latest: "CaptureValidator | None" = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.per_image: dict[str, dict[str, np.ndarray]] = {}
        CaptureValidator.latest = self

    def update_metrics(self, preds, batch):
        before = len(self.metrics.stats["tp"])
        super().update_metrics(preds, batch)
        files = batch["im_file"]
        for offset, file in enumerate(files):
            index = before + offset
            self.per_image[Path(file).name] = {
                key: np.array(self.metrics.stats[key][index], copy=True)
                for key in ("tp", "conf", "pred_cls", "target_cls")
            }


def label_path(image: Path) -> Path:
    parts = list(image.parts)
    try:
        parts[len(parts) - 1 - parts[::-1].index("images")] = "labels"
    except ValueError as exc:
        raise ValueError(f"image path has no images directory: {image}") from exc
    return Path(*parts).with_suffix(".txt")


def build_folds(images: list[Path]) -> list[list[str]]:
    positive, empty = [], []
    for image in images:
        label = label_path(image)
        (positive if label.exists() and label.stat().st_size else empty).append(image.name)
    rng = random.Random(FOLD_SEED)
    rng.shuffle(positive)
    rng.shuffle(empty)
    folds = [[] for _ in range(N_FOLDS)]
    for group in (positive, empty):
        for i, name in enumerate(group):
            folds[i % N_FOLDS].append(name)
    for fold in folds:
        fold.sort()
    assert sorted(name for fold in folds for name in fold) == sorted(p.name for p in images)
    return folds


def aggregate(records: dict[str, dict[str, np.ndarray]], names: set[str] | list[str]) -> dict[str, float]:
    selected = [records[name] for name in names]
    arrays = {key: np.concatenate([row[key] for row in selected], axis=0)
              for key in ("tp", "conf", "pred_cls", "target_cls")}
    result = ap_per_class(
        arrays["tp"], arrays["conf"], arrays["pred_cls"], arrays["target_cls"], names={0: "Placement Issues"}
    )
    p, r, ap = result[2], result[3], result[5]
    return {
        "P": round(float(np.mean(p)) if len(p) else 0.0, 6),
        "R": round(float(np.mean(r)) if len(r) else 0.0, 6),
        "mAP50": round(float(np.mean(ap[:, 0])) if ap.size else 0.0, 6),
        "mAP50-95": round(float(np.mean(ap)) if ap.size else 0.0, 6),
    }


def smooth_curve(curve: dict[int, dict[str, float]]) -> dict[int, float]:
    epochs = sorted(curve)
    smoothed = {}
    for i, epoch in enumerate(epochs):
        neighbors = epochs[max(0, i - 1): min(len(epochs), i + 2)]
        smoothed[epoch] = sum(curve[e]["mAP50-95"] for e in neighbors) / len(neighbors)
    return smoothed


def select_epoch(curve: dict[int, dict[str, float]]) -> tuple[int, dict[int, float]]:
    smoothed = smooth_curve(curve)
    epoch = min(smoothed, key=lambda e: (-smoothed[e], e))
    return epoch, smoothed


def epoch_of(path: Path) -> int:
    return 300 if path.stem == "last" else int(path.stem.removeprefix("epoch"))


def checkpoints(folder: Path) -> dict[int, Path]:
    found = {epoch_of(path): path for path in folder.glob("weights/epoch*.pt")}
    last = folder / "weights" / "last.pt"
    if last.exists():
        found[300] = last
    return dict(sorted(found.items()))


def infer_checkpoint(path: Path, tag: str) -> dict[str, dict[str, np.ndarray]]:
    CaptureValidator.latest = None
    YOLO(str(path)).val(
        validator=CaptureValidator,
        data=DEV_YAML,
        split="test",
        imgsz=640,
        batch=16,
        device=0,
        workers=0,
        verbose=False,
        plots=False,
        project=str(RUNS),
        name=f"v4_protocol/{tag}",
        exist_ok=True,
    )
    validator = CaptureValidator.latest
    if validator is None or len(validator.per_image) != 61:
        count = 0 if validator is None else len(validator.per_image)
        raise RuntimeError(f"expected 61 captured images for {path}, got {count}")
    return validator.per_image


def evaluate_weight(arm: str, weight: str, folds: list[list[str]], all_names: set[str]):
    folder = RUNS / arm / weight
    ckpts = checkpoints(folder)
    if 300 not in ckpts or len(ckpts) < 30:
        return {"error": f"incomplete run: {folder} ({len(ckpts)} checkpoints)"}, None

    stats = {}
    for epoch, path in ckpts.items():
        print(f"  {weight} epoch {epoch:>3}", flush=True)
        stats[epoch] = infer_checkpoint(path, f"{arm}_{weight}_e{epoch}")

    full_curve = {epoch: aggregate(rows, all_names) for epoch, rows in stats.items()}
    deployment_epoch, deployment_smooth = select_epoch(full_curve)
    oof_rows = {}
    fold_results = []
    for fold_id, heldout in enumerate(folds):
        heldout_set = set(heldout)
        selection_names = all_names - heldout_set
        selection_curve = {epoch: aggregate(rows, selection_names) for epoch, rows in stats.items()}
        selected_epoch, _ = select_epoch(selection_curve)
        oof_rows.update({name: stats[selected_epoch][name] for name in heldout})
        fold_results.append({
            "fold": fold_id,
            "n_selection": len(selection_names),
            "n_heldout": len(heldout),
            "selected_epoch": selected_epoch,
            "heldout_diagnostic": aggregate(stats[selected_epoch], heldout_set),
        })

    record = {
        "fixed_endpoint": {"epoch": 300, "metrics": full_curve[300]},
        "cross_fitted": {
            "official_pooled_oof_metrics": aggregate(oof_rows, all_names),
            "folds": fold_results,
        },
        "deployment": {
            "selected_epoch": deployment_epoch,
            "development_metrics": full_curve[deployment_epoch],
            "selection_rule": "max centered 3-point-smoothed mAP50-95; ties -> earlier epoch",
        },
        "full_dev_curve": [
            {"epoch": epoch, **full_curve[epoch], "smoothed_mAP50-95": round(deployment_smooth[epoch], 6)}
            for epoch in sorted(full_curve)
        ],
    }
    return record, stats


def joint_model_selection(weight_stats, folds, all_names):
    oof_rows = {}
    fold_results = []
    for fold_id, heldout in enumerate(folds):
        heldout_set = set(heldout)
        selection_names = all_names - heldout_set
        candidates = []
        for weight in WEIGHTS:
            stats = weight_stats.get(weight)
            if not stats:
                continue
            curve = {epoch: aggregate(rows, selection_names) for epoch, rows in stats.items()}
            epoch, smoothed = select_epoch(curve)
            candidates.append((smoothed[epoch], -epoch, -WEIGHTS.index(weight), weight, epoch))
        if not candidates:
            return {"error": "no complete detector runs"}
        _, _, _, weight, epoch = max(candidates)
        oof_rows.update({name: weight_stats[weight][epoch][name] for name in heldout})
        fold_results.append({
            "fold": fold_id,
            "selected_detector": weight,
            "selected_epoch": epoch,
            "heldout_diagnostic": aggregate(weight_stats[weight][epoch], heldout_set),
        })

    deployment_candidates = []
    for weight in WEIGHTS:
        stats = weight_stats.get(weight)
        if not stats:
            continue
        curve = {epoch: aggregate(rows, all_names) for epoch, rows in stats.items()}
        epoch, smoothed = select_epoch(curve)
        deployment_candidates.append((smoothed[epoch], -epoch, -WEIGHTS.index(weight), weight, epoch, curve[epoch]))
    _, _, _, weight, epoch, dev_metrics = max(deployment_candidates)
    return {
        "cross_fitted_model_selection": {
            "official_pooled_oof_metrics": aggregate(oof_rows, all_names),
            "folds": fold_results,
        },
        "deployment_model": {
            "detector": weight,
            "epoch": epoch,
            "development_metrics": dev_metrics,
            "warning": "development score; not a generalization estimate",
        },
    }


def run_arm(arm: str, folds: list[list[str]], all_names: set[str]) -> dict:
    output = {"arm": arm, "label": ARM_LABELS[arm], "train_images": TRAIN_SIZES[arm], "detectors": {}}
    weight_stats = {}
    for weight in WEIGHTS:
        record, stats = evaluate_weight(arm, weight, folds, all_names)
        output["detectors"][weight] = record
        if stats is not None:
            weight_stats[weight] = stats
    output["joint_detector_and_checkpoint_selection"] = joint_model_selection(weight_stats, folds, all_names)
    return output


def protocol_record(folds: list[list[str]]) -> dict:
    return {
        "version": "v4",
        "status": "pre-registered before formal v4 results",
        "development_set": "dev61 (61 independently sourced web images; 30 positive, 31 empty)",
        "outer_folds": N_FOLDS,
        "fold_seed": FOLD_SEED,
        "stratification": "non-empty vs empty label file; no source-group metadata available",
        "grouping_precondition": "dev61 internal thumbnail check must have zero pairs above 0.90",
        "checkpoint_candidates": "epoch 10, 20, ..., 300",
        "selection": "centered 3-point-smoothed mAP50-95; earlier epoch on ties",
        "detector_tie_break": WEIGHTS,
        "official_cross_fitted_metric": "AP computed once after pooling all held-out image predictions",
        "fold_metrics": "diagnostic only; never average fold mAP as the official score",
        "folds": folds,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", default="all", choices=[*ARM_LABELS, "all"])
    parser.add_argument("--protocol-only", action="store_true", help="write the pre-registered fold definition only")
    args = parser.parse_args()

    images = [Path(line.strip()) for line in DEV_LIST.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    assert len(images) == 61 and len({p.name for p in images}) == 61
    folds = build_folds(images)
    all_names = {path.name for path in images}
    arms = MAIN_ARMS if args.arm == "all" else [args.arm]
    protocol = protocol_record(folds)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    protocol_path = OUT_DIR / "protocol.json"
    protocol_path.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.protocol_only:
        print(f"saved -> {protocol_path}")
        return
    result = {
        "protocol": protocol,
        "arms": {},
    }
    for arm in arms:
        print(f"== {arm} ==", flush=True)
        result["arms"][arm] = run_arm(arm, folds, all_names)
        partial = OUT_DIR / f"v4_protocol_{arm}.json"
        partial.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"saved checkpoint -> {partial}", flush=True)
    out = OUT_DIR / ("v4_protocol_all.json" if args.arm == "all" else f"v4_protocol_{args.arm}.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"saved -> {out}", flush=True)


if __name__ == "__main__":
    main()
