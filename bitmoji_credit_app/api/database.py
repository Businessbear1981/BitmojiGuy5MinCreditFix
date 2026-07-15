# 5 Minutes to Credit Wellness — Database Layer
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# SQLAlchemy ORM with SQLite. All IDs are UUIDs. All dates UTC.
# PII fields stored encrypted via encryption.py.
# Designed for limited release (5-10 users/day), scales to Postgres by swapping URL.

import os
import uuid
from datetime import datetime, timedelta
from contextlib import contextmanager

from sqlalchemy import (
    create_engine, Column, String, Integer, Boolean, Text, LargeBinary,
    Float, DateTime, Index, event,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///creditfix.db")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {},
    pool_pre_ping=True,
)

# Enable WAL mode for SQLite
if "sqlite" in DB_URL:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.utcnow()


# ═════════════════════════════════════════════════════════════════════════════
# MODELS
# ═════════════════════════════════════════════════════════════════════════════

class Client(Base):
    """Core client record. PII fields are encrypted blobs."""
    __tablename__ = "clients"

    id = Column(String(36), primary_key=True, default=new_uuid)
    session_id = Column(String(36), unique=True, nullable=False, index=True)
    confirmation = Column(String(20), index=True)
    state = Column(String(2), default="")
    status = Column(String(20), default="started", index=True)
    referral_source = Column(String(20), default="")

    # Encrypted PII — stored as bytes, decrypted at read time
    name_enc = Column(LargeBinary)
    email_enc = Column(LargeBinary)
    phone_enc = Column(LargeBinary)
    address_enc = Column(LargeBinary)

    # Payment
    paid = Column(Boolean, default=False)
    paid_at = Column(DateTime)
    payment_method = Column(String(20))

    # Encrypted full profile JSON (dispute items, letters, etc.)
    profile_enc = Column(LargeBinary)

    # Dispute metadata (not PII, used for admin queries)
    dispute_count = Column(Integer, default=0)
    letter_count = Column(Integer, default=0)
    initials = Column(String(2), default="??")

    # Follow-up tracking
    dispatched_at = Column(DateTime)
    follow_up_30_sent = Column(Boolean, default=False)
    follow_up_60_sent = Column(Boolean, default=False)
    follow_up_90_sent = Column(Boolean, default=False)
    follow_up_30_date = Column(DateTime)
    follow_up_60_date = Column(DateTime)
    follow_up_90_date = Column(DateTime)

    # Watcher subscription
    watcher_subscribed = Column(Boolean, default=False)
    watcher_paid_at = Column(DateTime)
    notify_method = Column(String(20), default="email")
    notify_handle_enc = Column(LargeBinary)

    # Lifecycle
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    purge_after = Column(DateTime, index=True)

    __table_args__ = (
        Index("idx_followup", "paid", "follow_up_30_sent", "follow_up_60_sent", "follow_up_90_sent"),
    )


class LedgerBlock(Base):
    """Immutable hash-chain block for audit trail."""
    __tablename__ = "ledger_blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prev_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False)
    session_id = Column(String(36), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    data = Column(Text, nullable=False)
    block_hash = Column(String(64), unique=True, nullable=False)


class AgentLog(Base):
    """Agent action log — who did what, when."""
    __tablename__ = "agent_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)
    agent = Column(String(20), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)


class PipelineEntry(Base):
    """Watcher pipeline — tracks each client through 30/60/90 day milestones."""
    __tablename__ = "pipeline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, index=True)
    confirmation = Column(String(20))
    client_name = Column(String(100))
    client_email = Column(String(200))
    client_phone = Column(String(20))
    state = Column(String(2))
    notify_method = Column(String(20), default="email")
    notify_handle = Column(String(200))
    dispatched_at = Column(DateTime, nullable=False)
    stage = Column(String(20), default="active", index=True)

    day_30_due = Column(DateTime)
    day_30_done = Column(Boolean, default=False)
    day_30_done_at = Column(DateTime)
    day_60_due = Column(DateTime)
    day_60_done = Column(Boolean, default=False)
    day_60_done_at = Column(DateTime)
    day_90_due = Column(DateTime)
    day_90_done = Column(Boolean, default=False)
    day_90_done_at = Column(DateTime)

    letters_generated = Column(Integer, default=0)
    notifications_sent = Column(Integer, default=0)
    last_agent_run = Column(DateTime)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        Index("idx_pipe_30", "day_30_done", "day_30_due"),
        Index("idx_pipe_60", "day_60_done", "day_60_due"),
        Index("idx_pipe_90", "day_90_done", "day_90_due"),
    )


