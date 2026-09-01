"""
Central environment configuration.

Production fails closed: required secrets must be set or the app refuses to
boot. Development falls back to deterministic dev-only values so the flow
works out of the box.
"""
import base64
import hashlib
import os

from dotenv import load_dotenv

load_dotenv()

_VALID_ENVIRONMENTS = ("production", "development", "test")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "").strip().lower()

# This used to default to "development", and nothing in the Dockerfile,
# railway.toml or nixpacks.toml ever set it. A deploy that simply forgot the
# variable therefore ran as development, silently and with no signal on
# /api/health — which meant the dev fallback keys below (a SHA-256 of a public
# string, in a public repo), unsigned Stripe webhooks accepted as proof of
# payment, unverified Lob webhooks, and no "*" check on ALLOWED_ORIGINS.
#
# Refusing to boot is the correct failure. An app that will not start is a
# five-minute problem; an app serving customer PII under a key anyone can
# compute from GitHub is not.
if not ENVIRONMENT:
    raise RuntimeError(
        "ENVIRONMENT is not set. Set it to one of: "
        f"{', '.join(_VALID_ENVIRONMENTS)}. Refusing to guess — the previous "
        "default of 'development' silently enabled publicly-derivable "
        "encryption keys and unsigned payment webhooks."
    )
if ENVIRONMENT not in _VALID_ENVIRONMENTS:
    raise RuntimeError(
        f"ENVIRONMENT={ENVIRONMENT!r} is not recognised. Expected one of: "
        f"{', '.join(_VALID_ENVIRONMENTS)}. A typo such as 'Production' or "
        "'prod' would previously have been treated as development."
    )

IS_PROD = ENVIRONMENT == "production"

DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() in ("true", "1", "yes")


def _require(name: str, dev_default: str = "") -> str:
    value = os.environ.get(name, "")
    if value:
        return value
    if IS_PROD:
        raise RuntimeError(f"{name} must be set when ENVIRONMENT=production")
    return dev_default


def _dev_key(label: str) -> str:
    """Deterministic dev-only key so local restarts keep working."""
    raw = hashlib.sha256(f"ae-creditfix-dev-{label}".encode()).digest()
    return base64.urlsafe_b64encode(raw).decode()


# Secrets — fail closed in production
PII_ENCRYPTION_KEY = _require("PII_ENCRYPTION_KEY", _dev_key("pii"))
TERMS_TOKEN_SECRET = _require("TERMS_TOKEN_SECRET", _dev_key("terms"))
CYPHER_SERVER_SECRET = _require("CYPHER_SERVER_SECRET", _dev_key("cypher"))

# Admin: no default ever. Endpoints are disabled when unset (fail closed).
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
if IS_PROD and not ADMIN_KEY:
    raise RuntimeError("ADMIN_KEY must be set when ENVIRONMENT=production")

# Stripe
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
if IS_PROD and STRIPE_SECRET_KEY and not STRIPE_WEBHOOK_SECRET:
    raise RuntimeError("STRIPE_WEBHOOK_SECRET must be set when Stripe is live")

# Price: $24.99 one-time (confirmed with Sean 2026-07-04)
STRIPE_PRICE_CENTS = 2499
PRICE_DISPLAY = "$24.99"

# The Watcher. 0 means tracking is included in the base price, which is
# what beta ships as. Set a value only once checkout is actually wired —
# a price displayed but never charged is worse than no price at all.
WATCHER_PRICE_CENTS = int(os.environ.get("WATCHER_PRICE_CENTS", "0"))

# Manual pay (Cash App / Chime): customer sends money to Sean directly and the
# admin releases their letters after verifying receipt. Tags confirmed with
# Sean 2026-07-19 (Cash App cashtag = $5mincreditfix).
CASHAPP_CASHTAG = os.environ.get("CASHAPP_CASHTAG", "$5mincreditfix")
CHIME_TAG = os.environ.get("CHIME_TAG", "$AELabsPay")

# URLs
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
if IS_PROD and "*" in ALLOWED_ORIGINS:
    raise RuntimeError("ALLOWED_ORIGINS must not contain * in production")

# Ephemeral data retention
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "24"))

# Optional persistent rate-limit backend (e.g. redis://...); memory otherwise
RATE_LIMIT_STORAGE_URI = os.environ.get("RATE_LIMIT_STORAGE_URI", "memory://")

# Optional error tracking. When unset, Sentry is disabled entirely.
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
