#!/usr/bin/env python3
"""
Data Processing Pipeline Job
Container Image: python:3.12-slim
Command: python pipeline.py --input /data/raw --output /data/processed
Tags: cpu, CPU
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="ETL data processing pipeline")
    parser.add_argument("--input", required=True, help="Input data directory")
    parser.add_argument("--output", required=True, help="Output data directory")
    return parser.parse_args()


def discover_files(input_dir):
    """Discover CSV and JSON files in input directory (recursive)."""
    csv_files = list(Path(input_dir).rglob("*.csv"))
    json_files = list(Path(input_dir).rglob("*.json"))
    print(f"[INFO] Found {len(csv_files)} CSV files, {len(json_files)} JSON files")
    return csv_files, json_files


def read_csv_file(filepath):
    """Read a CSV file with encoding error handling."""
    rows = []
    with open(filepath, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def read_json_file(filepath):
    """Read a JSON file."""
    with open(filepath) as f:
        return json.load(f)


def transform_clean_nulls(data):
    """Remove rows where any value is None."""
    return [row for row in data if all(v is not None for v in row.values())]


def transform_trim_whitespace(data):
    """Strip whitespace from all string values."""
    return [
        {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
        for row in data
    ]


def transform_rename_columns(data, mapping):
    """Rename columns based on a mapping dict."""
    return [
        {mapping.get(k, k): v for k, v in row.items()}
        for row in data
    ]


def transform_deduplicate(data):
    """Remove duplicate rows."""
    seen = set()
    unique = []
    for row in data:
        key = json.dumps(row, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique


def transform_standardize_dates(data, date_fields=None):
    """Convert date fields from MM/DD/YYYY to ISO format."""
    if not date_fields:
        return data
    result = []
    for row in data:
        new_row = dict(row)
        for field in date_fields:
            if field in new_row and new_row[field]:
                try:
                    parsed = datetime.strptime(new_row[field], "%m/%d/%Y")
                    new_row[field] = parsed.strftime("%Y-%m-%d")
                except ValueError:
                    pass  # leave as-is if format doesn't match
        result.append(new_row)
    return result


def write_csv(data, output_path):
    """Write processed data as CSV."""
    if not data:
        Path(output_path).touch()
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def write_json(data, output_path):
    """Write processed data as JSON."""
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def process_file(filepath, output_dir):
    """Process a single file through the ETL pipeline."""
    ext = filepath.suffix.lower()
    print(f"[INFO] Processing {filepath}")

    if ext == ".csv":
        data = read_csv_file(filepath)
    elif ext == ".json":
        data = read_json_file(filepath)
        if isinstance(data, dict):
            data = [data]
    else:
        print(f"[WARN] Skipping unsupported file type: {ext}")
        return 0

    original_count = len(data)

    # Apply transformations
    data = transform_trim_whitespace(data)
    data = transform_clean_nulls(data)
    data = transform_deduplicate(data)

    print(f"[INFO]   {original_count} rows -> {len(data)} rows after transforms")

    # Write output
    rel_path = filepath.name
    output_path = os.path.join(output_dir, rel_path)

    if ext == ".csv":
        write_csv(data, output_path)
    else:
        write_json(data, output_path)

    return len(data)


def main():
    args = parse_args()

    if args.input == args.output:
        print("[ERROR] Input and output paths must be different")
        sys.exit(1)

    print(f"[INFO] Input:  {args.input}")
    print(f"[INFO] Output: {args.output}")

    if not os.path.isdir(args.input):
        print(f"[ERROR] Input directory does not exist: {args.input}")
        sys.exit(1)

    if not os.access(os.path.dirname(args.output) or "/", os.W_OK):
        print(f"[ERROR] Output directory is not writable: {args.output}")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)

    csv_files, json_files = discover_files(args.input)
    all_files = csv_files + json_files

    if not all_files:
        print("[WARN] No CSV or JSON files found in input directory")
        sys.exit(0)

    total_rows = 0
    for filepath in all_files:
        total_rows += process_file(filepath, args.output)

    print(f"[INFO] Pipeline complete — processed {len(all_files)} files, {total_rows} total rows")
    print("[INFO] Done")


if __name__ == "__main__":
    main()
