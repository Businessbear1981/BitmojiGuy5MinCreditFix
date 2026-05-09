"""
Cypher Security Module — AE 5-Min Credit Fix

Generates per-session encryption keys and provides AES-256 encryption
for all user-uploaded files and generated documents. Nothing is ever
written to disk unencrypted.

Key derivation:
  SHA-256( timestamp_ms + client_ip + CYPHER_SERVER_SECRET )

Encryption:
  AES-256-GCM (authenticated encryption)
"""
import os
import hashlib
import time
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CYPHER_SERVER_SECRET = os.environ.get("CYPHER_SERVER_SECRET", "ae-labs-default-dev-secret-change-in-prod")


def generate_session_key(client_ip: str) -> tuple[str, bytes]:
    """
    Generate a unique per-session encryption key.

    Returns:
        (key_id, raw_key_bytes)
        key_id is a hex string for reference (never logged with PII).
        raw_key_bytes is 32 bytes for AES-256.
    """
    timestamp_ms = str(int(time.time() * 1000))
    material = f"{timestamp_ms}{client_ip}{CYPHER_SERVER_SECRET}"
    key_hash = hashlib.sha256(material.encode("utf-8")).digest()  # 32 bytes

    # key_id is a short identifier derived from the key (not the key itself)
    key_id = hashlib.sha256(key_hash + b"id").hexdigest()[:16]

    return key_id, key_hash


def encrypt(data: bytes, key: bytes) -> bytes:
    """
    Encrypt data with AES-256-GCM.
    Returns: nonce (12 bytes) + ciphertext + tag
    """
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext


def decrypt(encrypted: bytes, key: bytes) -> bytes:
    """
    Decrypt AES-256-GCM encrypted data.
    Input: nonce (12 bytes) + ciphertext + tag
    """
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def encrypt_file_in_memory(file_bytes: bytes, key: bytes) -> bytes:
    """Encrypt an uploaded file. Returns encrypted bytes to store on disk."""
    return encrypt(file_bytes, key)


def decrypt_file_in_memory(encrypted_bytes: bytes, key: bytes) -> bytes:
    """Decrypt a stored file back to plaintext in memory."""
    return decrypt(encrypted_bytes, key)
