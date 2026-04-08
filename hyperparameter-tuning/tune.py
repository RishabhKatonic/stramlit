#!/usr/bin/env python3
"""
Hyperparameter Tuning Job
Container Image: GPU-enabled Python image (user-defined)
Command: python tune.py --search random --max-trials 20
Tags: gpu, parallel, advanced, GPU
"""

import argparse
import itertools
import json
import math
import os
import random
import sys
import time
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Hyperparameter tuning")
    parser.add_argument("--search", choices=["grid", "random"], default="random", help="Search method")
    parser.add_argument("--max-trials", type=int, default=20, help="Maximum number of trials")
    parser.add_argument("--patience", type=int, default=3, help="Early stopping patience")
    parser.add_argument("--config", default=None, help="Path to search space JSON config")
    parser.add_argument("--output", default="/tmp/tuning_results", help="Output directory")
    return parser.parse_args()


DEFAULT_SEARCH_SPACE = {
    "learning_rate": {"type": "log_uniform", "min": 1e-5, "max": 1e-1},
    "dropout": {"type": "uniform", "min": 0.0, "max": 0.5},
    "hidden_size": {"type": "categorical", "values": [64, 128, 256, 512]},
    "batch_size": {"type": "categorical", "values": [32, 64]},
    "optimizer": {"type": "categorical", "values": ["adam", "sgd", "rmsprop", "adamw"]},
}


def load_search_space(config_path):
    """Load search space from config file or use defaults."""
    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            space = json.load(f)
        print(f"[INFO] Loaded search space from {config_path}")
        return space
    print("[INFO] Using default search space")
    return DEFAULT_SEARCH_SPACE


def sample_params(space):
    """Sample a single set of hyperparameters from the search space."""
    params = {}
    for name, spec in space.items():
        if spec["type"] == "categorical":
            params[name] = random.choice(spec["values"])
        elif spec["type"] == "uniform":
            params[name] = round(random.uniform(spec["min"], spec["max"]), 6)
        elif spec["type"] == "log_uniform":
            log_val = random.uniform(math.log10(spec["min"]), math.log10(spec["max"]))
            params[name] = round(10 ** log_val, 8)
    return params


def generate_grid(space):
    """Generate all combinations for grid search."""
    grid_values = {}
    for name, spec in space.items():
        if spec["type"] == "categorical":
            grid_values[name] = spec["values"]
        elif spec["type"] in ("uniform", "log_uniform"):
            # Sample 3 points for continuous params
            grid_values[name] = [spec["min"], (spec["min"] + spec["max"]) / 2, spec["max"]]

    keys = list(grid_values.keys())
    combos = list(itertools.product(*[grid_values[k] for k in keys]))
    return [dict(zip(keys, combo)) for combo in combos]


def run_trial(trial_id, params, patience=3):
    """
    Run a single training trial with the given hyperparameters.
    Replace with actual training code.
    """
    lr = params.get("learning_rate", 0.01)
    epochs = 20  # fixed per trial
    losses = []
    best_loss = float("inf")
    no_improve = 0

    for epoch in range(epochs):
        # Simulated loss — lower lr generally converges slower but better
        noise = random.uniform(-0.05, 0.05)
        loss = 1.0 / (1.0 + 0.5 * epoch * math.sqrt(lr)) + noise + random.uniform(0, 0.2)
        loss = max(0.05, loss)
        losses.append(loss)

        if loss < best_loss:
            best_loss = loss
            no_improve = 0
        else:
            no_improve += 1

        # Early stopping / pruning
        if no_improve >= patience:
            return {
                "trial_id": trial_id,
                "params": params,
                "metrics": {"val_loss": round(best_loss, 4), "val_accuracy": round(1 - best_loss, 4)},
                "status": "PRUNED",
                "stopped_at_epoch": epoch + 1,
                "duration_seconds": epoch + 1,
            }

    return {
        "trial_id": trial_id,
        "params": params,
        "metrics": {"val_loss": round(best_loss, 4), "val_accuracy": round(1 - best_loss, 4)},
        "status": "COMPLETED",
        "stopped_at_epoch": epochs,
        "duration_seconds": epochs,
    }


