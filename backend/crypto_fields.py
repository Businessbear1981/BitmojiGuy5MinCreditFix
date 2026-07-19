"""
Field-level encryption for PII columns (ADR-0002 encrypted-ephemeral).

AES-256-GCM with a server-wide key from PII_ENCRYPTION_KEY. Values are stored
as base64("enc1:" prefix + nonce + ciphertext) so plaintext PII never reaches
the database. SQLAlchemy TypeDecorators keep the model code transparent.
"""
import base64
import json
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from config import PII_ENCRYPTION_KEY

_PREFIX = "enc1:"


def _key() -> bytes:
    raw = base64.urlsafe_b64decode(PII_ENCRYPTION_KEY.encode())
    if len(raw) != 32:
        raise RuntimeError("PII_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return raw


def encrypt_str(plaintext: str) -> str:
    nonce = secrets.token_bytes(12)
    ct = AESGCM(_key()).encrypt(nonce, plaintext.encode("utf-8"), None)
    return _PREFIX + base64.b64encode(nonce + ct).decode("ascii")


def decrypt_str(stored: str) -> str:
    if not stored.startswith(_PREFIX):
        # Legacy plaintext row (pre-encryption) — pass through
        return stored
    blob = base64.b64decode(stored[len(_PREFIX):])
    nonce, ct = blob[:12], blob[12:]
    return AESGCM(_key()).decrypt(nonce, ct, None).decode("utf-8")


class EncryptedString(TypeDecorator):
    """Transparently encrypts a string column at rest."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_str(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_str(value)


class EncryptedJSON(TypeDecorator):
    """JSON-serializes then encrypts a column at rest."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_str(json.dumps(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(decrypt_str(value))
