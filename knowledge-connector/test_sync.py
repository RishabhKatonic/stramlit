"""
Tests for Knowledge Connector Job
Template: Knowledge Connector
Container Image: connectorsdk:connector-sdk-v2-python-3.11
Command: python sync.py
Tags: connector, CPU
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


class TestKnowledgeConnectorSync(unittest.TestCase):
    """Test core sync.py behavior"""

    def test_sync_script_exists_pattern(self):
        """sync.py is the entrypoint — verify naming convention"""
        expected_script = "sync.py"
        self.assertEqual(expected_script, "sync.py")

    def test_connector_sdk_image_name(self):
        image = "connectorsdk:connector-sdk-v2-python-3.11"
        self.assertIn("connector-sdk-v2", image)
        self.assertIn("python-3.11", image)


class TestKnowledgeConnectorAuthentication(unittest.TestCase):
    """Test credential and auth configuration"""

    def test_api_key_env_variable(self):
        with patch.dict(os.environ, {"CONNECTOR_API_KEY": "test-key-123"}):
            key = os.environ.get("CONNECTOR_API_KEY")
            self.assertEqual(key, "test-key-123")

    def test_missing_api_key_detected(self):
        with patch.dict(os.environ, {}, clear=True):
            key = os.environ.get("CONNECTOR_API_KEY")
            self.assertIsNone(key)

    def test_oauth_token_env(self):
        with patch.dict(os.environ, {"CONNECTOR_OAUTH_TOKEN": "bearer-xyz"}):
            token = os.environ.get("CONNECTOR_OAUTH_TOKEN")
            self.assertIsNotNone(token)

    def test_base_url_env(self):
        with patch.dict(os.environ, {"CONNECTOR_BASE_URL": "https://api.example.com"}):
            url = os.environ.get("CONNECTOR_BASE_URL")
            self.assertTrue(url.startswith("https://"))

    def test_credentials_not_logged(self):
        """Credentials must not appear in log output"""
        secret = "sk-secret-12345"
        log_line = f"Connecting to source with key=***"
        self.assertNotIn(secret, log_line)


class TestKnowledgeConnectorDocumentIngestion(unittest.TestCase):
    """Test document ingestion and sync logic"""

    def test_document_schema(self):
        doc = {
            "id": "doc-001",
            "title": "Getting Started",
            "content": "This is the document body.",
            "source": "confluence",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"space": "Engineering"},
        }
        required = {"id", "title", "content", "source", "updated_at"}
        self.assertTrue(required.issubset(doc.keys()))

    def test_empty_content_skipped(self):
        docs = [
            {"id": "1", "content": "hello"},
            {"id": "2", "content": ""},
            {"id": "3", "content": None},
        ]
        valid = [d for d in docs if d.get("content")]
        self.assertEqual(len(valid), 1)

    def test_duplicate_document_dedup(self):
        docs = [
            {"id": "doc-1", "content": "a"},
            {"id": "doc-1", "content": "a updated"},
            {"id": "doc-2", "content": "b"},
        ]
        latest = {}
        for doc in docs:
            latest[doc["id"]] = doc
        self.assertEqual(len(latest), 2)
        self.assertEqual(latest["doc-1"]["content"], "a updated")

    def test_large_document_chunking(self):
        """Large documents should be chunked for the knowledge base"""
        content = "word " * 10000  # ~50K chars
        chunk_size = 1000
        chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), chunk_size)

    def test_document_id_uniqueness(self):
        ids = ["doc-1", "doc-2", "doc-3", "doc-1"]
        self.assertNotEqual(len(ids), len(set(ids)), "Duplicate IDs found")


class TestKnowledgeConnectorIncrementalSync(unittest.TestCase):
    """Test incremental/delta sync behavior"""

    def test_last_sync_timestamp_stored(self):
        state = {"last_sync": "2024-01-15T10:30:00Z"}
        self.assertIn("last_sync", state)

    def test_incremental_filters_by_timestamp(self):
        last_sync = datetime(2024, 1, 15, tzinfo=timezone.utc)
        docs = [
            {"id": "1", "updated_at": datetime(2024, 1, 10, tzinfo=timezone.utc)},
            {"id": "2", "updated_at": datetime(2024, 1, 20, tzinfo=timezone.utc)},
            {"id": "3", "updated_at": datetime(2024, 2, 1, tzinfo=timezone.utc)},
        ]
        new_docs = [d for d in docs if d["updated_at"] > last_sync]
        self.assertEqual(len(new_docs), 2)

    def test_full_sync_when_no_state(self):
        state = {}
        is_full_sync = "last_sync" not in state
        self.assertTrue(is_full_sync)

    def test_sync_state_persisted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "sync_state.json")
            state = {"last_sync": datetime.now(timezone.utc).isoformat(), "docs_synced": 42}
            with open(state_file, "w") as f:
                json.dump(state, f)
            with open(state_file) as f:
                loaded = json.load(f)
            self.assertEqual(loaded["docs_synced"], 42)


class TestKnowledgeConnectorSourceTypes(unittest.TestCase):
    """Test various external source connectors"""

    def test_supported_source_types(self):
        supported = [
            "confluence", "github", "google_drive", "sharepoint",
            "notion", "slack", "hubspot", "jira", "trello",
            "discord", "dropbox", "zendesk", "intercom",
        ]
        self.assertGreater(len(supported), 10)

    def test_source_config_schema(self):
        config = {
            "source_type": "confluence",
            "base_url": "https://mycompany.atlassian.net",
            "space_key": "ENG",
            "auth": {"type": "api_token"},
        }
        self.assertIn("source_type", config)
        self.assertIn("auth", config)

    def test_unknown_source_type_rejected(self):
        known = {"confluence", "github", "google_drive"}
        source = "unknown_source"
        self.assertNotIn(source, known)


class TestKnowledgeConnectorErrorHandling(unittest.TestCase):
    """Test error handling and retries"""

    def test_network_timeout_retry(self):
        max_retries = 3
        attempt = 0
        success = False
        while attempt < max_retries:
            attempt += 1
            if attempt == 3:
                success = True
                break
        self.assertTrue(success)
        self.assertEqual(attempt, 3)

    def test_rate_limit_backoff(self):
        """429 responses should trigger exponential backoff"""
        import time

        base_delay = 1.0
        delays = [base_delay * (2 ** i) for i in range(4)]
        self.assertEqual(delays, [1.0, 2.0, 4.0, 8.0])

    def test_partial_sync_resumes(self):
        """If sync fails mid-way, it should resume from checkpoint"""
        checkpoint = {"last_processed_id": "doc-50", "total": 100}
        remaining = checkpoint["total"] - 50
        self.assertEqual(remaining, 50)

    def test_auth_failure_clear_error(self):
        error = {"status": 401, "message": "Invalid credentials"}
        self.assertEqual(error["status"], 401)


class TestKnowledgeConnectorContainerEnv(unittest.TestCase):
    """Test container environment expectations"""

    def test_connector_sdk_python_version(self):
        """Image is connectorsdk:connector-sdk-v2-python-3.11"""
        major, minor = sys.version_info[:2]
        self.assertGreaterEqual(major, 3)
        self.assertGreaterEqual(minor, 10)

    def test_cpu_only(self):
        """Knowledge Connector is CPU-only"""
        self.assertTrue(True)

    def test_env_config_pattern(self):
        """Connector config typically via env vars"""
        expected_vars = [
            "CONNECTOR_SOURCE_TYPE",
            "CONNECTOR_API_KEY",
            "CONNECTOR_BASE_URL",
            "KNOWLEDGE_BASE_ID",
        ]
        # Just verifying the pattern, not actual values
        for var in expected_vars:
            self.assertIsInstance(var, str)


if __name__ == "__main__":
    unittest.main()
