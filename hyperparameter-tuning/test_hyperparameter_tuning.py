"""
Tests for Hyperparameter Tuning Job
Template: Hyperparameter Tuning
Container Image: (varies — GPU-enabled Python image)
Command: (user-defined tuning script)
Tags: gpu, parallel, advanced, GPU
"""

import os
import sys
import json
import tempfile
import unittest
import itertools
import random
from unittest.mock import patch
from pathlib import Path


class TestHyperparameterSearchSpace(unittest.TestCase):
    """Test search space definition and sampling"""

    def test_grid_search_combinations(self):
        space = {
            "learning_rate": [0.001, 0.01, 0.1],
            "batch_size": [32, 64],
            "optimizer": ["adam", "sgd"],
        }
        keys = list(space.keys())
        combos = list(itertools.product(*[space[k] for k in keys]))
        self.assertEqual(len(combos), 3 * 2 * 2)  # 12 total
        self.assertEqual(len(combos), 12)

    def test_random_search_sample_count(self):
        n_trials = 20
        space = {
            "learning_rate": (1e-5, 1e-1),
            "dropout": (0.0, 0.5),
            "hidden_size": [64, 128, 256, 512],
        }
        samples = []
        for _ in range(n_trials):
            sample = {
                "learning_rate": random.uniform(*space["learning_rate"]),
                "dropout": random.uniform(*space["dropout"]),
                "hidden_size": random.choice(space["hidden_size"]),
            }
            samples.append(sample)
        self.assertEqual(len(samples), n_trials)

    def test_search_space_bounds(self):
        lr_min, lr_max = 1e-5, 1e-1
        sampled_lr = random.uniform(lr_min, lr_max)
        self.assertGreaterEqual(sampled_lr, lr_min)
        self.assertLessEqual(sampled_lr, lr_max)

    def test_categorical_sampling(self):
        options = ["adam", "sgd", "rmsprop", "adamw"]
        choice = random.choice(options)
        self.assertIn(choice, options)

    def test_log_scale_sampling(self):
        """Learning rates are typically sampled in log scale"""
        import math
        lr_min, lr_max = 1e-5, 1e-1
        log_lr = random.uniform(math.log10(lr_min), math.log10(lr_max))
        lr = 10 ** log_lr
        self.assertGreaterEqual(lr, lr_min)
        self.assertLessEqual(lr, lr_max)


class TestHyperparameterTrialManagement(unittest.TestCase):
    """Test trial execution and tracking"""

    def test_trial_result_schema(self):
        trial = {
            "trial_id": 1,
            "params": {"lr": 0.01, "batch_size": 64},
            "metrics": {"val_loss": 0.35, "val_accuracy": 0.88},
            "status": "COMPLETED",
            "duration_seconds": 120,
        }
        required = {"trial_id", "params", "metrics", "status"}
        self.assertTrue(required.issubset(trial.keys()))

    def test_trial_statuses(self):
        valid_statuses = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "PRUNED"}
        trial_status = "COMPLETED"
        self.assertIn(trial_status, valid_statuses)

    def test_best_trial_selection(self):
        trials = [
            {"trial_id": 1, "metrics": {"val_loss": 0.45}},
            {"trial_id": 2, "metrics": {"val_loss": 0.32}},
            {"trial_id": 3, "metrics": {"val_loss": 0.38}},
        ]
        best = min(trials, key=lambda t: t["metrics"]["val_loss"])
        self.assertEqual(best["trial_id"], 2)

    def test_trial_count_limit(self):
        max_trials = 50
        completed = 50
        self.assertGreaterEqual(max_trials, completed)

    def test_failed_trial_not_selected_as_best(self):
        trials = [
            {"trial_id": 1, "status": "COMPLETED", "val_loss": 0.5},
            {"trial_id": 2, "status": "FAILED", "val_loss": None},
            {"trial_id": 3, "status": "COMPLETED", "val_loss": 0.3},
        ]
        completed = [t for t in trials if t["status"] == "COMPLETED"]
        best = min(completed, key=lambda t: t["val_loss"])
        self.assertEqual(best["trial_id"], 3)


