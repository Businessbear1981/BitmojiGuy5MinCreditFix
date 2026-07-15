# 5 Minutes to Credit Wellness — Encryption Engine
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# Session-ID-only key derivation. No IP address in the key.
# Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
# Two modes:
#   1. App-level: single key from SECRET_KEY env var (for DB-persisted PII)
#   2. Session-level: key derived from session_id + SECRET_KEY (for ephemeral data)

import os
import json
import hashlib
import base64

from cryptography.fernet import Fernet, InvalidToken

SECRET_KEY = os.environ.get("SECRET_KEY", "ae-labs-credit-fix-dev-key-change-me")


def _derive_key(salt: str) -> bytes:
    """Derive a 32-byte Fernet key from SECRET_KEY + salt."""
    raw = f"{salt}:{SECRET_KEY}"
    digest = hashlib.sha256(raw.encode()).digest()
    return base64.urlsafe_b64encode(digest[:32])


def _app_key() -> bytes:
    """App-level key — same across all sessions. For DB-persisted encryption."""
    return _derive_key("app-level")


def _session_key(session_id: str) -> bytes:
    """Session-level key — unique per session. For ephemeral in-memory data."""
    return _derive_key(session_id)


# ═════════════════════════════════════════════════════════════════════════════
# APP-LEVEL ENCRYPTION — for database PII columns
# ═════════════════════════════════════════════════════════════════════════════

def encrypt(plaintext: str) -> bytes:
    """Encrypt a string using the app-level key. Returns bytes."""
    if not plaintext:
        return b""
    return Fernet(_app_key()).encrypt(plaintext.encode())


def decrypt(token: bytes) -> str:
    """Decrypt bytes using the app-level key. Returns string."""
    if not token:
        return ""
    return Fernet(_app_key()).decrypt(token).decode()


def encrypt_json(data: dict) -> bytes:
    """Encrypt a dict as JSON using the app-level key."""
    return Fernet(_app_key()).encrypt(json.dumps(data).encode())


def decrypt_json(token: bytes) -> dict:
    """Decrypt bytes to a dict using the app-level key."""
    if not token:
        return {}
    return json.loads(Fernet(_app_key()).decrypt(token).decode())


# ═════════════════════════════════════════════════════════════════════════════
# SESSION-LEVEL ENCRYPTION — for ephemeral in-memory session data
# ═════════════════════════════════════════════════════════════════════════════

def session_encrypt(data: dict, session_id: str) -> bytes:
    """Encrypt session data using session-specific key."""
    return Fernet(_session_key(session_id)).encrypt(json.dumps(data).encode())


def session_decrypt(token: bytes, session_id: str) -> dict:
    """Decrypt session data using session-specific key."""
    if not token:
        return {}
    try:
        return json.loads(Fernet(_session_key(session_id)).decrypt(token).decode())
    except (InvalidToken, json.JSONDecodeError):
        return {}
