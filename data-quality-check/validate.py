#!/usr/bin/env python3
"""
Data Quality Check Job
Container Image: python:3.12-slim
Command: python validate.py --suite full --output /reports/dq
Tags: cpu, validation, CPU
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Run data quality checks")
    parser.add_argument(
        "--suite",
        choices=["full", "basic", "custom"],
        default="full",
        help="Validation suite to run (default: full)",
    )
    parser.add_argument("--output", required=True, help="Output directory for DQ reports")
    parser.add_argument("--input", default="/data", help="Input data directory to validate")
    parser.add_argument("--threshold", type=float, default=5.0, help="Null percentage threshold")
    return parser.parse_args()


class CheckResult:
    def __init__(self, name, status, metric=None, value=None, threshold=None, message=""):
        self.name = name
        self.status = status  # PASS, FAIL, WARN
        self.metric = metric
        self.value = value
        self.threshold = threshold
        self.message = message

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
        }


def check_nulls(data, columns, threshold=5.0):
    """Detect null/missing values per column."""
    results = []
    total = len(data)
    if total == 0:
        return results

    for col in columns:
        null_count = sum(1 for row in data if row.get(col) is None or row.get(col) == "")
        pct = (null_count / total) * 100

        if pct > threshold:
            status = "FAIL"
            msg = f"Null percentage {pct:.1f}% exceeds threshold {threshold}%"
        elif pct > 0:
            status = "WARN"
            msg = f"Null percentage {pct:.1f}% (within threshold)"
        else:
            status = "PASS"
            msg = "No nulls found"

        results.append(CheckResult(
            name=f"null_check_{col}",
            status=status,
            metric="null_percentage",
            value=pct,
            threshold=threshold,
            message=msg,
        ))
    return results


def check_schema(data, expected_columns):
    """Verify expected columns are present."""
    if not data:
        return [CheckResult("schema_check", "WARN", message="No data to validate")]

    actual = set(data[0].keys())
    missing = expected_columns - actual
    extra = actual - expected_columns

    results = []
    if missing:
        results.append(CheckResult(
            "missing_columns", "FAIL",
            message=f"Missing columns: {missing}",
        ))
    else:
        results.append(CheckResult("missing_columns", "PASS", message="All expected columns present"))

    if extra:
        results.append(CheckResult(
            "unexpected_columns", "WARN",
            message=f"Unexpected columns: {extra}",
        ))
    return results


def check_duplicates(data, key_column="id"):
    """Detect duplicate rows by key."""
    if not data:
        return [CheckResult("duplicate_check", "PASS", message="No data")]

    seen = set()
    dupes = []
    for row in data:
        key = row.get(key_column, json.dumps(row, sort_keys=True))
        if key in seen:
            dupes.append(key)
        seen.add(key)

    if dupes:
        return [CheckResult(
            "duplicate_check", "FAIL",
            metric="duplicate_count", value=len(dupes),
            message=f"Found {len(dupes)} duplicate(s)",
        )]
    return [CheckResult("duplicate_check", "PASS", message="No duplicates found")]


def check_value_ranges(data, column, min_val=None, max_val=None):
    """Check that numeric values fall within expected range."""
    results = []
    out_of_range = []
    for row in data:
        val = row.get(column)
        if val is None:
            continue
        try:
            num = float(val)
        except (ValueError, TypeError):
            continue
        if min_val is not None and num < min_val:
            out_of_range.append(num)
        if max_val is not None and num > max_val:
            out_of_range.append(num)

    if out_of_range:
        results.append(CheckResult(
            f"range_check_{column}", "FAIL",
            metric="out_of_range_count", value=len(out_of_range),
            message=f"{len(out_of_range)} values out of range [{min_val}, {max_val}]",
        ))
    else:
        results.append(CheckResult(
            f"range_check_{column}", "PASS",
            message=f"All values within [{min_val}, {max_val}]",
        ))
    return results


def check_empty_strings(data, columns):
    """Detect empty or blank string values."""
    results = []
    for col in columns:
        empty_count = sum(1 for row in data if isinstance(row.get(col), str) and not row[col].strip())
        if empty_count > 0:
            results.append(CheckResult(
                f"empty_string_{col}", "WARN",
                metric="empty_count", value=empty_count,
                message=f"{empty_count} empty/blank values in '{col}'",
            ))
        else:
            results.append(CheckResult(f"empty_string_{col}", "PASS", message="No empty strings"))
    return results


def load_data(input_dir):
    """Load data files from input directory."""
    data = []
    for f in Path(input_dir).rglob("*.csv"):
        with open(f, encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            data.extend(list(reader))
    for f in Path(input_dir).rglob("*.json"):
        with open(f) as fh:
            content = json.load(fh)
            if isinstance(content, list):
                data.extend(content)
            else:
                data.append(content)
    return data


def build_report(suite, all_checks):
    """Build the final quality report."""
    passed = sum(1 for c in all_checks if c.status == "PASS")
    failed = sum(1 for c in all_checks if c.status == "FAIL")
    warnings = sum(1 for c in all_checks if c.status == "WARN")

    report = {
        "suite": suite,
        "timestamp": datetime.now().isoformat(),
        "total_checks": len(all_checks),
        "passed": passed,
        "failed": failed,
        "warnings": warnings,
        "pass_rate": round((passed / len(all_checks)) * 100, 1) if all_checks else 0,
        "checks": [c.to_dict() for c in all_checks],
    }
    return report


def main():
    args = parse_args()
    print(f"[INFO] Suite:     {args.suite}")
    print(f"[INFO] Output:    {args.output}")
    print(f"[INFO] Input:     {args.input}")
    print(f"[INFO] Threshold: {args.threshold}%")

    # Load data
    if os.path.isdir(args.input):
        data = load_data(args.input)
        print(f"[INFO] Loaded {len(data)} records")
    else:
        print(f"[WARN] Input directory {args.input} not found — using sample data")
        data = [
            {"id": "1", "name": "Alice", "email": "alice@example.com", "score": "85"},
            {"id": "2", "name": "", "email": "bob@example.com", "score": "92"},
            {"id": "3", "name": "Charlie", "email": "", "score": "200"},
            {"id": "1", "name": "Alice", "email": "alice@example.com", "score": "85"},
        ]

    columns = set()
    for row in data:
        columns.update(row.keys())

    # Run checks
    all_checks = []

    # Null checks
    all_checks.extend(check_nulls(data, columns, threshold=args.threshold))

    # Schema check
    if columns:
        all_checks.extend(check_schema(data, columns))

    # Duplicate check
    all_checks.extend(check_duplicates(data))

    # Empty string checks
    str_cols = [c for c in columns if any(isinstance(row.get(c), str) for row in data)]
    all_checks.extend(check_empty_strings(data, str_cols))

    if args.suite == "full":
        # Additional range checks for numeric-looking columns
        for col in columns:
            sample_vals = [row.get(col) for row in data[:10] if row.get(col)]
            try:
                [float(v) for v in sample_vals if v]
                all_checks.extend(check_value_ranges(data, col, min_val=0, max_val=1000))
            except (ValueError, TypeError):
                pass

    # Build and write report
    report = build_report(args.suite, all_checks)

    os.makedirs(args.output, exist_ok=True)
    report_path = os.path.join(args.output, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(f"\n{'='*50}")
    print(f"Data Quality Report — {args.suite.upper()} suite")
    print(f"{'='*50}")
    print(f"Total checks: {report['total_checks']}")
    print(f"Passed:       {report['passed']}")
    print(f"Failed:       {report['failed']}")
    print(f"Warnings:     {report['warnings']}")
    print(f"Pass rate:    {report['pass_rate']}%")
    print(f"Report:       {report_path}")

    # Exit with error code if any checks failed
    if report["failed"] > 0:
        print(f"\n[FAIL] {report['failed']} check(s) failed")
        sys.exit(1)

    print("\n[PASS] All checks passed")


if __name__ == "__main__":
    main()
