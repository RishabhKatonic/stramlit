#!/usr/bin/env python3
"""
ML Model Training Job
Container Image: GPU-enabled Python image (user-defined)
Command: python train.py --epochs 10
Tags: gpu, GPU
"""

import argparse
import json
import math
import os
import sys
import random
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Train an ML model")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Training batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--optimizer", choices=["adam", "sgd", "rmsprop", "adamw"], default="adam")
    parser.add_argument("--dataset", default=None, help="Path to dataset directory")
    parser.add_argument("--checkpoint-dir", default="/tmp/checkpoints", help="Checkpoint directory")
    parser.add_argument("--config", default=None, help="Path to JSON config file")
    return parser.parse_args()


def load_config(config_path):
    """Load hyperparameters from a JSON config file."""
    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        print(f"[INFO] Loaded config from {config_path}")
        return config
    return {}


def load_config_from_env():
    """Load hyperparameters from environment variables."""
    config = {}
    if "LEARNING_RATE" in os.environ:
        config["lr"] = float(os.environ["LEARNING_RATE"])
    if "BATCH_SIZE" in os.environ:
        config["batch_size"] = int(os.environ["BATCH_SIZE"])
    if "EPOCHS" in os.environ:
        config["epochs"] = int(os.environ["EPOCHS"])
    return config


def detect_device():
    """Detect available compute device."""
    cuda_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if cuda_devices and cuda_devices != "cpu":
        devices = cuda_devices.split(",")
        gpu_mem = os.environ.get("GPU_MEMORY_LIMIT", "unknown")
        print(f"[INFO] GPU device(s): {devices} (memory limit: {gpu_mem})")
        return f"cuda:{devices[0]}"
    print("[INFO] No GPU detected — using CPU")
    return "cpu"


def load_dataset(dataset_path):
    """Load dataset from directory."""
    if dataset_path is None:
        print("[INFO] Dataset: None (using synthetic data)")
        # Generate synthetic data
        train_data = [{"features": [random.random() for _ in range(10)], "label": random.randint(0, 1)} for _ in range(1000)]
        val_data = [{"features": [random.random() for _ in range(10)], "label": random.randint(0, 1)} for _ in range(200)]
        return train_data, val_data

    print(f"[INFO] Loading dataset from {dataset_path}")
    if not os.path.isdir(dataset_path):
        print(f"[ERROR] Dataset directory not found: {dataset_path}")
        sys.exit(1)

    # Read line-by-line for large files
    train_data, val_data = [], []
    train_file = os.path.join(dataset_path, "train.csv")
    val_file = os.path.join(dataset_path, "val.csv")

    if os.path.exists(train_file):
        with open(train_file) as f:
            for line in f:
                train_data.append({"raw": line.strip()})
    if os.path.exists(val_file):
        with open(val_file) as f:
            for line in f:
                val_data.append({"raw": line.strip()})

    print(f"[INFO] Train: {len(train_data)} samples, Val: {len(val_data)} samples")
    return train_data, val_data


def simulate_training_step(epoch, total_epochs, lr):
    """Simulate a training step (replace with actual model training)."""
    # Simulated decreasing loss
    base_loss = 2.5 * math.exp(-0.3 * epoch) + random.uniform(-0.05, 0.05)
    train_loss = max(0.01, base_loss)
    val_loss = max(0.01, base_loss + random.uniform(0, 0.15))
    train_acc = min(0.99, 1.0 - train_loss / 3.0 + random.uniform(-0.02, 0.02))
    val_acc = min(0.99, 1.0 - val_loss / 3.0 + random.uniform(-0.02, 0.02))

    return {
        "epoch": epoch,
        "train_loss": round(train_loss, 4),
        "val_loss": round(val_loss, 4),
        "train_accuracy": round(train_acc, 4),
        "val_accuracy": round(val_acc, 4),
        "learning_rate": lr,
    }


def save_checkpoint(checkpoint_dir, epoch, metrics):
    """Save a model checkpoint."""
    os.makedirs(checkpoint_dir, exist_ok=True)
    ckpt_path = os.path.join(checkpoint_dir, f"checkpoint_epoch_{epoch:03d}.pt")
    checkpoint = {
        "epoch": epoch,
        "model_state_dict": {"layer1.weight": "tensor_placeholder"},
        "optimizer_state_dict": {"lr": metrics["learning_rate"]},
        "loss": metrics["val_loss"],
    }
    with open(ckpt_path, "w") as f:
        json.dump(checkpoint, f)
    return ckpt_path


def save_best_model(checkpoint_dir, metrics):
    """Save the best model."""
    best_path = os.path.join(checkpoint_dir, "best_model.pt")
    with open(best_path, "w") as f:
        json.dump({"best_val_loss": metrics["val_loss"], "epoch": metrics["epoch"]}, f)
    return best_path


def main():
    args = parse_args()

    # Merge config sources (env > file > CLI defaults)
    env_config = load_config_from_env()
    file_config = load_config(args.config)

    epochs = env_config.get("epochs", file_config.get("epochs", args.epochs))
    batch_size = env_config.get("batch_size", file_config.get("batch_size", args.batch_size))
    lr = env_config.get("lr", file_config.get("learning_rate", args.lr))
    optimizer = file_config.get("optimizer", args.optimizer)

    assert lr > 0, "Learning rate must be positive"
    assert batch_size > 0, "Batch size must be positive"

    device = detect_device()

    print(f"[INFO] Epochs:      {epochs}")
    print(f"[INFO] Batch size:  {batch_size}")
    print(f"[INFO] LR:          {lr}")
    print(f"[INFO] Optimizer:   {optimizer}")
    print(f"[INFO] Device:      {device}")
    print(f"[INFO] Checkpoints: {args.checkpoint_dir}")

    train_data, val_data = load_dataset(args.dataset)

    # Training loop
    metrics_log = []
    best_val_loss = float("inf")

    log_path = os.path.join(args.checkpoint_dir, "metrics.jsonl")
    os.makedirs(args.checkpoint_dir, exist_ok=True)

    with open(log_path, "w") as log_file:
        for epoch in range(epochs):
            metrics = simulate_training_step(epoch, epochs, lr)
            metrics_log.append(metrics)

            log_file.write(json.dumps(metrics) + "\n")
            log_file.flush()

            print(
                f"[Epoch {epoch + 1}/{epochs}] "
                f"train_loss={metrics['train_loss']:.4f} "
                f"val_loss={metrics['val_loss']:.4f} "
                f"train_acc={metrics['train_accuracy']:.4f} "
                f"val_acc={metrics['val_accuracy']:.4f}"
            )

            # Save checkpoint
            save_checkpoint(args.checkpoint_dir, epoch, metrics)

            # Track best model
            if metrics["val_loss"] < best_val_loss:
                best_val_loss = metrics["val_loss"]
                best_path = save_best_model(args.checkpoint_dir, metrics)
                print(f"[INFO] New best model saved (val_loss={best_val_loss:.4f})")

    print(f"\n[INFO] Training complete")
    print(f"[INFO] Best val_loss: {best_val_loss:.4f}")
    print(f"[INFO] Metrics log:  {log_path}")
    print("[INFO] Done")


if __name__ == "__main__":
    main()
