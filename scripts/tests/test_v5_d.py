"""Offline safety checks; never constructs a detector or invokes training/inference."""
import contextlib
import io
import json
from pathlib import Path
import sys
import shutil
import uuid
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_v5_d as prep
import run_v5_d as runner
import eval_v5_d as evaluation
from ultralytics.cfg import get_cfg


@contextlib.contextmanager
def temporary_workspace():
    root = (prep.ROOT / ".tmp").resolve()
    path = root / f"v5_test_{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        assert path.resolve().parent == root and path.name.startswith("v5_test_")
        shutil.rmtree(path)


class DPreparationTests(unittest.TestCase):
    def test_default_launcher_cannot_start_work(self):
        with patch.object(sys, "argv", ["run_v5_d.py"]), patch.object(runner, "check"), \
             patch.object(runner, "run_logged") as launch, patch.object(runner, "worker") as worker, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            runner.main()
        launch.assert_not_called()
        worker.assert_not_called()
        self.assertIn("PLAN ONLY", output.getvalue())

    def test_worker_requires_execute(self):
        with patch.object(sys, "argv", ["run_v5_d.py", "--worker", "yolov8s"]), \
             patch.object(runner, "worker") as worker:
            with self.assertRaisesRegex(RuntimeError, "requires --execute"):
                runner.main()
        worker.assert_not_called()

    def test_batch_guard_before_epoch_exists_and_oom_limit(self):
        with temporary_workspace() as tmp:
            trainer = SimpleNamespace(batch_size=16, start_epoch=0)
            events = []
            runner.record_batch(trainer, events, tmp / "batch.json")
            self.assertEqual(events[0]["epoch_internal"], 0)
            trainer.batch_size = 8
            runner.record_batch(trainer, events, tmp / "batch.json")
            self.assertEqual([e["batch"] for e in events], [16, 8])
            trainer.batch_size = 4
            with self.assertRaisesRegex(RuntimeError, "only batch 16 or 8"):
                runner.record_batch(trainer, events, tmp / "batch.json")

    def test_eval_default_cannot_infer(self):
        with patch.object(sys, "argv", ["eval_v5_d.py"]), \
             patch.object(evaluation, "evaluate") as evaluate, patch.object(evaluation, "bootstrap") as bootstrap, \
             contextlib.redirect_stdout(io.StringIO()):
            evaluation.main()
        evaluate.assert_not_called()
        bootstrap.assert_not_called()

    def test_all_six_configs_are_valid_and_preserve_protocol(self):
        for weight in runner.WEIGHTS:
            cfg = get_cfg(overrides=runner.train_args(weight))
            self.assertEqual((cfg.epochs, cfg.batch, cfg.seed, cfg.save_period, cfg.patience, cfg.close_mosaic),
                             (300, 16, 0, 10, 0, 10))
            self.assertEqual(cfg.project, str(runner.RUNS))
            self.assertEqual(cfg.name, weight)
            self.assertEqual(cfg.data, str(prep.OUT / "data_D1085.yaml"))
        self.assertNotIn("test:", prep.config_text())

    def test_labels_allow_empty_but_reject_invalid_boxes(self):
        with temporary_workspace() as tmp:
            label = Path(tmp) / "test.txt"
            for text, count in [("", 0), ("0 0.5 0.5 1 1\n", 1)]:
                label.write_text(text)
                self.assertEqual(prep.label_count(label), count)
            for text in ["1 0.5 0.5 1 1", "0 nan 0.5 1 1", "0 0.1 0.5 1 1", "0 0.5 0.5 0 1",
                         "0 0.5 0.5 1 1\n0 0.5 0.5 1 1"]:
                label.write_text(text)
                with self.assertRaises(RuntimeError):
                    prep.label_count(label)

    def test_snapshot_mapping_matches_v4_and_rejects_missing(self):
        with temporary_workspace() as tmp, patch.object(runner, "RUNS", Path(tmp)):
            folder = Path(tmp) / "yolov8s"
            (folder / "weights").mkdir(parents=True)
            for p in runner.checkpoint_paths("yolov8s"):
                with p.open("wb") as f:
                    f.truncate(1000001)
            (folder / "results.csv").write_text("epoch\n" + "\n".join(map(str, range(1, 301))))
            runner.validate_finished("yolov8s")
            self.assertEqual(set(evaluation.ev.checkpoints(folder)), set(range(10, 301, 10)))
            (folder / "weights/epoch10.pt").unlink()
            with self.assertRaisesRegex(RuntimeError, "snapshot"):
                runner.validate_finished("yolov8s")

    def test_stale_prediction_cache_stops_before_model_load(self):
        with temporary_workspace() as tmp, patch.object(evaluation, "RAW", Path(tmp)), \
             patch.object(evaluation, "sha", return_value="current"), patch("ultralytics.YOLO") as yolo:
            (Path(tmp) / "test.json").write_text(json.dumps({"provenance": {"checkpoint_sha256": "old"}}))
            with self.assertRaisesRegex(RuntimeError, "Stale inference cache"):
                evaluation.cached_inference(Path("dummy.pt"), "test")
            yolo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
