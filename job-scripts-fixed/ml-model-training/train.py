#!/usr/bin/env python3
"""
ML Model Training Job
Container Image: python:3.12-slim
Command: python train.py --input /data/train.csv --output /reports/model.pkl --label-col target
Tags: cpu, training

Trains a scikit-learn classifier/regressor and writes the pickled model
+ training metrics to the output directory.
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
    p = argparse.ArgumentParser(description="Train a scikit-learn model")
    p.add_argument("--input", required=True, help="CSV with features + label column")
    p.add_argument("--output", required=True, help="Output .pkl model file path")
    p.add_argument("--label-col", default="label", help="Label/target column name")
    p.add_argument("--task", choices=["auto", "classification", "regression"], default="auto")
    p.add_argument("--model", choices=["rf", "lr", "gbm"], default="rf",
                   help="rf=RandomForest, lr=LinearModel, gbm=GradientBoosting")
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--random-state", type=int, default=42)
    return p.parse_args()


def load_csv(path, label_col):
    with open(path, encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"[ERROR] {path} is empty")
        sys.exit(1)
    if label_col not in rows[0]:
        print(f"[ERROR] Label column '{label_col}' not found. Available: {list(rows[0].keys())}")
        sys.exit(1)
    feature_cols = [c for c in rows[0].keys() if c != label_col]

    def coerce(v):
        if v in ("", None):
            return 0.0
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    X = np.array([[coerce(r.get(c)) for c in feature_cols] for r in rows])
    y_raw = [r.get(label_col) for r in rows]
    return X, y_raw, feature_cols


def detect_task(y_raw):
    """Classification if all labels are integers (or strings), else regression."""
    try:
        nums = [float(v) for v in y_raw if v not in ("", None)]
        if all(n.is_integer() for n in nums) and len(set(nums)) <= 20:
            return "classification"
        return "regression"
    except (ValueError, TypeError):
        return "classification"


def build_model(kind, task):
    if kind == "rf":
        if task == "classification":
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(n_estimators=100, random_state=42)
        from sklearn.ensemble import RandomForestRegressor
        return RandomForestRegressor(n_estimators=100, random_state=42)
    if kind == "lr":
        if task == "classification":
            from sklearn.linear_model import LogisticRegression
            return LogisticRegression(max_iter=1000)
        from sklearn.linear_model import LinearRegression
        return LinearRegression()
    if kind == "gbm":
        if task == "classification":
            from sklearn.ensemble import GradientBoostingClassifier
            return GradientBoostingClassifier(random_state=42)
        from sklearn.ensemble import GradientBoostingRegressor
        return GradientBoostingRegressor(random_state=42)


def main():
    args = parse_args()
    print(f"[INFO] Input={args.input} Output={args.output} Task={args.task}")

    X, y_raw, feature_cols = load_csv(args.input, args.label_col)
    print(f"[INFO] Loaded X={X.shape}, y={len(y_raw)}")

    task = args.task if args.task != "auto" else detect_task(y_raw)
    print(f"[INFO] Task type: {task}")

    # Encode labels for classification
    if task == "classification":
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        y = le.fit_transform(y_raw)
    else:
        y = np.array([float(v) for v in y_raw])
        le = None

    # Split
    from sklearn.model_selection import train_test_split
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state
    )
    print(f"[INFO] Train={len(X_tr)} Test={len(X_te)}")

    # Train
    try:
        model = build_model(args.model, task)
        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)
    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Metrics
    metrics = {}
    if task == "classification":
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        metrics["accuracy"] = float(accuracy_score(y_te, preds))
        p, r, f, _ = precision_recall_fscore_support(y_te, preds, average="weighted", zero_division=0)
        metrics["precision"] = float(p)
        metrics["recall"] = float(r)
        metrics["f1"] = float(f)
    else:
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        metrics["mse"] = float(mean_squared_error(y_te, preds))
        metrics["mae"] = float(mean_absolute_error(y_te, preds))
        metrics["r2"] = float(r2_score(y_te, preds))
    print(f"[INFO] Metrics: {metrics}")

    # Save
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "wb") as f:
        pickle.dump(model, f)
    print(f"[INFO] Model → {args.output}")

    meta = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "algorithm": args.model,
        "feature_cols": feature_cols,
        "label_col": args.label_col,
        "label_classes": le.classes_.tolist() if le else None,
        "train_size": int(len(X_tr)),
        "test_size": int(len(X_te)),
        "metrics": metrics,
    }
    meta_path = args.output.rsplit(".", 1)[0] + "_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, default=str)
    print(f"[INFO] Metadata → {meta_path}")


if __name__ == "__main__":
    main()
