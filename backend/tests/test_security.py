"""
Security posture: encryption at rest, webhook signatures, admin auth,
terms tokens, and the 24h purge.
"""
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta

from sqlalchemy import text

from cleanup import purge_expired_sessions
from crypto_fields import decrypt_str, encrypt_str
from database import CaseRecord, SessionLocal
from terms_token import _sign, verify_token
from tests.conftest import TEST_CASE


def test_pii_is_encrypted_at_rest(client, case_session):
    """Raw DB rows must contain ciphertext, not plaintext PII."""
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT name, address, email, ssn_last4 FROM cases WHERE session_id = :sid"),
            {"sid": case_session},
        ).fetchone()
    finally:
        db.close()

    assert row is not None
    for raw_value in row:
        assert raw_value.startswith("enc1:")
        assert TEST_CASE["name"] not in raw_value
        assert TEST_CASE["email"] not in raw_value

    # And the ORM round-trips back to plaintext
    db = SessionLocal()
    try:
        record = db.query(CaseRecord).filter_by(session_id=case_session).first()
        assert record.name == TEST_CASE["name"]
        assert record.ssn_last4 == TEST_CASE["ssn_last4"]
    finally:
        db.close()


def test_encrypt_decrypt_roundtrip():
    assert decrypt_str(encrypt_str("hello pii")) == "hello pii"
    # Two encryptions of the same value differ (fresh nonce)
    assert encrypt_str("x") != encrypt_str("x")


def test_terms_token_expiry_and_tamper():
    stale_ts = str(int(time.time()) - 31 * 60)
    stale = f"{stale_ts}.{_sign(stale_ts)}"
    assert verify_token(stale) is None

    fresh_ts = str(int(time.time()))
    tampered = f"{fresh_ts}.{'0' * 32}"
    assert verify_token(tampered) is None
    assert verify_token("garbage") is None
    assert verify_token(f"{fresh_ts}.{_sign(fresh_ts)}") is not None


def test_lob_webhook_rejects_bad_signature(client):
    payload = json.dumps({"event_type": {"id": "letter.delivered"}, "body": {}}).encode()
    resp = client.post(
        "/api/webhooks/lob",
        content=payload,
        headers={"lob-signature": "not-a-real-signature", "content-type": "application/json"},
    )
    assert resp.status_code == 401

    good_sig = hmac.new(b"test-lob-secret", payload, hashlib.sha256).hexdigest()
    resp = client.post(
        "/api/webhooks/lob",
        content=payload,
        headers={"lob-signature": good_sig, "content-type": "application/json"},
    )
    assert resp.status_code == 200


def test_admin_requires_key(client):
    assert client.get("/api/admin/stats").status_code == 401
    assert client.get("/api/admin/stats", headers={"X-Admin-Key": "wrong"}).status_code == 401
    # Query-param keys are no longer accepted (they leak into access logs)
    assert client.get("/api/admin/stats?key=test-admin-key").status_code == 401

    resp = client.get("/api/admin/stats", headers={"X-Admin-Key": "test-admin-key"})
    assert resp.status_code == 200
    assert "total_cases" in resp.json()


def test_purge_deletes_expired_sessions(client, case_session):
    db = SessionLocal()
    try:
        record = db.query(CaseRecord).filter_by(session_id=case_session).first()
        record.created_at = datetime.utcnow() - timedelta(hours=25)
        db.commit()
    finally:
        db.close()

    assert purge_expired_sessions() >= 1

    db = SessionLocal()
    try:
        assert db.query(CaseRecord).filter_by(session_id=case_session).first() is None
    finally:
        db.close()

    assert client.get(f"/api/case/{case_session}/status").status_code == 404
