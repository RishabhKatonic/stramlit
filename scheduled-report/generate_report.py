#!/usr/bin/env python3
"""
Scheduled Report Job
Container Image: python:3.12-slim
Command: python generate_report.py --format pdf
Tags: cron, CPU
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a scheduled report")
    parser.add_argument(
        "--format",
        choices=["pdf", "csv", "html", "json"],
        default="pdf",
        help="Output report format (default: pdf)",
    )
    parser.add_argument(
        "--output-dir",
        default="/tmp/reports",
        help="Directory to write reports to (default: /tmp/reports)",
    )
    return parser.parse_args()


def fetch_data():
    """Fetch data from configured data source."""
    # Placeholder: replace with actual DB/API query
    print("[INFO] Fetching data from source...")
    data = [
        {"metric": "active_users", "value": 1234},
        {"metric": "requests", "value": 56789},
        {"metric": "error_rate", "value": 0.02},
        {"metric": "avg_latency_ms", "value": 142},
    ]
    print(f"[INFO] Fetched {len(data)} metrics")
    return data


def build_report(data, fmt):
    """Build the report payload."""
    report = {
        "title": "Daily Summary",
        "generated_at": datetime.now().isoformat(),
        "format": fmt,
        "source": "scheduled",
        "version": "1.0",
        "rows": data,
    }
    return report


def write_report(report, output_dir, fmt):
    """Write the report to disk with timestamp-based filename."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.{fmt}"
    output_path = os.path.join(output_dir, filename)

    if fmt == "json":
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
    elif fmt == "csv":
        import csv
        with open(output_path, "w", newline="") as f:
            if report["rows"]:
                writer = csv.DictWriter(f, fieldnames=report["rows"][0].keys())
                writer.writeheader()
                writer.writerows(report["rows"])
    elif fmt == "html":
        with open(output_path, "w") as f:
            f.write("<html><body>\n")
            f.write(f"<h1>{report['title']}</h1>\n")
            f.write(f"<p>Generated: {report['generated_at']}</p>\n")
            f.write("<table border='1'>\n")
            for row in report["rows"]:
                f.write("<tr>" + "".join(f"<td>{v}</td>" for v in row.values()) + "</tr>\n")
            f.write("</table>\n</body></html>")
    else:
        # pdf — write JSON as a placeholder (real impl would use reportlab/weasyprint)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

    return output_path


def main():
    args = parse_args()
    print(f"[INFO] Report format: {args.format}")
    print(f"[INFO] Output dir:    {args.output_dir}")

    data = fetch_data()

    if not data:
        print("[WARN] No data returned — generating empty report")

    report = build_report(data, args.format)
    output_path = write_report(report, args.output_dir, args.format)

    print(f"[INFO] Report written to {output_path}")
    print(f"[INFO] Report contains {len(report['rows'])} rows")

    # Verify JSON serializable
    json.dumps(report)
    print("[INFO] Done")


if __name__ == "__main__":
    main()