def should_prune_median(current_loss, completed_trials):
    """Median pruning: prune if current trial worse than median of completed."""
    if len(completed_trials) < 3:
        return False
    completed_losses = sorted(t["metrics"]["val_loss"] for t in completed_trials if t["status"] == "COMPLETED")
    if not completed_losses:
        return False
    median = completed_losses[len(completed_losses) // 2]
    return current_loss > median


def main():
    args = parse_args()
    max_parallel = int(os.environ.get("MAX_PARALLEL_TRIALS", "1"))
    gpu_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "cpu")

    print(f"[INFO] Search method:    {args.search}")
    print(f"[INFO] Max trials:       {args.max_trials}")
    print(f"[INFO] Patience:         {args.patience}")
    print(f"[INFO] Parallel trials:  {max_parallel}")
    print(f"[INFO] GPU devices:      {gpu_devices}")

    space = load_search_space(args.config)

    # Generate trial parameter sets
    if args.search == "grid":
        all_params = generate_grid(space)
        if len(all_params) > args.max_trials:
            all_params = all_params[: args.max_trials]
        print(f"[INFO] Grid search: {len(all_params)} combinations")
    else:
        all_params = [sample_params(space) for _ in range(args.max_trials)]
        print(f"[INFO] Random search: {len(all_params)} trials")

    # Run trials
    trials = []
    for i, params in enumerate(all_params):
        print(f"\n[Trial {i + 1}/{len(all_params)}] params={params}")
        result = run_trial(trial_id=i + 1, params=params, patience=args.patience)
        trials.append(result)
        status = result["status"]
        val_loss = result["metrics"]["val_loss"]
        print(f"[Trial {i + 1}] status={status} val_loss={val_loss:.4f}")

    # Find best trial
    completed = [t for t in trials if t["status"] == "COMPLETED"]
    pruned = [t for t in trials if t["status"] == "PRUNED"]
    failed = [t for t in trials if t["status"] == "FAILED"]

    if completed:
        best = min(completed, key=lambda t: t["metrics"]["val_loss"])
    elif pruned:
        best = min(pruned, key=lambda t: t["metrics"]["val_loss"])
    else:
        best = None

    # Build summary
    summary = {
        "total_trials": len(trials),
        "completed": len(completed),
        "failed": len(failed),
        "pruned": len(pruned),
        "best_trial": best,
        "search_method": args.search,
        "objective": "minimize val_loss",
    }

    # Write results
    os.makedirs(args.output, exist_ok=True)

    results_path = os.path.join(args.output, "tuning_results.json")
    with open(results_path, "w") as f:
        json.dump(summary, f, indent=2)

    trials_log_path = os.path.join(args.output, "trials.jsonl")
    with open(trials_log_path, "w") as f:
        for trial in trials:
            f.write(json.dumps(trial) + "\n")

    # Leaderboard
    leaderboard = sorted(
        [t for t in trials if t["metrics"].get("val_loss") is not None],
        key=lambda t: t["metrics"]["val_loss"],
    )

    # Print summary
    print(f"\n{'='*60}")
    print(f"Hyperparameter Tuning Results — {args.search} search")
    print(f"{'='*60}")
    print(f"Total trials: {len(trials)}")
    print(f"Completed:    {len(completed)}")
    print(f"Pruned:       {len(pruned)}")
    print(f"Failed:       {len(failed)}")
    if best:
        print(f"\nBest trial #{best['trial_id']}:")
        print(f"  val_loss:   {best['metrics']['val_loss']:.4f}")
        print(f"  params:     {best['params']}")
    print(f"\nTop 5 leaderboard:")
    for rank, trial in enumerate(leaderboard[:5], 1):
        print(f"  {rank}. trial #{trial['trial_id']} val_loss={trial['metrics']['val_loss']:.4f}")
    print(f"\nResults: {results_path}")
    print(f"Trials:  {trials_log_path}")
    print("[INFO] Done")


if __name__ == "__main__":
    main()
