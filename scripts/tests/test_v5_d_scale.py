"""D493 execution gates, sampling and output isolation; no detector is instantiated."""
import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_v5_d_scale as prep
import run_v5_d_scale as runner
import eval_v5_d_scale as evaluation
from ultralytics.cfg import get_cfg
from test_v5_d import temporary_workspace


class DScaleTests(unittest.TestCase):
    def setUp(self):
        self.restore = []
        for module, names in [(runner.training, ["OUT", "ARM", "RUNS", "LOGS", "train_args"]),
                              (evaluation.inference, ["OUT", "ARM", "RAW"]),
                              (evaluation.ev, ["infer_checkpoint"]),
                              (evaluation.bp, ["load_cache", "official_arm", "OUT_DIR"])]:
            self.restore += [(module, name, getattr(module, name)) for name in names]

    def tearDown(self):
        for module, name, value in self.restore:
            setattr(module, name, value)

    def test_default_launcher_does_not_execute_or_change_status(self):
        before = prep.sha(prep.OUT / "execution.json")
        with patch.object(sys, "argv", ["run_v5_d_scale.py"]), patch.object(runner, "check"), \
             patch.object(runner.training, "run_logged") as launch, patch.object(runner.training, "worker") as worker, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            runner.main()
        launch.assert_not_called()
        worker.assert_not_called()
        self.assertIn("PLAN ONLY", output.getvalue())
        self.assertEqual(before, prep.sha(prep.OUT / "execution.json"))

    def test_worker_requires_execute(self):
        with patch.object(sys, "argv", ["run_v5_d_scale.py", "--worker", "yolov8s"]), \
             patch.object(runner.training, "worker") as worker:
            with self.assertRaisesRegex(RuntimeError, "requires --execute"):
                runner.main()
        worker.assert_not_called()

    def test_evaluation_default_cannot_infer_or_bootstrap(self):
        with patch.object(sys, "argv", ["eval_v5_d_scale.py"]), patch.object(evaluation, "evaluate") as evaluate, \
             patch.object(evaluation, "bootstrap") as bootstrap, contextlib.redirect_stdout(io.StringIO()):
            evaluation.main()
        evaluate.assert_not_called()
        bootstrap.assert_not_called()

    def test_draw_is_unique_reproducible_and_ignores_labels_and_order(self):
        records = prep.read(prep.parent.OUT / "input_manifest.json")["images"]
        selected = [r["image"] for r in prep.sample_records(records)]
        changed = [{**r, "boxes": 999, "source_set": "arbitrary"} for r in reversed(records)]
        self.assertEqual(selected, [r["image"] for r in prep.sample_records(changed)])
        self.assertEqual(len(set(selected)), 493)
        self.assertEqual(set(selected), {r["image"] for r in prep.read(prep.OUT / "input_manifest.json")["images"]})

    def test_six_configs_align_and_training_outputs_are_isolated(self):
        runner.configure_training()
        for w in prep.WEIGHTS:
            frozen = runner.train_args(w)
            self.assertEqual(frozen, prep.aligned_args(w))
            cfg = get_cfg(overrides=frozen)
            self.assertEqual((cfg.epochs, cfg.imgsz, cfg.batch, cfg.seed, cfg.patience, cfg.save_period), (300, 640, 16, 0, 0, 10))
            self.assertEqual(cfg.data, str(prep.OUT / "data_D493.yaml"))
            paths = runner.training.checkpoint_paths(w)
            self.assertEqual(len(paths), 30)
            self.assertTrue(all(p.is_relative_to(prep.RUNS) for p in paths))
        self.assertNotIn("test:", prep.config_text())
        self.assertEqual(runner.training.OUT, prep.OUT)
        self.assertEqual(prep.parent.OUT, prep.ROOT / "experiments/v5_d")

    def test_bootstrap_is_full_minus_subset_and_13_targets(self):
        with temporary_workspace() as tmp:
            result, cache = tmp / "result.json", tmp / "cache.json"
            result.write_text('{"input_manifest_sha256":"frozen"}')
            cache.write_text('{}')
            def fake_boot(arms, args):
                self.assertEqual(arms, [prep.ARM, prep.parent.ARM])
                self.assertEqual((args.n_boot, args.targets), (10000, "all"))
                targets = [("joint", None)] + [(t, w) for t in ("fixed_endpoint", "oof") for w in prep.WEIGHTS]
                prep.write_json(args.out, {"comparisons": [{"target": t, "detector": w} for t, w in targets]})
            with patch.object(evaluation, "OUT", tmp), patch.object(evaluation, "RESULT", result), \
                 patch.object(evaluation, "CACHE", cache), patch.object(evaluation, "sha", return_value="frozen"), \
                 patch.object(evaluation, "load_cache", return_value={"input_manifest_sha256": "frozen"}), \
                 patch.object(evaluation.bp, "boot", side_effect=fake_boot) as boot:
                evaluation.bootstrap()
                evaluation.bootstrap()  # complete provenance-matched statistics are not repeated
            self.assertEqual(boot.call_count, 1)
            self.assertEqual(len(prep.read(tmp / "bootstrap_D1085_minus_D493.json")["comparisons"]), 13)

    def test_cached_inference_uses_scale_provenance_and_rejects_stale(self):
        with temporary_workspace() as tmp, patch.object(evaluation.inference, "RAW", tmp), \
             patch.object(evaluation.inference, "OUT", prep.OUT), patch.object(evaluation.inference, "sha", return_value="new"), \
             patch("ultralytics.YOLO") as model:
            prep.write_json(tmp / "test.json", {"provenance": {"checkpoint_sha256": "old"}})
            with self.assertRaisesRegex(RuntimeError, "Stale inference cache"):
                evaluation.inference.cached_inference(Path("dummy.pt"), "test")
            model.assert_not_called()

    def test_evaluator_reproduces_accepted_selection_from_saved_predictions(self):
        # Feed accepted D1085 prediction arrays through the D493 evaluator to check
        # the adapter, without training or inferring D493 or writing real results.
        full_runs = prep.ROOT / "runs/detect" / prep.parent.ARM
        checkpoints = {w: evaluation.ev.checkpoints(full_runs / w) for w in prep.WEIGHTS}
        accepted = prep.read(prep.parent.OUT / f"v5_protocol_{prep.parent.ARM}.json")["arms"][prep.parent.ARM]
        def saved_inference(path, tag):
            weight = path.parent.parent.name
            epoch = next(e for e, p in checkpoints[weight].items() if p == path)
            rows = prep.read(full_runs / "eval_cache" / f"{prep.parent.ARM}_{weight}_e{epoch}.json")["rows"]
            return {n: evaluation.bp.dec_row(r) for n, r in rows.items()}
        with temporary_workspace() as tmp, patch.object(evaluation, "OUT", tmp), \
             patch.object(evaluation, "RESULT", tmp / "result.json"), patch.object(evaluation, "CACHE", tmp / "cache.json"), \
             patch.object(evaluation, "configure_training"), patch.object(runner.training, "is_complete", return_value=True), \
             patch.object(runner.training, "checkpoint_paths", side_effect=lambda w: list(checkpoints[w].values())), \
             patch.object(evaluation.ev, "checkpoints", side_effect=lambda folder: checkpoints[folder.name]), \
             patch.object(evaluation.inference, "cached_inference", side_effect=saved_inference) as infer, \
             contextlib.redirect_stdout(io.StringIO()):
            prep.write_json(tmp / "input_manifest.json", {})
            evaluation.evaluate(prep.read(prep.OUT / "input_manifest.json"))
            actual = prep.read(tmp / "result.json")["arms"][prep.ARM]
            self.assertEqual((actual["label"], actual["train_images"]), ("D_LoRA493", 493))
            self.assertEqual(actual["joint_detector_and_checkpoint_selection"], accepted["joint_detector_and_checkpoint_selection"])
            for w in prep.WEIGHTS:
                for key in ("fixed_endpoint", "cross_fitted", "deployment", "full_dev_curve", "non_convergent"):
                    self.assertEqual(actual["detectors"][w][key], accepted["detectors"][w][key])
            self.assertEqual(infer.call_count, 180)


if __name__ == "__main__":
    unittest.main()
