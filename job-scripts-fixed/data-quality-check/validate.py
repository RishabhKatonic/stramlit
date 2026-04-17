#!/usr/bin/env python3
"""
Data Quality Check Job
Container Image: python:3.12-slim
Command: python validate.py --suite full --input /data --output /reports/dq
Tags: cpu, validation

Fixes from v1:
- No fake sample-data fallback — fails loud if input is missing
- Schema check reads an external schema.json instead of using input's own columns
- Duplicate check auto-detects an id-like column OR uses --key-column
- Range checks configurable per column via rules.json
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Run data quality checks")
    p.add_argument("--suite", choices=["full", "basic"], default="full")
    p.add_argument("--input", default="/data", help="Input data directory")
    p.add_argument("--output", required=True, help="Output directory for DQ reports")
    p.add_argument("--threshold", type=float, default=5.0, help="Null % threshold")
    p.add_argument("--schema", default="", help="Path to expected schema JSON: [\"col1\", \"col2\", ...]")
    p.add_argument("--rules", default="", help="Path to range rules JSON: {\"col\": {\"min\": 0, \"max\": 100}}")
    p.add_argument("--key-column", default="", help="Column to use for duplicate detection (auto-detect if empty)")
    return p.parse_args()


class CheckResult:
    def __init__(self, name, status, metric=None, value=None, threshold=None, message=""):
        self.name, self.status = name, status
        self.metric, self.value, self.threshold = metric, value, threshold
        self.message = message

    def to_dict(self):
        return {
            "name": self.name, "status": self.status,
            "metric": self.metric, "value": self.value,
            "threshold": self.threshold, "message": self.message,
        }


def check_nulls(data, columns, threshold):
    if not data:
        return []
    out = []
    for col in columns:
        nulls = sum(1 for r in data if r.get(col) in (None, ""))
        pct = (nulls / len(data)) * 100
        if pct > threshold:
            out.append(CheckResult(f"null_{col}", "FAIL", "null_pct", round(pct, 2), threshold,
                                   f"{pct:.1f}% nulls exceed {threshold}%"))
        elif pct > 0:
            out.append(CheckResult(f"null_{col}", "WARN", "null_pct", round(pct, 2), threshold,
                                   f"{pct:.1f}% nulls (within threshold)"))
        else:
            out.append(CheckResult(f"null_{col}", "PASS", "null_pct", 0, threshold, "no nulls"))
    return out


def check_schema(data, expected):
    """Validate against EXTERNAL expected schema."""
    if not expected:
        return [CheckResult("schema", "WARN", message="no --schema provided; skipping")]
    if not data:
        return [CheckResult("schema", "WARN", message="no data to check")]
    actual = set(data[0].keys())
    expected_set = set(expected)
    missing = expected_set - actual
    extra = actual - expected_set
    out = []
    if missing:
        out.append(CheckResult("schema_missing", "FAIL",
                               message=f"missing columns: {sorted(missing)}"))
    else:
        out.append(CheckResult("schema_missing", "PASS", message="all expected columns present"))
    if extra:
        out.append(CheckResult("schema_extra", "WARN",
                               message=f"unexpected columns: {sorted(extra)}"))
    return out


def detect_key_column(data, columns):
    """Auto-detect a unique key column (id, uuid, email, etc.)."""
    if not data:
        return None
    candidates = [c for c in columns if c.lower() in ("id", "uuid", "pk", "_id")]
    for c in candidates:
        vals = [r.get(c) for r in data]
        if len(set(vals)) == len(vals) and all(v for v in vals):
            return c
    return None


def check_duplicates(data, key_column):
    if not data:
        return [CheckResult("duplicates", "PASS", message="no data")]
    if not key_column:
        return [CheckResult("duplicates", "WARN",
                            message="no key column provided/detected; skipped")]
    seen = set()
    dupes = 0
    for row in data:
        k = row.get(key_column)
        if k is None:
            continue
        if k in seen:
            dupes += 1
        else:
            seen.add(k)
    if dupes:
        return [CheckResult("duplicates", "FAIL", "dupe_count", dupes, None,
                            f"{dupes} duplicate values on '{key_column}'")]
    return [CheckResult("duplicates", "PASS", "dupe_count", 0, None,
                        f"no duplicates on '{key_column}'")]


def check_ranges(data, rules):
    """rules: {"col": {"min": 0, "max": 100}}"""
    if not rules:
        return []
    out = []
    for col, rule in rules.items():
        mn = rule.get("min")
        mx = rule.get("max")
        bad = []
        for r in data:
            v = r.get(col)
            if v in (None, ""):
                continue
            try:
                num = float(v)
            except (ValueError, TypeError):
                continue
            if mn is not None and num < mn:
                bad.append(num)
            if mx is not None and num > mx:
                bad.append(num)
        if bad:
            out.append(CheckResult(f"range_{col}", "FAIL", "out_of_range", len(bad),
                                   None, f"{len(bad)} values outside [{mn}, {mx}]"))
        else:
            out.append(CheckResult(f"range_{col}", "PASS", "out_of_range", 0,
                                   None, f"all values in [{mn}, {mx}]"))
    return out


def check_empty_strings(data, columns):
    out = []
    for col in columns:
        empty = sum(1 for r in data if isinstance(r.get(col), str) and not r[col].strip())
        if empty:
            out.append(CheckResult(f"empty_{col}", "WARN", "empty_count", empty,
                                   None, f"{empty} blank/empty values"))
        else:
            out.append(CheckResult(f"empty_{col}", "PASS", message="no blanks"))
    return out


def load_data(input_dir):
    data = []
    p = Path(input_dir)
    for f in p.rglob("*.csv"):
        with open(f, encoding="utf-8", errors="replace") as fh:
            data.extend(list(csv.DictReader(fh)))
    for f in p.rglob("*.json"):
        with open(f) as fh:
            try:
                c = json.load(fh)
                if isinstance(c, list):
                    data.extend(c)
                elif isinstance(c, dict):
                    data.append(c)
            except json.JSONDecodeError as e:
                print(f"[WARN] Bad JSON {f}: {e}")
    return data


def load_optional_json(path, default):
    if not path:
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARN] {path} not found — skipping")
        return default
    except json.JSONDecodeError as e:
        print(f"[ERROR] invalid JSON in {path}: {e}")
        sys.exit(1)


def main():
    args = parse_args()
    print(f"[INFO] Suite={args.suite} Input={args.input} Output={args.output}")

    if not os.path.isdir(args.input):
        print(f"[ERROR] Input dir missing: {args.input}")
        sys.exit(1)

    data = load_data(args.input)
    print(f"[INFO] Loaded {len(data)} records")
    if not data:
        print("[ERROR] No data loaded — aborting (use --input with real CSV/JSON)")
        sys.exit(1)

    columns = set()
    for r in data:
        columns.update(r.keys())

    expected_schema = load_optional_json(args.schema, [])
    range_rules = load_optional_json(args.rules, {})
    key_col = args.key_column or detect_key_column(data, columns)
    if key_col:
        print(f"[INFO] Duplicate key column: {key_col}")

    all_checks = []
    all_checks += check_nulls(data, columns, args.threshold)
    all_checks += check_schema(data, expected_schema)
    all_checks += check_duplicates(data, key_col)
    all_checks += check_empty_strings(
        data, [c for c in columns if any(isinstance(r.get(c), str) for r in data)]
    )
    if args.suite == "full":
        all_checks += check_ranges(data, range_rules)

    passed = sum(1 for c in all_checks if c.status == "PASS")
    failed = sum(1 for c in all_checks if c.status == "FAIL")
    warns = sum(1 for c in all_checks if c.status == "WARN")
    report = {
        "suite": args.suite,
        "timestamp": datetime.now().isoformat(),
        "records": len(data),
        "total": len(all_checks),
        "passed": passed, "failed": failed, "warnings": warns,
        "pass_rate": round((passed / len(all_checks)) * 100, 1) if all_checks else 0,
        "checks": [c.to_dict() for c in all_checks],
    }

    os.makedirs(args.output, exist_ok=True)
    report_path = os.path.join(args.output, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Data Quality Report — {args.suite.upper()}")
    print(f"{'='*50}")
    print(f"Records:   {len(data)}")
    print(f"Checks:    {len(all_checks)}")
    print(f"Passed:    {passed}")
    print(f"Failed:    {failed}")
    print(f"Warnings:  {warns}")
    print(f"Pass rate: {report['pass_rate']}%")
    print(f"Report:    {report_path}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
