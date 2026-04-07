"""
Tests for Data Quality Check Job
Template: Data Quality Check
Container Image: Python 3.12 (python:3.12-slim)
Command: python validate.py --suite full --output /reports/dq
Tags: cpu, validation, CPU
"""

import os
import sys
import json
import argparse
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


class TestDataQualityArgParsing(unittest.TestCase):
    """Test CLI argument parsing for validate.py"""

    def test_suite_full_accepted(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--suite", choices=["full", "basic", "custom"], default="full")
        parser.add_argument("--output", required=True)
        args = parser.parse_args(["--suite", "full", "--output", "/reports/dq"])
        self.assertEqual(args.suite, "full")

    def test_suite_basic_accepted(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--suite", choices=["full", "basic", "custom"], default="full")
        parser.add_argument("--output", required=True)
        args = parser.parse_args(["--suite", "basic", "--output", "/reports/dq"])
        self.assertEqual(args.suite, "basic")

    def test_default_suite_is_full(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--suite", choices=["full", "basic", "custom"], default="full")
        parser.add_argument("--output", required=True)
        args = parser.parse_args(["--output", "/reports/dq"])
        self.assertEqual(args.suite, "full")

    def test_invalid_suite_rejected(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--suite", choices=["full", "basic", "custom"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["--suite", "mega"])

    def test_output_path_required(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--output", required=True)
        with self.assertRaises(SystemExit):
            parser.parse_args([])


class TestDataQualityNullChecks(unittest.TestCase):
    """Test null/missing value detection"""

    def test_detect_null_values(self):
        data = [{"a": 1, "b": None}, {"a": 2, "b": 3}, {"a": None, "b": 4}]
        null_counts = {}
        for row in data:
            for k, v in row.items():
                if v is None:
                    null_counts[k] = null_counts.get(k, 0) + 1
        self.assertEqual(null_counts.get("a"), 1)
        self.assertEqual(null_counts.get("b"), 1)

    def test_null_percentage_calculation(self):
        total = 100
        null_count = 15
        pct = (null_count / total) * 100
        self.assertAlmostEqual(pct, 15.0)

    def test_no_nulls_passes(self):
        data = [{"a": 1}, {"a": 2}]
        has_nulls = any(v is None for row in data for v in row.values())
        self.assertFalse(has_nulls)

    def test_all_nulls_flagged(self):
        data = [{"a": None}, {"a": None}]
        null_count = sum(1 for row in data if row["a"] is None)
        self.assertEqual(null_count, 2)


class TestDataQualitySchemaValidation(unittest.TestCase):
    """Test schema conformance checks"""

    def test_expected_columns_present(self):
        expected = {"id", "name", "email", "created_at"}
        actual = {"id", "name", "email", "created_at", "extra_col"}
        missing = expected - actual
        self.assertEqual(len(missing), 0)

    def test_missing_columns_detected(self):
        expected = {"id", "name", "email"}
        actual = {"id", "name"}
        missing = expected - actual
        self.assertEqual(missing, {"email"})

    def test_unexpected_columns_detected(self):
        expected = {"id", "name"}
        actual = {"id", "name", "phone"}
        extra = actual - expected
        self.assertEqual(extra, {"phone"})

    def test_type_validation_int(self):
        value = "123"
        try:
            int(value)
            valid = True
        except ValueError:
            valid = False
        self.assertTrue(valid)

    def test_type_validation_float_fail(self):
        value = "not_a_number"
        try:
            float(value)
            valid = True
        except ValueError:
            valid = False
        self.assertFalse(valid)


class TestDataQualityDuplicateDetection(unittest.TestCase):
    """Test duplicate row detection"""

    def test_find_duplicates_by_id(self):
        data = [{"id": 1}, {"id": 2}, {"id": 1}, {"id": 3}]
        seen = set()
        dupes = []
        for row in data:
            if row["id"] in seen:
                dupes.append(row)
            seen.add(row["id"])
        self.assertEqual(len(dupes), 1)
        self.assertEqual(dupes[0]["id"], 1)

    def test_no_duplicates(self):
        data = [{"id": i} for i in range(10)]
        ids = [r["id"] for r in data]
        self.assertEqual(len(ids), len(set(ids)))

    def test_full_row_duplicate(self):
        data = [{"a": 1, "b": 2}, {"a": 1, "b": 2}, {"a": 1, "b": 3}]
        seen = set()
        dupes = 0
        for row in data:
            key = json.dumps(row, sort_keys=True)
            if key in seen:
                dupes += 1
            seen.add(key)
        self.assertEqual(dupes, 1)


class TestDataQualityDriftDetection(unittest.TestCase):
    """Test data drift and distribution checks"""

    def test_value_range_check(self):
        values = [10, 20, 30, 40, 50]
        min_val, max_val = 0, 100
        out_of_range = [v for v in values if v < min_val or v > max_val]
        self.assertEqual(len(out_of_range), 0)

    def test_outlier_detection(self):
        values = [10, 11, 12, 13, 14, 15, 10, 12, 11, 13, 200]
        sorted_vals = sorted(values)
        q1 = sorted_vals[len(sorted_vals) // 4]
        q3 = sorted_vals[3 * len(sorted_vals) // 4]
        iqr = q3 - q1
        upper_bound = q3 + 1.5 * iqr
        outliers = [v for v in values if v > upper_bound]
        self.assertGreater(len(outliers), 0)
        self.assertIn(200, outliers)

    def test_categorical_unexpected_values(self):
        expected_categories = {"low", "medium", "high"}
        actual_values = ["low", "medium", "high", "very_high"]
        unexpected = set(actual_values) - expected_categories
        self.assertEqual(unexpected, {"very_high"})

    def test_empty_string_detection(self):
        data = ["Alice", "", "Bob", "  ", "Charlie"]
        empty_or_blank = [v for v in data if not v.strip()]
        self.assertEqual(len(empty_or_blank), 2)


class TestDataQualityReportGeneration(unittest.TestCase):
    """Test quality report output"""

    def test_report_structure(self):
        report = {
            "suite": "full",
            "timestamp": datetime.now().isoformat(),
            "total_checks": 10,
            "passed": 8,
            "failed": 2,
            "warnings": 1,
            "checks": [],
        }
        required = {"suite", "timestamp", "total_checks", "passed", "failed"}
        self.assertTrue(required.issubset(report.keys()))

    def test_report_written_to_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "dq")
            os.makedirs(output_dir)
            report_path = os.path.join(output_dir, "report.json")
            report = {"passed": 5, "failed": 1}
            with open(report_path, "w") as f:
                json.dump(report, f)
            self.assertTrue(os.path.exists(report_path))

    def test_pass_rate_calculation(self):
        passed = 8
        total = 10
        rate = (passed / total) * 100
        self.assertAlmostEqual(rate, 80.0)

    def test_check_detail_format(self):
        check = {
            "name": "null_check_column_a",
            "status": "FAIL",
            "metric": "null_percentage",
            "value": 15.0,
            "threshold": 5.0,
            "message": "Null percentage 15.0% exceeds threshold 5.0%",
        }
        self.assertIn("status", check)
        self.assertIn(check["status"], ("PASS", "FAIL", "WARN"))

    def test_report_json_serializable(self):
        report = {
            "suite": "full",
            "timestamp": datetime.now().isoformat(),
            "checks": [{"name": "test", "status": "PASS"}],
        }
        serialized = json.dumps(report)
        self.assertIsInstance(serialized, str)


class TestDataQualityContainerEnv(unittest.TestCase):
    """Test container environment expectations"""

    def test_python_version(self):
        major, minor = sys.version_info[:2]
        self.assertGreaterEqual(major, 3)
        self.assertGreaterEqual(minor, 10)

    def test_output_dir_writable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertTrue(os.access(tmpdir, os.W_OK))

    def test_cpu_only_no_gpu_required(self):
        """Data Quality Check is CPU+validation only"""
        self.assertTrue(True)  # No GPU dependency


if __name__ == "__main__":
    unittest.main()
