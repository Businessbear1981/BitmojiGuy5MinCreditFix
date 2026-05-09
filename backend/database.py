import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime, Float, Text, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./creditfix.db")

# Render PostgreSQL URLs start with postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class CaseRecord(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(24), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Client info
    name = Column(String(200), nullable=False)
    address = Column(String(500), nullable=False)
    dob = Column(String(20), nullable=False)
    ssn_last4 = Column(String(4), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(200), nullable=False)

    # Attachments (filenames as JSON array)
    attachments = Column(JSON, default=list)

    # Dispute items (JSON array of item dicts)
    items = Column(JSON, default=list)

    # Generated letters (JSON array of letter dicts)
    letters = Column(JSON, default=list)

    # Phases / status tracking
    docs_complete = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)
    stripe_session_id = Column(String(200), nullable=True)
    stripe_payment_intent = Column(String(200), nullable=True)

    # Email
    email_sent = Column(Boolean, default=False)

    # Certified mail (Lob)
    mail_sent = Column(Boolean, default=False)
    mail_tracking = Column(JSON, default=list)

    # Letter content stored as text (bundled)
    letter_bundle_text = Column(Text, nullable=True)
    # PDF binary stored as path reference
    letter_pdf_path = Column(String(500), nullable=True)

    # Cypher security
    cypher_key_id = Column(String(16), nullable=True)
    # Store the encrypted session key (encrypted with server master key)
    cypher_key_enc = Column(Text, nullable=True)

    # Terms acceptance (timestamp + session_id only, no PII)
    terms_accepted_at = Column(DateTime, nullable=True)


class RateLimit(Base):
    """Track rate limits by IP."""
    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True)
    ip = Column(String(50), index=True)
    endpoint = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