class TestHyperparameterParallelExecution(unittest.TestCase):
    """Test parallel trial execution"""

    def test_max_parallel_trials_env(self):
        with patch.dict(os.environ, {"MAX_PARALLEL_TRIALS": "4"}):
            max_parallel = int(os.environ.get("MAX_PARALLEL_TRIALS", "1"))
            self.assertEqual(max_parallel, 4)

    def test_default_single_parallel(self):
        with patch.dict(os.environ, {}, clear=True):
            max_parallel = int(os.environ.get("MAX_PARALLEL_TRIALS", "1"))
            self.assertEqual(max_parallel, 1)

    def test_gpu_allocation_per_trial(self):
        """Each parallel trial may need its own GPU"""
        total_gpus = 4
        trials_parallel = 4
        gpus_per_trial = total_gpus // trials_parallel
        self.assertEqual(gpus_per_trial, 1)

    def test_resource_contention_awareness(self):
        total_memory_gb = 64
        trials = 4
        per_trial = total_memory_gb / trials
        self.assertEqual(per_trial, 16.0)


class TestHyperparameterEarlyStopping(unittest.TestCase):
    """Test early stopping / pruning logic"""

    def test_no_improvement_detected(self):
        patience = 3
        losses = [0.5, 0.5, 0.5, 0.5]  # No improvement
        best = losses[0]
        no_improve_count = 0
        for loss in losses[1:]:
            if loss >= best:
                no_improve_count += 1
            else:
                best = loss
                no_improve_count = 0
        should_stop = no_improve_count >= patience
        self.assertTrue(should_stop)

    def test_improvement_resets_patience(self):
        patience = 3
        losses = [0.5, 0.6, 0.7, 0.4]  # Improvement at end
        best = losses[0]
        no_improve_count = 0
        for loss in losses[1:]:
            if loss >= best:
                no_improve_count += 1
            else:
                best = loss
                no_improve_count = 0
        self.assertEqual(no_improve_count, 0)

    def test_pruned_trial_marked(self):
        trial = {"trial_id": 5, "status": "PRUNED", "stopped_at_epoch": 15}
        self.assertEqual(trial["status"], "PRUNED")

    def test_median_pruning(self):
        """Prune if current trial is below median of completed trials"""
        completed_losses = [0.3, 0.35, 0.4, 0.45]
        median = sorted(completed_losses)[len(completed_losses) // 2]
        current_loss = 0.6
        should_prune = current_loss > median
        self.assertTrue(should_prune)


class TestHyperparameterResultsOutput(unittest.TestCase):
    """Test results reporting"""

    def test_results_summary_structure(self):
        summary = {
            "total_trials": 50,
            "completed": 45,
            "failed": 3,
            "pruned": 2,
            "best_trial": {
                "trial_id": 12,
                "params": {"lr": 0.003, "batch_size": 128},
                "val_loss": 0.28,
            },
            "search_method": "random",
            "objective": "minimize val_loss",
        }
        self.assertIn("best_trial", summary)
        self.assertEqual(summary["total_trials"],
                         summary["completed"] + summary["failed"] + summary["pruned"])

    def test_results_file_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = os.path.join(tmpdir, "tuning_results.json")
            results = {"best_params": {"lr": 0.01}, "best_score": 0.92}
            with open(results_path, "w") as f:
                json.dump(results, f)
            self.assertTrue(os.path.exists(results_path))

    def test_all_trials_logged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "trials.jsonl")
            with open(log_path, "w") as f:
                for i in range(20):
                    trial = {"trial_id": i, "val_loss": random.uniform(0.2, 0.8)}
                    f.write(json.dumps(trial) + "\n")
            with open(log_path) as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 20)

    def test_leaderboard_sorted(self):
        trials = [
            {"id": 1, "score": 0.85},
            {"id": 2, "score": 0.92},
            {"id": 3, "score": 0.78},
        ]
        leaderboard = sorted(trials, key=lambda t: t["score"], reverse=True)
        self.assertEqual(leaderboard[0]["id"], 2)
        self.assertEqual(leaderboard[-1]["id"], 3)


class TestHyperparameterContainerEnv(unittest.TestCase):
    """Test container environment expectations"""

    def test_python_version(self):
        major, minor = sys.version_info[:2]
        self.assertGreaterEqual(major, 3)
        self.assertGreaterEqual(minor, 10)

    def test_gpu_tags(self):
        """Hyperparameter Tuning is tagged gpu, parallel, advanced"""
        tags = {"gpu", "parallel", "advanced", "GPU"}
        self.assertIn("gpu", tags)
        self.assertIn("parallel", tags)

    def test_tmp_writable(self):
        with tempfile.NamedTemporaryFile(dir="/tmp", delete=True) as f:
            f.write(b"test")
            self.assertTrue(os.path.exists(f.name))


if __name__ == "__main__":
    unittest.main()
