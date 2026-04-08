#!/usr/bin/env python3
"""
Batch Prediction Job
Container Image: python:3.11-slim
Command: python predict.py --model /models/latest --batch-size 256
Tags: parallel, CPU/GPU
"""

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Run batch inference")
    parser.add_argument("--model", required=True, help="Path to model directory or file")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size (default: 256)")
    parser.add_argument("--input", default="/data/input", help="Input data directory")
    parser.add_argument("--output", default="/data/predictions", help="Output predictions directory")
    args = parser.parse_args()
    if args.batch_size <= 0:
        parser.error("--batch-size must be a positive integer")
    return args


def load_model(model_path):
    """Load model from the given path (resolves symlinks like 'latest')."""
    resolved = os.path.realpath(model_path)
    print(f"[INFO] Loading model from {resolved}")
    if not os.path.exists(resolved):
        print(f"[ERROR] Model path does not exist: {resolved}")
        sys.exit(1)
    # Placeholder: replace with actual model loading (torch.load, joblib, etc.)
    model = {"path": resolved, "loaded": True}
    print("[INFO] Model loaded successfully")
    return model


def load_input_data(input_dir):
    """Discover and load input data."""
    if not os.path.isdir(input_dir):
        print(f"[WARN] Input directory {input_dir} not found, using sample data")
        return [{"id": i, "features": [0.1 * i, 0.2 * i]} for i in range(100)]

    data = []
    for f in sorted(Path(input_dir).rglob("*.json")):
        with open(f) as fh:
            data.extend(json.load(fh))
    print(f"[INFO] Loaded {len(data)} input records")
    return data


def batch_data(data, batch_size):
    """Split data into batches."""
    return [data[i : i + batch_size] for i in range(0, len(data), batch_size)]


def predict_batch(model, batch):
    """Run inference on a single batch."""
    # Placeholder: replace with actual model.predict()
    return [
        {
            "input_id": str(item.get("id", idx)),
            "prediction": round(min(max(0.0, (hash(str(item)) % 100) / 100.0), 1.0), 4),
            "label": "positive" if (hash(str(item)) % 100) > 50 else "negative",
        }
        for idx, item in enumerate(batch)
    ]


def main():
    args = parse_args()
    workers = int(os.environ.get("NUM_WORKERS", "1"))
    device = os.environ.get("CUDA_VISIBLE_DEVICES", "cpu")

    print(f"[INFO] Model path:  {args.model}")
    print(f"[INFO] Batch size:  {args.batch_size}")
    print(f"[INFO] Workers:     {workers}")
    print(f"[INFO] Device:      {device}")

    model = load_model(args.model)
    data = load_input_data(args.input)

    if not data:
        print("[WARN] No input data — writing empty predictions")
        predictions = []
    else:
        batches = batch_data(data, args.batch_size)
        print(f"[INFO] Processing {len(data)} records in {len(batches)} batches")

        predictions = []
        for i, batch in enumerate(batches):
            preds = predict_batch(model, batch)
            predictions.extend(preds)
            print(f"[INFO] Batch {i + 1}/{len(batches)} done ({len(preds)} predictions)")

    # Write output
    os.makedirs(args.output, exist_ok=True)
    output_path = os.path.join(args.output, "predictions.json")
    with open(output_path, "w") as f:
        json.dump(predictions, f, indent=2)

    print(f"[INFO] {len(predictions)} predictions written to {output_path}")
    assert len(predictions) == len(data), "Prediction count must match input count"
    print("[INFO] Done")


if __name__ == "__main__":
    main()
