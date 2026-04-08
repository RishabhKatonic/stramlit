#!/usr/bin/env python3
"""
Knowledge Connector Job
Container Image: connectorsdk:connector-sdk-v2-python-3.11
Command: python sync.py
Tags: connector, CPU
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ── Configuration from environment variables ──────────────────────────────────

SOURCE_TYPE = os.environ.get("CONNECTOR_SOURCE_TYPE", "confluence")
API_KEY = os.environ.get("CONNECTOR_API_KEY")
OAUTH_TOKEN = os.environ.get("CONNECTOR_OAUTH_TOKEN")
BASE_URL = os.environ.get("CONNECTOR_BASE_URL", "https://api.example.com")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "default")
STATE_DIR = os.environ.get("SYNC_STATE_DIR", "/tmp/sync_state")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1000"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))

SUPPORTED_SOURCES = {
    "confluence", "github", "google_drive", "sharepoint",
    "notion", "slack", "hubspot", "jira", "trello",
    "discord", "dropbox", "zendesk", "intercom",
}


def get_credentials():
    """Retrieve and validate credentials (never log them)."""
    if API_KEY:
        print(f"[INFO] Auth method: API key (key=***)")
        return {"type": "api_key", "key": API_KEY}
    elif OAUTH_TOKEN:
        print(f"[INFO] Auth method: OAuth token (token=***)")
        return {"type": "oauth", "token": OAUTH_TOKEN}
    else:
        print("[ERROR] No credentials found. Set CONNECTOR_API_KEY or CONNECTOR_OAUTH_TOKEN")
        sys.exit(1)


def load_sync_state():
    """Load previous sync state for incremental sync."""
    os.makedirs(STATE_DIR, exist_ok=True)
    state_file = os.path.join(STATE_DIR, "sync_state.json")
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)
        print(f"[INFO] Incremental sync from {state.get('last_sync', 'unknown')}")
        return state
    print("[INFO] No previous state — running full sync")
    return {}


def save_sync_state(state):
    """Persist sync state for next run."""
    os.makedirs(STATE_DIR, exist_ok=True)
    state_file = os.path.join(STATE_DIR, "sync_state.json")
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
    print(f"[INFO] Sync state saved ({state.get('docs_synced', 0)} docs)")


def fetch_documents(credentials, last_sync=None):
    """
    Fetch documents from the source.
    Replace this placeholder with actual SDK calls for your connector.
    """
    print(f"[INFO] Fetching documents from {SOURCE_TYPE} ({BASE_URL})")

    # Placeholder: in production, use the connector SDK to fetch real docs
    docs = [
        {
            "id": f"doc-{i:03d}",
            "title": f"Document {i}",
            "content": f"This is the content of document {i}. " * 20,
            "source": SOURCE_TYPE,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"space": "Engineering"},
        }
        for i in range(1, 11)
    ]

    # Filter by last_sync for incremental
    if last_sync:
        last_dt = datetime.fromisoformat(last_sync)
        docs = [d for d in docs if datetime.fromisoformat(d["updated_at"]) > last_dt]
        print(f"[INFO] Incremental: {len(docs)} new/updated documents")
    else:
        print(f"[INFO] Full sync: {len(docs)} documents")

    return docs


def validate_document(doc):
    """Validate document has required fields and non-empty content."""
    required = {"id", "title", "content", "source", "updated_at"}
    if not required.issubset(doc.keys()):
        return False
    if not doc.get("content"):
        return False
    return True


def deduplicate_documents(docs):
    """Keep latest version of each document by ID."""
    latest = {}
    for doc in docs:
        latest[doc["id"]] = doc
    deduped = list(latest.values())
    if len(deduped) < len(docs):
        print(f"[INFO] Deduplication: {len(docs)} -> {len(deduped)} documents")
    return deduped


def chunk_document(doc, chunk_size=1000):
    """Split large documents into chunks for the knowledge base."""
    content = doc["content"]
    if len(content) <= chunk_size:
        return [doc]

    chunks = []
    for i in range(0, len(content), chunk_size):
        chunk_doc = dict(doc)
        chunk_doc["id"] = f"{doc['id']}_chunk_{i // chunk_size}"
        chunk_doc["content"] = content[i : i + chunk_size]
        chunks.append(chunk_doc)

    return chunks


def ingest_documents(docs):
    """Ingest documents into the knowledge base with retry logic."""
    print(f"[INFO] Ingesting {len(docs)} documents into knowledge base {KNOWLEDGE_BASE_ID}")
    ingested = 0

    for doc in docs:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Placeholder: replace with actual KB ingestion API call
                ingested += 1
                break
            except Exception as e:
                delay = 1.0 * (2 ** (attempt - 1))  # exponential backoff
                print(f"[WARN] Retry {attempt}/{MAX_RETRIES} for {doc['id']} (waiting {delay}s)")
                time.sleep(delay)
                if attempt == MAX_RETRIES:
                    print(f"[ERROR] Failed to ingest {doc['id']} after {MAX_RETRIES} retries")

    return ingested


def main():
    print(f"[INFO] Knowledge Connector Sync")
    print(f"[INFO] Source type:      {SOURCE_TYPE}")
    print(f"[INFO] Knowledge base:   {KNOWLEDGE_BASE_ID}")

    # Validate source type
    if SOURCE_TYPE not in SUPPORTED_SOURCES:
        print(f"[ERROR] Unsupported source type: {SOURCE_TYPE}")
        print(f"[INFO] Supported: {sorted(SUPPORTED_SOURCES)}")
        sys.exit(1)

    credentials = get_credentials()
    state = load_sync_state()
    last_sync = state.get("last_sync")

    # Fetch
    docs = fetch_documents(credentials, last_sync=last_sync)

    # Validate & filter
    valid_docs = [d for d in docs if validate_document(d)]
    if len(valid_docs) < len(docs):
        print(f"[WARN] Filtered {len(docs) - len(valid_docs)} invalid documents")

    # Deduplicate
    valid_docs = deduplicate_documents(valid_docs)

    # Chunk large documents
    all_chunks = []
    for doc in valid_docs:
        all_chunks.extend(chunk_document(doc, chunk_size=CHUNK_SIZE))
    print(f"[INFO] {len(valid_docs)} docs -> {len(all_chunks)} chunks")

    # Ingest
    ingested = ingest_documents(all_chunks)

    # Save state
    save_sync_state({
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "docs_synced": ingested,
        "source_type": SOURCE_TYPE,
    })

    print(f"[INFO] Sync complete — {ingested} chunks ingested")
    print("[INFO] Done")


if __name__ == "__main__":
    main()
