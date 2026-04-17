#!/usr/bin/env python3
"""
Data Processing Pipeline Job
Container Image: python:3.12-slim
Command: python pipeline.py --input /data --output /reports/processed
Tags: cpu, ETL
"""

import argparse
import csv
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="ETL data processing pipeline")
    parser.add_argument("--input", required=True, help="Input data directory")
    parser.add_argument("--output", required=True, help="Output data directory")
    parser.add_argument("--date-fields", default="", help="Comma-separated MM/DD/YYYY date columns to normalize")
    parser.add_argument("--required-columns", default="", help="Comma-separated columns that must be non-null (drops rows where any listed col is null)")
    parser.add_argument("--rename", default="", help="Comma-separated renames: old=new,old2=new2")
    parser.add_argument("--dedupe", action="store_true", help="Drop duplicate rows")
    parser.add_argument("--trim", action="store_true", default=True, help="Strip whitespace from strings")
    return parser.parse_args()


def discover_files(input_dir):
    csv_files = list(Path(input_dir).rglob("*.csv"))
    json_files = list(Path(input_dir).rglob("*.json"))
    print(f"[INFO] Found {len(csv_files)} CSV, {len(json_files)} JSON")
    return csv_files, json_files


def read_csv_file(filepath):
    with open(filepath, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def read_json_file(filepath):
    with open(filepath) as f:
        return json.load(f)


def transform_clean_nulls(data, required_columns):
    """Drop rows where listed columns are null/empty. If no required_columns, no-op."""
    if not required_columns:
        return data
    return [
        row for row in data
        if all(row.get(c) is not None and row.get(c) != "" for c in required_columns)
    ]


def transform_trim_whitespace(data):
    return [
        {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
        for row in data
    ]


def transform_rename_columns(data, mapping):
    if not mapping:
        return data
    return [{mapping.get(k, k): v for k, v in row.items()} for row in data]


def transform_deduplicate(data):
    seen = set()
    unique = []
    for row in data:
        key = json.dumps(row, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique


def transform_standardize_dates(data, date_fields):
    if not date_fields:
        return data
    out = []
    for row in data:
        new_row = dict(row)
        for field in date_fields:
            val = new_row.get(field)
            if not val:
                continue
            for fmt in ("%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                try:
                    new_row[field] = datetime.strptime(val, fmt).strftime("%Y-%m-%d")
                    break
                except (ValueError, TypeError):
                    continue
        out.append(new_row)
    return out


def write_csv(data, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not data:
        output_path.touch()
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)


def write_json(data, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def parse_rename(s):
    if not s:
        return {}
    pairs = {}
    for p in s.split(","):
        if "=" in p:
            k, v = p.split("=", 1)
            pairs[k.strip()] = v.strip()
    return pairs


def process_file(filepath, input_root, output_dir, args):
    ext = filepath.suffix.lower()
    print(f"[INFO] Processing {filepath}")
    try:
        if ext == ".csv":
            data = read_csv_file(filepath)
        elif ext == ".json":
            data = read_json_file(filepath)
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                print(f"[WARN] JSON at {filepath} is not a list — skipping")
                return 0, 0, True
        else:
            print(f"[WARN] Skipping unsupported file: {ext}")
            return 0, 0, True

        original = len(data)
        date_fields = [s.strip() for s in args.date_fields.split(",") if s.strip()]
        required = [s.strip() for s in args.required_columns.split(",") if s.strip()]
        rename = parse_rename(args.rename)

        if args.trim:
            data = transform_trim_whitespace(data)
        if rename:
            data = transform_rename_columns(data, rename)
        data = transform_standardize_dates(data, date_fields)
        data = transform_clean_nulls(data, required)
        if args.dedupe:
            data = transform_deduplicate(data)

        rel = filepath.relative_to(input_root)
        out_path = Path(output_dir) / rel

        if ext == ".csv":
            write_csv(data, out_path)
        else:
            write_json(data, out_path)

        print(f"[INFO]   {original} → {len(data)} rows, wrote {out_path}")
        return original, len(data), True
    except Exception as exc:
        print(f"[ERROR] Failed to process {filepath}: {exc}")
        traceback.print_exc()
        return 0, 0, False


def main():
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)

    print(f"[INFO] Input:  {in_path}")
    print(f"[INFO] Output: {out_path}")

    if in_path.resolve() == out_path.resolve():
        print("[ERROR] --input and --output must differ")
        sys.exit(1)
    if not in_path.exists():
        print(f"[ERROR] Input path not found: {in_path}")
        sys.exit(1)

    out_path.mkdir(parents=True, exist_ok=True)

    # --input can be a directory (batch mode) OR a single file (single mode).
    if in_path.is_file():
        if in_path.suffix.lower() not in (".csv", ".json"):
            print(f"[ERROR] Only .csv or .json files are supported, got: {in_path.suffix}")
            sys.exit(1)
        all_files = [in_path]
        # Use the file's parent as the input_root so relative paths make sense
        input_root = in_path.parent
        print(f"[INFO] Single-file mode: {in_path.name}")
    else:
        csv_files, json_files = discover_files(in_path)
        all_files = csv_files + json_files
        input_root = in_path
        if not all_files:
            print("[WARN] No CSV or JSON files found — nothing to do")
            sys.exit(0)

    total_in, total_out, succeeded, failed = 0, 0, 0, 0
    for fp in all_files:
        orig, kept, ok = process_file(fp, input_root, out_path, args)
        total_in += orig
        total_out += kept
        if ok:
            succeeded += 1
        else:
            failed += 1

    print(f"[INFO] Pipeline complete — {succeeded}/{len(all_files)} files ok, {failed} failed")
    print(f"[INFO] Rows: {total_in} in → {total_out} out")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
