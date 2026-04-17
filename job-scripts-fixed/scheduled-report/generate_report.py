#!/usr/bin/env python3
"""
Scheduled Report Job
Container Image: python:3.12-slim
Command: python generate_report.py --input /data --output /reports --format csv
Tags: cron, CPU

Fixes from v1:
- Reads REAL data from --input directory (CSV/JSON), not hardcoded sample
- Default output is /reports (persistent) not /tmp (lost on pod exit)
- PDF format is now optional and honest: if reportlab is installed it
  makes a real PDF; otherwise it falls back to HTML and warns
- Non-zero exit on write failure
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
    p = argparse.ArgumentParser(description="Generate a scheduled summary report")
    p.add_argument("--input", default="/data", help="Input directory with CSV/JSON metrics")
    p.add_argument("--output", default="/reports", help="Output directory for reports")
    p.add_argument("--format", choices=["csv", "html", "json", "pdf"], default="csv")
    p.add_argument("--title", default="Daily Summary Report")
    return p.parse_args()


def _read_one(f):
    """Read a single CSV/JSON file into a list of dicts."""
    rows = []
    ext = f.suffix.lower()
    if ext == ".csv":
        with open(f, encoding="utf-8", errors="replace") as fh:
            rows.extend(list(csv.DictReader(fh)))
    elif ext == ".json":
        with open(f) as fh:
            try:
                c = json.load(fh)
                if isinstance(c, list):
                    rows.extend(c)
                elif isinstance(c, dict):
                    rows.append(c)
            except json.JSONDecodeError:
                pass
    return rows


def fetch_data(input_path):
    """Read CSV/JSON files — accepts a directory OR a single file."""
    rows = []
    p = Path(input_path)
    if not p.exists():
        return rows
    if p.is_file():
        return _read_one(p)
    for f in p.rglob("*.csv"):
        rows.extend(_read_one(f))
    for f in p.rglob("*.json"):
        rows.extend(_read_one(f))
    return rows


def build_report(rows, title):
    return {
        "title": title,
        "generated_at": datetime.now().isoformat(),
        "source": "scheduled",
        "version": "2.0",
        "record_count": len(rows),
        "rows": rows,
    }


def write_csv(report, path):
    with open(path, "w", newline="") as f:
        if not report["rows"]:
            f.write("# No data\n")
            return
        keys = list(report["rows"][0].keys())
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(report["rows"])


def write_json(report, path):
    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)


def write_html(report, path):
    rows = report["rows"]
    with open(path, "w") as f:
        f.write(f"<!doctype html><html><head><title>{report['title']}</title>")
        f.write("<style>body{font-family:system-ui;margin:2em;}"
                "table{border-collapse:collapse;}"
                "th,td{border:1px solid #ccc;padding:6px 12px;}"
                "th{background:#f4f4f4;}</style></head><body>")
        f.write(f"<h1>{report['title']}</h1>")
        f.write(f"<p>Generated: {report['generated_at']}<br>"
                f"Records: {report['record_count']}</p>")
        if rows:
            keys = list(rows[0].keys())
            f.write("<table><tr>")
            for k in keys:
                f.write(f"<th>{k}</th>")
            f.write("</tr>")
            for r in rows:
                f.write("<tr>")
                for k in keys:
                    f.write(f"<td>{r.get(k, '')}</td>")
                f.write("</tr>")
            f.write("</table>")
        else:
            f.write("<p><em>No data</em></p>")
        f.write("</body></html>")


def write_pdf(report, path):
    """Real PDF if reportlab is installed; else HTML fallback."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        html_path = path.with_suffix(".html")
        print(f"[WARN] reportlab not installed — falling back to HTML ({html_path})")
        write_html(report, html_path)
        return html_path

    c = canvas.Canvas(str(path), pagesize=letter)
    w, h = letter
    y = h - 50
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, report["title"])
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Generated: {report['generated_at']}")
    y -= 15
    c.drawString(50, y, f"Records: {report['record_count']}")
    y -= 25
    for row in report["rows"][:40]:  # cap at 40 for 1 page
        line = " | ".join(f"{k}={v}" for k, v in row.items())[:100]
        c.drawString(50, y, line)
        y -= 14
        if y < 50:
            c.showPage()
            y = h - 50
    c.save()
    return path


def main():
    args = parse_args()
    print(f"[INFO] Input:  {args.input}")
    print(f"[INFO] Output: {args.output}")
    print(f"[INFO] Format: {args.format}")

    try:
        os.makedirs(args.output, exist_ok=True)
    except OSError as e:
        print(f"[ERROR] Cannot create output dir: {e}")
        sys.exit(1)

    rows = fetch_data(args.input)
    print(f"[INFO] Fetched {len(rows)} rows from {args.input}")
    if not rows:
        print(f"[WARN] No data in {args.input} — report will be empty")

    report = build_report(rows, args.title)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(args.output) / f"report_{ts}.{args.format}"

    try:
        if args.format == "csv":
            write_csv(report, out)
        elif args.format == "json":
            write_json(report, out)
        elif args.format == "html":
            write_html(report, out)
        elif args.format == "pdf":
            out = write_pdf(report, out)
    except Exception as e:
        print(f"[ERROR] Write failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    print(f"[INFO] Report written → {out}")
    print(f"[INFO] {report['record_count']} records")
    print("[INFO] Done")


if __name__ == "__main__":
    main()
