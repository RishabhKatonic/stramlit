#!/usr/bin/env python3
"""
Knowledge Connector Sync Job
Container Image: quay.io/katonic/connectorsdk:connector-sdk-v3-python-3.11
Command: python sync.py --source /data/docs --output /reports/chunks.json
Tags: connector, cpu

Reads documents (txt/md/pdf/html), chunks them, and writes a JSON
index ready to be ingested by the knowledge engine. Chunking uses
simple paragraph/sentence splitting — no ML deps required.
"""

import argparse
import json
import os
import re
import sys
import traceback
import hashlib
from datetime import datetime
from pathlib import Path


SUPPORTED_EXT = {".txt", ".md", ".rst", ".html", ".htm"}


def parse_args():
    p = argparse.ArgumentParser(description="Knowledge connector — chunk + index documents")
    p.add_argument("--source", default="/data", help="Source directory with documents")
    p.add_argument("--output", default="/reports/chunks.json", help="Output chunk index path")
    p.add_argument("--chunk-size", type=int, default=500, help="Words per chunk")
    p.add_argument("--overlap", type=int, default=50, help="Word overlap between chunks")
    p.add_argument("--max-chunks", type=int, default=10000, help="Safety cap on total chunks")
    return p.parse_args()


def discover(src):
    """Return list of supported docs under `src`. `src` can be a directory
    (recursive scan) OR a single file path."""
    p = Path(src)
    if p.is_file():
        return [p] if p.suffix.lower() in SUPPORTED_EXT else []
    files = []
    for ext in SUPPORTED_EXT:
        files.extend(p.rglob(f"*{ext}"))
    return sorted(files)


def clean_html(html):
    """Strip HTML tags + collapse whitespace (no beautifulsoup needed)."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_document(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    if path.suffix.lower() in (".html", ".htm"):
        return clean_html(content)
    return content


def chunk_text(text, size, overlap):
    """Split by words with overlap."""
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break
        start = end - overlap
    return chunks


def make_id(source, idx, text):
    h = hashlib.sha256(f"{source}|{idx}|{text[:100]}".encode()).hexdigest()[:12]
    return f"chunk_{h}"


def main():
    args = parse_args()
    src = Path(args.source)
    if not src.exists():
        print(f"[ERROR] Source path missing: {src}")
        sys.exit(1)

    print(f"[INFO] Source: {src}")
    print(f"[INFO] Chunk size: {args.chunk_size} words, overlap={args.overlap}")

    files = discover(src)
    print(f"[INFO] Found {len(files)} documents")
    if not files:
        print("[WARN] No supported documents found (.txt/.md/.rst/.html)")
        # Still write empty index so downstream jobs can detect it
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump({"chunks": [], "meta": {"total": 0, "timestamp": datetime.now().isoformat()}}, f, indent=2)
        sys.exit(0)

    chunks = []
    failed = 0
    for fp in files:
        try:
            text = read_document(fp)
            if not text.strip():
                continue
            for i, c in enumerate(chunk_text(text, args.chunk_size, args.overlap)):
                if len(chunks) >= args.max_chunks:
                    print(f"[WARN] Hit --max-chunks={args.max_chunks}, stopping")
                    break
                # relative_to fails if src is a single file (not an ancestor
                # of fp). Fall back to the filename in that case.
                try:
                    rel_source = str(fp.relative_to(src if src.is_dir() else src.parent))
                except ValueError:
                    rel_source = fp.name
                chunks.append({
                    "id": make_id(str(fp), i, c),
                    "source": rel_source,
                    "chunk_index": i,
                    "word_count": len(c.split()),
                    "text": c,
                })
            if len(chunks) >= args.max_chunks:
                break
        except Exception as e:
            failed += 1
            print(f"[ERROR] {fp}: {e}")
            traceback.print_exc()

    # Write
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    output = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "source": str(src),
            "total_files": len(files),
            "failed_files": failed,
            "total_chunks": len(chunks),
            "chunk_size": args.chunk_size,
            "overlap": args.overlap,
        },
        "chunks": chunks,
    }
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[INFO] {len(files)} files → {len(chunks)} chunks ({failed} failed)")
    print(f"[INFO] Index written → {args.output}")
    sys.exit(1 if failed and len(chunks) == 0 else 0)


if __name__ == "__main__":
    main()
