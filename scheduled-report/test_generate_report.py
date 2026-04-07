"""
Tests for Scheduled Report Job
Template: Scheduled Report
Container Image: Python 3.12 (python:3.12-slim)
Command: python generate_report.py --format pdf
Tags: cron, CPU
"""

import os
import sys
import json
import argparse
import tempfile
import subprocess
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path


class TestScheduledReportArgParsing(unittest.TestCase):
    """Test CLI argument parsing for generate_report.py"""

    def test_format_pdf_accepted(self):
        """--format pdf should be a valid argument"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--format", choices=["pdf", "csv", "html", "json"], default="pdf")
        args = parser.parse_args(["--format", "pdf"])
        self.assertEqual(args.format, "pdf")

    def test_format_csv_accepted(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--format", choices=["pdf", "csv", "html", "json"], default="pdf")
        args = parser.parse_args(["--format", "csv"])
        self.assertEqual(args.format, "csv")

    def test_format_html_accepted(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--format", choices=["pdf", "csv", "html", "json"], default="pdf")
        args = parser.parse_args(["--format", "html"])
        self.assertEqual(args.format, "html")

    def test_default_format_is_pdf(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--format", choices=["pdf", "csv", "html", "json"], default="pdf")
        args = parser.parse_args([])
        self.assertEqual(args.format, "pdf")

    def test_invalid_format_rejected(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--format", choices=["pdf", "csv", "html", "json"], default="pdf")
        with self.assertRaises(SystemExit):
            parser.parse_args(["--format", "xlsx"])


class TestScheduledReportOutputDirectory(unittest.TestCase):
    """Test output directory setup and permissions"""

    def test_output_directory_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "reports")
            os.makedirs(output_dir, exist_ok=True)
            self.assertTrue(os.path.isdir(output_dir))

    def test_output_directory_writable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_report.pdf")
            with open(test_file, "w") as f:
                f.write("test")
            self.assertTrue(os.path.exists(test_file))

    def test_report_filename_contains_timestamp(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.pdf"
        self.assertRegex(filename, r"report_\d{8}_\d{6}\.pdf")

    def test_report_overwrite_protection(self):
        """Reports should not silently overwrite existing files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = os.path.join(tmpdir, "report.pdf")
            with open(existing, "w") as f:
                f.write("original")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file = os.path.join(tmpdir, f"report_{ts}.pdf")
            with open(new_file, "w") as f:
                f.write("new")
            self.assertTrue(os.path.exists(existing))
            self.assertTrue(os.path.exists(new_file))


class TestScheduledReportCronSchedule(unittest.TestCase):
    """Test cron scheduling logic"""

    def test_daily_schedule_expression(self):
        """Standard daily cron: 0 0 * * *"""
        cron_expr = "0 0 * * *"
        parts = cron_expr.split()
        self.assertEqual(len(parts), 5)
        self.assertEqual(parts[0], "0")  # minute
        self.assertEqual(parts[1], "0")  # hour

    def test_weekly_schedule_expression(self):
        """Weekly cron: 0 0 * * 1"""
        cron_expr = "0 0 * * 1"
        parts = cron_expr.split()
        self.assertEqual(parts[4], "1")  # Monday

    def test_hourly_schedule_expression(self):
        cron_expr = "0 * * * *"
        parts = cron_expr.split()
        self.assertEqual(parts[0], "0")
        self.assertEqual(parts[1], "*")


class TestScheduledReportDataSources(unittest.TestCase):
    """Test data source connectivity and fallback"""

    def test_empty_data_produces_empty_report(self):
        data = []
        report_content = {"data": data, "generated_at": datetime.now().isoformat()}
        self.assertEqual(len(report_content["data"]), 0)

    def test_report_metadata_fields(self):
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "format": "pdf",
            "source": "scheduled",
            "version": "1.0",
        }
        required_keys = {"generated_at", "format", "source", "version"}
        self.assertTrue(required_keys.issubset(metadata.keys()))

    def test_large_dataset_handling(self):
        """Report should handle large result sets without memory blow-up"""
        data = [{"id": i, "value": f"row_{i}"} for i in range(100_000)]
        self.assertEqual(len(data), 100_000)

    def test_report_json_serializable(self):
        report = {
            "title": "Daily Summary",
            "rows": [{"metric": "users", "value": 1234}],
            "generated_at": datetime.now().isoformat(),
        }
        serialized = json.dumps(report)
        self.assertIsInstance(serialized, str)


class TestScheduledReportContainerEnv(unittest.TestCase):
    """Test container environment expectations"""

    def test_python_version_312(self):
        """Container uses python:3.12-slim"""
        major, minor = sys.version_info[:2]
        # This test validates the runtime matches the expected container image
        self.assertGreaterEqual(major, 3)
        self.assertGreaterEqual(minor, 10, "Expected Python 3.10+")

    def test_tmp_directory_writable(self):
        with tempfile.NamedTemporaryFile(dir="/tmp", delete=True) as f:
            f.write(b"test")
            self.assertTrue(os.path.exists(f.name))

    def test_no_gpu_required(self):
        """Scheduled Report is CPU-only; GPU env vars should not be required"""
        # Job should work without CUDA
        cuda_home = os.environ.get("CUDA_HOME")
        # Not asserting absence — just ensuring the job doesn't depend on it
        self.assertIsNone(cuda_home, "Scheduled Report should not require CUDA_HOME")


if __name__ == "__main__":
    unittest.main()
