"""
Test env must be configured before backend modules import config/database.
"""
import base64
import hashlib
import os
import sys
import tempfile
from pathlib import Path

# Deterministic test secrets
_test_key = base64.urlsafe_b64encode(hashlib.sha256(b"test-pii-key").digest()).decode()
_tmpdir = tempfile.mkdtemp(prefix="creditfix-test-")

os.environ.update({
    "ENVIRONMENT": "test",
    "DATABASE_URL": f"sqlite:///{_tmpdir}/test.db",
    "PII_ENCRYPTION_KEY": _test_key,
    "TERMS_TOKEN_SECRET": "test-terms-secret",
    "CYPHER_SERVER_SECRET": "test-cypher-secret",
    "ADMIN_KEY": "test-admin-key",
    "STRIPE_SECRET_KEY": "",
    "STRIPE_WEBHOOK_SECRET": "",
    "LOB_API_KEY": "",
    "LOB_WEBHOOK_SECRET": "test-lob-secret",
    "ANTHROPIC_API_KEY": "",
    "DEMO_MODE": "false",
})

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

import main  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(main.app) as c:
        yield c


@pytest.fixture()
def terms_token(client):
    resp = client.post("/api/terms/accept")
    assert resp.status_code == 200
    return resp.json()["terms_token"]


TEST_CASE = {
    "name": "Jane Testcase",
    "address": "123 Main St, Dallas, TX 75201",
    "dob": "1990-05-01",
    "ssn_last4": "1234",
    "phone": "555-123-4567",
    "email": "jane@example.com",
}


@pytest.fixture()
def case_session(client, terms_token):
    """A freshly created case; returns its session_id."""
    resp = client.post("/api/case", json=TEST_CASE, headers={"X-Terms-Token": terms_token})
    assert resp.status_code == 200, resp.text
    return resp.json()["session_id"]
