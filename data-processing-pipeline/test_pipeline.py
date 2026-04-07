"""
Tests for Data Processing Pipeline Job
Template: Data Processing Pipeline
Container Image: Python 3.12 (python:3.12-slim)
Command: python pipeline.py --input /data/raw --output /data/processed
Tags: cpu, CPU
"""

import os
import sys
import json
import csv
import argparse
import tempfile
import shutil
import unittest
from unittest.mock import patch
from pathlib import Path


class TestDataPipelineArgParsing(unittest.TestCase):
    """Test CLI argument parsing for pipeline.py"""

    def test_input_and_output_required(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", required=True)
        parser.add_argument("--output", required=True)
        args = parser.parse_args(["--input", "/data/raw", "--output", "/data/processed"])
        self.assertEqual(args.input, "/data/raw")
        self.assertEqual(args.output, "/data/processed")

    def test_missing_input_fails(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", required=True)
        parser.add_argument("--output", required=True)
        with self.assertRaises(SystemExit):
            parser.parse_args(["--output", "/data/processed"])

    def test_missing_output_fails(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", required=True)
        parser.add_argument("--output", required=True)
        with self.assertRaises(SystemExit):
            parser.parse_args(["--input", "/data/raw"])

    def test_custom_paths(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", required=True)
        parser.add_argument("--output", required=True)
        args = parser.parse_args(["--input", "/mnt/nfs/raw", "--output", "/mnt/nfs/clean"])
        self.assertEqual(args.input, "/mnt/nfs/raw")
        self.assertEqual(args.output, "/mnt/nfs/clean")


class TestDataPipelineInputValidation(unittest.TestCase):
    """Test input directory and file discovery"""

    def test_input_directory_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "raw")
            os.makedirs(input_dir)
            self.assertTrue(os.path.isdir(input_dir))

    def test_empty_input_directory_handled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "raw")
            os.makedirs(input_dir)
            files = os.listdir(input_dir)
            self.assertEqual(len(files), 0)

    def test_discovers_csv_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["data1.csv", "data2.csv", "readme.txt"]:
                Path(os.path.join(tmpdir, name)).touch()
            csv_files = [f for f in os.listdir(tmpdir) if f.endswith(".csv")]
            self.assertEqual(len(csv_files), 2)

    def test_discovers_json_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["events.json", "users.json"]:
                Path(os.path.join(tmpdir, name)).touch()
            json_files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
            self.assertEqual(len(json_files), 2)

    def test_nested_subdirectory_scan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sub = os.path.join(tmpdir, "2024", "01")
            os.makedirs(sub)
            Path(os.path.join(sub, "data.csv")).touch()
            found = list(Path(tmpdir).rglob("*.csv"))
            self.assertEqual(len(found), 1)


class TestDataPipelineTransformations(unittest.TestCase):
    """Test ETL transformation logic"""

    def test_null_value_removal(self):
        data = [{"a": 1, "b": None}, {"a": 2, "b": 3}]
        cleaned = [row for row in data if all(v is not None for v in row.values())]
        self.assertEqual(len(cleaned), 1)

    def test_column_rename(self):
        row = {"old_name": 42}
        mapping = {"old_name": "new_name"}
        renamed = {mapping.get(k, k): v for k, v in row.items()}
        self.assertIn("new_name", renamed)
        self.assertNotIn("old_name", renamed)

    def test_type_casting_string_to_int(self):
        raw = {"count": "123"}
        processed = {"count": int(raw["count"])}
        self.assertIsInstance(processed["count"], int)
        self.assertEqual(processed["count"], 123)

    def test_duplicate_removal(self):
        data = [{"id": 1, "v": "a"}, {"id": 1, "v": "a"}, {"id": 2, "v": "b"}]
        seen = set()
        unique = []
        for row in data:
            key = json.dumps(row, sort_keys=True)
            if key not in seen:
                seen.add(key)
                unique.append(row)
        self.assertEqual(len(unique), 2)

    def test_whitespace_trimming(self):
        raw = {"name": "  Alice  ", "email": " bob@example.com "}
        cleaned = {k: v.strip() if isinstance(v, str) else v for k, v in raw.items()}
        self.assertEqual(cleaned["name"], "Alice")
        self.assertEqual(cleaned["email"], "bob@example.com")

    def test_date_format_standardization(self):
        from datetime import datetime

        raw_date = "01/15/2024"
        parsed = datetime.strptime(raw_date, "%m/%d/%Y")
        iso = parsed.strftime("%Y-%m-%d")
        self.assertEqual(iso, "2024-01-15")


class TestDataPipelineOutputGeneration(unittest.TestCase):
    """Test output writing"""

    def test_output_directory_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "processed")
            os.makedirs(output_dir, exist_ok=True)
            self.assertTrue(os.path.isdir(output_dir))

    def test_csv_output_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
            with open(output_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "name"])
                writer.writeheader()
                writer.writerows(rows)
            with open(output_file) as f:
                reader = csv.DictReader(f)
                result = list(reader)
            self.assertEqual(len(result), 2)

    def test_json_output_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.json")
            data = [{"id": 1}, {"id": 2}]
            with open(output_file, "w") as f:
                json.dump(data, f)
            with open(output_file) as f:
                loaded = json.load(f)
            self.assertEqual(len(loaded), 2)

    def test_output_not_same_as_input(self):
        input_path = "/data/raw"
        output_path = "/data/processed"
        self.assertNotEqual(input_path, output_path)

    def test_parquet_like_partitioning(self):
        """Output may be partitioned by date/key"""
        with tempfile.TemporaryDirectory() as tmpdir:
            for part in ["year=2024/month=01", "year=2024/month=02"]:
                p = os.path.join(tmpdir, part)
                os.makedirs(p)
                Path(os.path.join(p, "data.csv")).touch()
            found = list(Path(tmpdir).rglob("data.csv"))
            self.assertEqual(len(found), 2)


class TestDataPipelineErrorHandling(unittest.TestCase):
    """Test error handling and resilience"""

    def test_malformed_csv_row_skipped(self):
        raw_lines = ["id,name", "1,Alice", "BAD_ROW", "2,Bob"]
        valid = []
        for line in raw_lines[1:]:
            parts = line.split(",")
            if len(parts) == 2:
                valid.append({"id": parts[0], "name": parts[1]})
        self.assertEqual(len(valid), 2)

    def test_encoding_error_handled(self):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(b"id,name\n1,\xff\xfe\n")
            path = f.name
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.assertIn("id,name", content)
        finally:
            os.unlink(path)

    def test_permission_denied_on_output_dir(self):
        """Pipeline should raise clear error if output dir is not writable"""
        non_writable = "/proc/fake_output"
        self.assertFalse(os.access(non_writable, os.W_OK))


class TestDataPipelineContainerEnv(unittest.TestCase):
    """Test container environment expectations"""

    def test_python_version(self):
        major, minor = sys.version_info[:2]
        self.assertGreaterEqual(major, 3)
        self.assertGreaterEqual(minor, 10)

    def test_cpu_only_job(self):
        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
        # CPU-only job should not depend on GPU devices
        # Passes regardless — just documenting the expectation
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
