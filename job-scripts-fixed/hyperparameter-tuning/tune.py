#!/usr/bin/env python3
"""
Hyperparameter Tuning Job
Container Image: python:3.12-slim
Command: python tune.py --input /data/train.csv --output /reports --label-col target --trials 20
Tags: cpu, training

GridSearchCV-based hyperparameter search over a small param grid.
Writes best_params.json + metrics.json + best_model.pkl.
"""

import argparse
import csv
import json
import os
import pickle
import sys
import traceback
from datetime import datetime

import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description="Hyperparameter tuning via GridSearchCV")
    p.add_argument("--input", required=True, help="Training CSV")
    p.add_argument("--output", required=True, help="Output directory for best model + metrics")
    p.add_argument("--label-col", default="target")
    p.add_argument("--task", choices=["auto", "classification", "regression"], default="auto")
    p.add_argument("--trials", type=int, default=20, help="Max combinations to search")
    p.add_argument("--cv", type=int, default=3, help="CV folds")
    return p.parse_args()


def load(path, label_col):
    with open(path, encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("[ERROR] empty input"); sys.exit(1)
    if label_col not in rows[0]:
        print(f"[ERROR] label '{label_col}' missing. Cols={list(rows[0].keys())}"); sys.exit(1)
    feats = [c for c in rows[0].keys() if c != label_col]

    def coerce(v):
        try:
            return float(v) if v not in ("", None) else 0.0
        except (ValueError, TypeError):
            return 0.0

    X = np.array([[coerce(r.get(c)) for c in feats] for r in rows])
    y = [r.get(label_col) for r in rows]
    return X, y, feats


def main():
    args = parse_args()
    print(f"[INFO] Input={args.input} Trials={args.trials} CV={args.cv}")

    X, y_raw, feats = load(args.input, args.label_col)
    print(f"[INFO] X={X.shape}, y={len(y_raw)}, features={feats}")

    # Detect task
    task = args.task
    if task == "auto":
        try:
            nums = [float(v) for v in y_raw if v not in ("", None)]
            task = "classification" if all(n.is_integer() for n in nums) and len(set(nums)) <= 20 else "regression"
        except (ValueError, TypeError):
            task = "classification"
    print(f"[INFO] Task={task}")

    # Encode classification labels
    if task == "classification":
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        y = le.fit_transform(y_raw)
    else:
        y = np.array([float(v) for v in y_raw])
        le = None

    # Model + grid
    from sklearn.model_selection import GridSearchCV
    if task == "classification":
        from sklearn.ensemble import RandomForestClassifier
        estimator = RandomForestClassifier(random_state=42)
        grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 5, 10, 20],
            "min_samples_split": [2, 5],
        }
        scoring = "accuracy"
    else:
        from sklearn.ensemble import RandomForestRegressor
        estimator = RandomForestRegressor(random_state=42)
        grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 5, 10, 20],
            "min_samples_split": [2, 5],
        }
        scoring = "r2"

    # Cap search size by --trials
    from itertools import product
    all_combos = list(product(*grid.values()))
    if len(all_combos) > args.trials:
        print(f"[INFO] Sampling {args.trials} of {len(all_combos)} combinations")
        import random
        random.seed(42)
        sampled = random.sample(all_combos, args.trials)
        grid = {k: list({s[i] for s in sampled}) for i, k in enumerate(grid.keys())}
        print(f"[INFO] Reduced grid: {grid}")

    try:
        gs = GridSearchCV(estimator, grid, cv=args.cv, scoring=scoring, n_jobs=1, verbose=1)
        gs.fit(X, y)
    except Exception as e:
        print(f"[ERROR] GridSearch failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    print(f"[INFO] Best {scoring}: {gs.best_score_:.4f}")
    print(f"[INFO] Best params: {gs.best_params_}")

    # Save
    os.makedirs(args.output, exist_ok=True)
    with open(os.path.join(args.output, "best_model.pkl"), "wb") as f:
        pickle.dump(gs.best_estimator_, f)

    # All results
    all_runs = []
    for i, (params, score) in enumerate(zip(gs.cv_results_["params"], gs.cv_results_["mean_test_score"])):
        all_runs.append({"trial": i, "params": params, "score": float(score)})
    all_runs.sort(key=lambda r: -r["score"])

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "best_score": float(gs.best_score_),
        "best_params": gs.best_params_,
        "scoring": scoring,
        "total_trials": len(gs.cv_results_["params"]),
        "features": feats,
        "top_trials": all_runs[:10],
    }
    with open(os.path.join(args.output, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    with open(os.path.join(args.output, "best_params.json"), "w") as f:
        json.dump(gs.best_params_, f, indent=2, default=str)

    print(f"[INFO] Wrote best_model.pkl, metrics.json, best_params.json → {args.output}")


if __name__ == "__main__":
    main()
