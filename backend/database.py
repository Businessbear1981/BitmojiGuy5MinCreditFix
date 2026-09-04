import os
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import TypeDecorator

from crypto_fields import EncryptedJSON, EncryptedString


def utcnow() -> datetime:
    """The only clock this application reads. Always timezone-aware UTC."""
    return datetime.now(timezone.utc)


class UtcDateTime(TypeDecorator):
    """
    A DateTime that is timezone-aware UTC everywhere in Python, and stored on
    disk in exactly the format the existing rows already use.

    Two databases disagree about timezones: SQLite has no timezone type and
    hands back naive values, while Postgres `timestamptz` hands back aware
    ones. Left alone, that difference means a comparison which passes in dev
    (SQLite, naive both sides) raises `TypeError: can't compare offset-naive
    and offset-aware datetimes` in production — and the first place it would
    bite is the 24-hour purge loop, which is the ADR-0002 guarantee.

    So the conversion happens here, once, instead of at every call site:

      * on write  — an aware value is converted to UTC and the tzinfo dropped,
        so what lands on disk is naive UTC, byte-identical to every row
        written before this change. No migration, no DDL change, no rewrite
        of existing data.
      * on read   — a naive value is stamped as UTC.

    Naive values written by any remaining caller are assumed to be UTC, which
    is what the codebase has always meant by a naive timestamp. Application
    code above this layer can now assume every timestamp is aware.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc)
        return value.replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./creditfix.db")

# Some hosts hand out postgres:// URLs but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
engine_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Postgres behind a pooler drops idle connections, and SQLAlchemy hands
    # the dead one to the next caller: the first customer after a quiet spell
    # gets `server closed the connection unexpectedly` as a 500, then it works
    # on refresh — the hardest shape of bug to diagnose from support tickets.
    # `pool_pre_ping` costs one round trip and removes the whole class.
    #
    # The pool is kept small on purpose. Two uvicorn workers at the default
    # pool of 5 plus 10 overflow is 30 connections against a Supavisor tier
    # that may cap lower, and exhausting the pooler fails every request rather
    # than queueing.
    engine_args = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 3,
        "max_overflow": 2,
    }

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class CaseRecord(Base):
    """
    One customer dispute case. PII columns are encrypted at rest (AES-GCM)
    and every record is hard-deleted after SESSION_TTL_HOURS (ADR-0002).
    """

    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(24), unique=True, index=True, nullable=False)
    created_at = Column(UtcDateTime, default=utcnow, index=True)

    # Client PII — encrypted at rest
    name = Column(EncryptedString, nullable=False)
    # Street line only. City/state/ZIP are separate columns because the mail
    # carrier needs them as separate fields: splitting a free-text address on
    # commas put "Apt 3B" in the city field and "Austin" in the state field,
    # Lob rejected the payload, the error was swallowed, and the customer was
    # told their letters had been posted when nothing had been.
    address = Column(EncryptedString, nullable=False)
    city = Column(EncryptedString, nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(10), nullable=True)
    dob = Column(EncryptedString, nullable=False)
    ssn_last4 = Column(EncryptedString, nullable=False)
    phone = Column(EncryptedString, nullable=False)
    email = Column(EncryptedString, nullable=False)

    # Case contents — encrypted at rest (contain PII)
    attachments = Column(EncryptedJSON, default=list)
    items = Column(EncryptedJSON, default=list)
    letters = Column(EncryptedJSON, default=list)

    # Status flags (no PII)
    region = Column(String(2), nullable=True, index=True)
    docs_complete = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)
    stripe_session_id = Column(String(200), nullable=True)
    stripe_payment_intent = Column(String(200), nullable=True)
    # Manual pay (Cash App / Chime): customer sends money directly, admin
    # verifies receipt and releases. Code goes in the payment memo.
    manual_pay_method = Column(String(20), nullable=True)
    manual_pay_code = Column(String(24), nullable=True)
    # The customer's own cashtag / Chime handle, so the admin can match the
    # incoming payment to the case without decoding a memo field.
    manual_pay_handle = Column(EncryptedString, nullable=True)
    manual_pay_requested_at = Column(UtcDateTime, nullable=True)
    manual_pay_released_at = Column(UtcDateTime, nullable=True)
    email_sent = Column(Boolean, default=False)
    mail_sent = Column(Boolean, default=False)
    mail_tracking = Column(EncryptedJSON, default=list)
    # When round 1 actually went into the mail. The escalation ladder and the
    # Watcher both measure from here, not from case creation — a case can sit
    # unpaid for a week before anything is sent.
    mail_dispatched_at = Column(UtcDateTime, nullable=True)
    # Highest tier mailed so far, so a re-run cannot silently repeat a round.
    mail_tier = Column(Integer, default=0)

    # Per-session upload encryption key (itself encrypted at rest)
    cypher_key_enc = Column(EncryptedString, nullable=True)

    # Consent audit: timestamp only, no PII
    terms_accepted_at = Column(UtcDateTime, nullable=True)
    # Disclosure acknowledgements — which statements were affirmed, the version
    # of the text shown, and when. No PII beyond a hashed IP.
    acknowledgements = Column(EncryptedJSON, nullable=True)
    acknowledged_at = Column(UtcDateTime, nullable=True)
    # The consumer's e-signature: the PNG mark plus the intent evidence that
    # makes it meaningful under E-SIGN. Encrypted, purged with the case.
    signature = Column(EncryptedJSON, nullable=True)
    signed_at = Column(UtcDateTime, nullable=True)

    # ── The Watcher: 30/60/90-day tracking ──────────────────────────────
    # `watcher_retain_until` is the only thing that exempts a case from the
    # 24-hour purge, and it is only ever set by a consumer subscribing. See
    # watcher.retention_notice() for the sentence they have to read first.
    # Tracking is a separate purchase on its own screen. `paid` covers the
    # letters; this covers the tracker, and the tracker is what escalates a
    # case to certified mail on three bureaus.
    watcher_paid = Column(Boolean, default=False)
    watcher_stripe_session_id = Column(String(200), nullable=True)
    watcher_subscribed = Column(Boolean, default=False)
    watcher_subscribed_at = Column(UtcDateTime, nullable=True)
    watcher_retain_until = Column(UtcDateTime, nullable=True, index=True)
    watcher_notify_method = Column(String(20), nullable=True)
    # A contact handle is PII and is encrypted like every other identifier.
    watcher_notify_handle = Column(EncryptedString, nullable=True)
    # Tiers already generated, so a round is never silently rebuilt.
    watcher_rounds = Column(EncryptedJSON, default=list)
    watcher_notifications = Column(EncryptedJSON, default=list)


def init_db():
    # create_all is not multi-worker safe on first boot — workers can race
    # creating the same sequence/table. Treat "already exists" as success.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        msg = str(e).lower()
        if "already exists" not in msg:
            raise
    _ensure_columns()


# Columns added after the initial schema. create_all never alters existing
# tables, so add them at boot (idempotent; safe across multiple workers).
_ADDED_COLUMNS = [
    ("city", "TEXT"),
    ("state", "VARCHAR(2)"),
    ("zip_code", "VARCHAR(10)"),
    ("manual_pay_method", "VARCHAR(20)"),
    ("manual_pay_code", "VARCHAR(24)"),
    ("manual_pay_requested_at", "TIMESTAMP"),
    ("manual_pay_released_at", "TIMESTAMP"),
    ("mail_dispatched_at", "TIMESTAMP"),
    ("mail_tier", "INTEGER"),
    ("manual_pay_handle", "TEXT"),
    ("acknowledgements", "TEXT"),
    ("acknowledged_at", "TIMESTAMP"),
    ("signature", "TEXT"),
    ("signed_at", "TIMESTAMP"),
    # Tracking is sold separately on its own screen, so whether it was paid
    # for is its own fact — `paid` covers the letters and nothing more.
    ("watcher_paid", "BOOLEAN"),
    ("watcher_stripe_session_id", "VARCHAR(200)"),
    ("watcher_subscribed", "BOOLEAN"),
    ("watcher_subscribed_at", "TIMESTAMP"),
    ("watcher_retain_until", "TIMESTAMP"),
    ("watcher_notify_method", "VARCHAR(20)"),
    ("watcher_notify_handle", "TEXT"),
    ("watcher_rounds", "TEXT"),
    ("watcher_notifications", "TEXT"),
]


def _ensure_columns():
    from sqlalchemy import inspect, text

    existing = {c["name"] for c in inspect(engine).get_columns("cases")}
    for name, ddl_type in _ADDED_COLUMNS:
        if name in existing:
            continue
        try:
            # One transaction per ALTER: a lost race (another worker added the
            # column first) must not poison the remaining statements.
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE cases ADD COLUMN {name} {ddl_type}"))
        except Exception as e:
            if "duplicate" not in str(e).lower() and "already exists" not in str(e).lower():
                raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
