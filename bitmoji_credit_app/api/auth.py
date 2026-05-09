# 5 Minutes to Credit Wellness — Admin Authentication
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# Argon2 password hashing for admin users.
# JWT session tokens with configurable expiry.
# First-run auto-creates admin from ADMIN_KEY env var.

import os
import secrets
from datetime import datetime, timedelta

import argon2
import jwt

from api.database import AdminUser, get_db, utcnow

PASSWORD_HASHER = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
)

JWT_SECRET = os.environ.get("JWT_SECRET", os.environ.get("SECRET_KEY", "ae-jwt-dev-secret"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "8"))

ADMIN_KEY = os.environ.get("ADMIN_KEY", "ae-admin-2025")


def hash_password(password: str) -> str:
    """Hash a password with argon2id."""
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against an argon2id hash."""
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (argon2.exceptions.VerifyMismatchError, argon2.exceptions.InvalidHashError):
        return False


def create_token(username: str) -> str:
    """Create a JWT session token for an admin user."""
    payload = {
        "sub": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def ensure_admin_exists():
    """Create default admin user from ADMIN_KEY if no admin users exist."""
    with get_db() as db:
        count = db.query(AdminUser).count()
        if count == 0:
            admin = AdminUser(
                username="admin",
                password_hash=hash_password(ADMIN_KEY),
            )
            db.add(admin)
            db.commit()
            print("[AUTH] Default admin user created from ADMIN_KEY")


def authenticate(username: str, password: str) -> str | None:
    """Authenticate an admin user. Returns JWT token or None."""
    with get_db() as db:
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        user.last_login = utcnow()
        db.commit()
        return create_token(username)


def get_current_admin(token: str) -> str | None:
    """Validate token and return username, or None if invalid/expired."""
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("sub")
