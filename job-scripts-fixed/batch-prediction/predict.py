#!/usr/bin/env python3
"""
Batch Prediction Job
Container Image: python:3.12-slim
Command: python predict.py --model /data/model.pkl --input /data/inputs.csv --output /reports/predictions.csv
Tags: cpu, inference

Loads a pickled sklearn / cloudpickle model and runs batch prediction
over CSV rows. Writes predictions alongside the original features.
"""

import argparse
import csv
import json
import os
import pickle
import sys
import traceback
from datetime import datetime


def parse_args():
    p = argparse.ArgumentParser(description="Batch prediction over CSV/JSON")
    p.add_argument("--model", required=True, help="Path to .pkl model file")
    p.add_argument("--input", required=True, help="CSV/JSON with feature rows")
    p.add_argument("--output", required=True, help="Output CSV path")
    p.add_argument("--feature-cols", default="", help="Comma-separated feature columns (auto if empty)")
    p.add_argument("--batch-size", type=int, default=1000)
    return p.parse_args()


def load_model(path):
    print(f"[INFO] Loading model: {path}")
    with open(path, "rb") as f:
        # Try cloudpickle for models with embedded custom classes
        try:
            import cloudpickle
            model = cloudpickle.load(f)
        except ImportError:
            model = pickle.load(f)
    print(f"[INFO] Model type: {type(model).__name__}")
    if not hasattr(model, "predict"):
        print("[ERROR] Loaded object has no .predict() method")
        sys.exit(1)
    return model


def load_rows(path):
    if path.endswith(".json"):
        with open(path) as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def to_features(row, feature_cols):
    vals = []
    for c in feature_cols:
        v = row.get(c, 0)
        try:
            vals.append(float(v) if v not in ("", None) else 0.0)
        except (ValueError, TypeError):
            vals.append(0.0)
    return vals


def main():
    args = parse_args()
    model = load_model(args.model)

    rows = load_rows(args.input)
    print(f"[INFO] Loaded {len(rows)} input rows")
    if not rows:
        print("[ERROR] No rows to predict on")
        sys.exit(1)

    feature_cols = [c.strip() for c in args.feature_cols.split(",") if c.strip()]
    if not feature_cols:
        # Auto: every column except obvious label columns
        candidates = [c for c in rows[0].keys()
                      if c.lower() not in ("label", "target", "y", "class")]
        feature_cols = candidates
        print(f"[INFO] Auto-detected features: {feature_cols}")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    predictions = []
    total = len(rows)
    try:
        for i in range(0, total, args.batch_size):
            batch = rows[i:i + args.batch_size]
            X = [to_features(r, feature_cols) for r in batch]
            try:
                preds = model.predict(X)
            except Exception:
                # Fallback: single-row prediction (for wrapper classes)
                preds = [model.predict([x])[0] for x in X]
            for r, p in zip(batch, preds):
                out = dict(r)
                out["prediction"] = p.tolist() if hasattr(p, "tolist") else p
                predictions.append(out)
            if i % (args.batch_size * 10) == 0:
                print(f"[INFO] {i + len(batch)}/{total}")
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Write output CSV
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(predictions[0].keys()))
        writer.writeheader()
        writer.writerows(predictions)

    meta = {
        "timestamp": datetime.now().isoformat(),
        "model_type": type(model).__name__,
        "rows_in": total,
        "rows_out": len(predictions),
        "feature_cols": feature_cols,
    }
    meta_path = args.output.rsplit(".", 1)[0] + "_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, default=str)

    print(f"[INFO] Wrote {len(predictions)} predictions → {args.output}")
    print(f"[INFO] Metadata → {meta_path}")


if __name__ == "__main__":
    main()