class Notification(Base):
    """Notification log — every email/DM sent or queued."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)
    day = Column(Integer, nullable=False)
    method = Column(String(30), nullable=False)
    handle = Column(String(200))
    delivered = Column(Boolean, default=False)
    message_preview = Column(Text, default="")
    sent_at = Column(DateTime, default=utcnow, nullable=False)


class AdminUser(Base):
    """Admin user with argon2-hashed password."""
    __tablename__ = "admin_users"

    id = Column(String(36), primary_key=True, default=new_uuid)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    last_login = Column(DateTime)


# ═════════════════════════════════════════════════════════════════════════════
# DB SESSION MANAGEMENT
# ═════════════════════════════════════════════════════════════════════════════

@contextmanager
def get_db():
    """Yield a DB session, auto-close on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_dependency():
    """FastAPI Depends() compatible generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═════════════════════════════════════════════════════════════════════════════
# INIT — create all tables
# ═════════════════════════════════════════════════════════════════════════════

def init_db():
    """Create all tables. Safe to call multiple times."""
    Base.metadata.create_all(bind=engine)


# ═════════════════════════════════════════════════════════════════════════════
# CLIENT CRUD
# ═════════════════════════════════════════════════════════════════════════════

def save_client(db: Session, client_data: dict, encrypt_fn) -> Client:
    """Upsert a client record. encrypt_fn(plaintext) -> bytes."""
    sid = client_data["id"]
    now = utcnow()
    purge = now + timedelta(days=90)

    existing = db.query(Client).filter(Client.session_id == sid).first()

    # Compute follow-up dates from paid_at
    fu30 = fu60 = fu90 = None
    paid_at = client_data.get("paid_at")
    if paid_at:
        if isinstance(paid_at, str):
            paid_at = datetime.fromisoformat(paid_at)
        fu30 = paid_at + timedelta(days=30)
        fu60 = paid_at + timedelta(days=60)
        fu90 = paid_at + timedelta(days=90)

    dispatched_at = client_data.get("dispatched_at")
    if dispatched_at and isinstance(dispatched_at, str):
        dispatched_at = datetime.fromisoformat(dispatched_at)

    watcher_paid_at = client_data.get("watcher_paid_at")
    if watcher_paid_at and isinstance(watcher_paid_at, str):
        watcher_paid_at = datetime.fromisoformat(watcher_paid_at)

    import json
    fields = dict(
        session_id=sid,
        confirmation=client_data.get("confirmation"),
        state=client_data.get("state", ""),
        status=client_data.get("status", "started"),
        referral_source=client_data.get("referral_source", ""),
        name_enc=encrypt_fn(client_data.get("name", "")),
        email_enc=encrypt_fn(client_data.get("email", "")),
        phone_enc=encrypt_fn(client_data.get("phone", "")),
        address_enc=encrypt_fn(client_data.get("address", "")),
        paid=bool(client_data.get("paid")),
        paid_at=paid_at if isinstance(paid_at, datetime) else None,
        payment_method=client_data.get("payment_method"),
        profile_enc=encrypt_fn(json.dumps(client_data)),
        dispute_count=len(client_data.get("dispute_items", [])),
        letter_count=len(client_data.get("letters", [])),
        initials=(client_data.get("name", "??")[:2]).upper(),
        dispatched_at=dispatched_at if isinstance(dispatched_at, datetime) else None,
        follow_up_30_date=fu30,
        follow_up_60_date=fu60,
        follow_up_90_date=fu90,
        watcher_subscribed=bool(client_data.get("watcher_subscribed")),
        watcher_paid_at=watcher_paid_at if isinstance(watcher_paid_at, datetime) else None,
        notify_method=client_data.get("notify_method", "email"),
        notify_handle_enc=encrypt_fn(client_data.get("notify_handle", "")),
        updated_at=now,
        purge_after=purge,
    )

    if existing:
        for k, v in fields.items():
            if k != "session_id":
                setattr(existing, k, v)
        db.commit()
        return existing
    else:
        fields["created_at"] = now
        client = Client(**fields)
        db.add(client)
        db.commit()
        db.refresh(client)
        return client


def load_client(db: Session, session_id: str, decrypt_fn) -> dict | None:
    """Load and decrypt full profile by session_id."""
    import json
    client = db.query(Client).filter(Client.session_id == session_id).first()
    if not client or not client.profile_enc:
        return None
    try:
        return json.loads(decrypt_fn(client.profile_enc))
    except Exception:
        return None


def load_client_by_confirmation(db: Session, code: str) -> dict | None:
    """Load minimal non-PII info by confirmation code."""
    client = db.query(Client).filter(Client.confirmation == code).first()
    if not client:
        return None
    return {
        "session_id": client.session_id,
        "confirmation": client.confirmation,
        "state": client.state,
        "status": client.status,
        "paid": client.paid,
        "dispute_count": client.dispute_count,
        "created_at": client.created_at.isoformat() if client.created_at else None,
    }


def get_all_clients_admin(db: Session, decrypt_fn) -> list[dict]:
    """All clients for admin dashboard, PII decrypted."""
    clients = db.query(Client).order_by(Client.created_at.desc()).all()
    results = []
    for c in clients:
        entry = {
            "session_id": c.session_id,
            "confirmation": c.confirmation,
            "state": c.state,
            "status": c.status,
            "paid": c.paid,
            "paid_at": c.paid_at.isoformat() if c.paid_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "initials": c.initials,
            "referral_source": c.referral_source,
            "dispute_count": c.dispute_count,
            "letter_count": c.letter_count,
            "follow_up_30_sent": c.follow_up_30_sent,
            "follow_up_60_sent": c.follow_up_60_sent,
            "follow_up_90_sent": c.follow_up_90_sent,
        }
        for field, enc_attr in [("name", "name_enc"), ("email", "email_enc"), ("phone", "phone_enc")]:
            raw = getattr(c, enc_attr)
            try:
                entry[field] = decrypt_fn(raw) if raw else ""
            except Exception:
                entry[field] = ""
        results.append(entry)
    return results


def get_due_followups(db: Session, day: int) -> list[Client]:
    """Get clients needing follow-up at the given day mark (30, 60, or 90)."""
    now = utcnow()
    q = db.query(Client).filter(Client.paid == True)
    if day == 30:
        q = q.filter(Client.follow_up_30_sent == False, Client.follow_up_30_date <= now)
    elif day == 60:
        q = q.filter(Client.follow_up_30_sent == True, Client.follow_up_60_sent == False, Client.follow_up_60_date <= now)
    elif day == 90:
        q = q.filter(Client.follow_up_60_sent == True, Client.follow_up_90_sent == False, Client.follow_up_90_date <= now)
    else:
        return []
    return q.all()


def mark_followup_sent(db: Session, session_id: str, day: int):
    """Mark a follow-up day as sent."""
    client = db.query(Client).filter(Client.session_id == session_id).first()
    if not client:
        return
    if day == 30:
        client.follow_up_30_sent = True
    elif day == 60:
        client.follow_up_60_sent = True
    elif day == 90:
        client.follow_up_90_sent = True
    client.updated_at = utcnow()
    db.commit()


def delete_expired_clients(db: Session) -> int:
    """Purge all client records older than 90 days."""
    now = utcnow()
    count = db.query(Client).filter(Client.purge_after <= now).delete()
    db.commit()
    if count:
        print(f"[PURGE] Deleted {count} expired client records")
    return count


def get_stats(db: Session) -> dict:
    """Aggregate stats for admin dashboard."""
    from sqlalchemy import func
    row = db.query(
        func.count(Client.id).label("total"),
        func.sum(func.cast(Client.paid, Integer)).label("paid"),
        func.sum(func.cast(Client.follow_up_30_sent, Integer)).label("fu30"),
        func.sum(func.cast(Client.follow_up_60_sent, Integer)).label("fu60"),
        func.sum(func.cast(Client.follow_up_90_sent, Integer)).label("fu90"),
    ).first()

    total = row.total or 0
    paid = row.paid or 0

    # Referral source breakdown
    ref_rows = (
        db.query(Client.referral_source, func.count(Client.id).label("count"))
        .filter(Client.referral_source != "", Client.referral_source.isnot(None))
        .group_by(Client.referral_source)
        .all()
    )

    return {
        "total": total,
        "paid": paid,
        "pending": total - paid,
        "revenue": round(paid * 24.99, 2),
        "fu30": row.fu30 or 0,
        "fu60": row.fu60 or 0,
        "fu90": row.fu90 or 0,
        "referral_sources": {r.referral_source: r.count for r in ref_rows},
    }
