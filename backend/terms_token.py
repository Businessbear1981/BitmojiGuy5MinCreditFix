"""
Stateless terms-acceptance tokens.

HMAC-signed timestamp instead of server-side cache, so any worker can verify
a token issued by any other worker and nothing survives a restart.
"""
import hashlib
import hmac
import time
from datetime import datetime, timezone
from typing import Optional

from config import TERMS_TOKEN_SECRET

TOKEN_TTL_SECONDS = 30 * 60


def _sign(ts: str) -> str:
    return hmac.new(TERMS_TOKEN_SECRET.encode(), ts.encode(), hashlib.sha256).hexdigest()[:32]


def issue_token() -> tuple[str, datetime]:
    """Returns (token, accepted_at)."""
    now = int(time.time())
    ts = str(now)
    return f"{ts}.{_sign(ts)}", datetime.fromtimestamp(now, tz=timezone.utc)


def verify_token(token: str) -> Optional[datetime]:
    """Returns the acceptance timestamp if the token is valid and fresh."""
    try:
        ts, sig = token.split(".", 1)
        issued = int(ts)
    except (ValueError, AttributeError):
        return None
    if not hmac.compare_digest(sig, _sign(ts)):
        return None
    if time.time() - issued > TOKEN_TTL_SECONDS:
        return None
    return datetime.fromtimestamp(issued, tz=timezone.utc)
