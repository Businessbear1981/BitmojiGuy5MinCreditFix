import os
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from crypto_fields import EncryptedJSON, EncryptedString

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./creditfix.db")

# Some hosts hand out postgres:// URLs but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
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
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Client PII — encrypted at rest
    name = Column(EncryptedString, nullable=False)
    address = Column(EncryptedString, nullable=False)
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
    email_sent = Column(Boolean, default=False)
    mail_sent = Column(Boolean, default=False)
    mail_tracking = Column(EncryptedJSON, default=list)

    # Per-session upload encryption key (itself encrypted at rest)
    cypher_key_enc = Column(EncryptedString, nullable=True)

    # Consent audit: timestamp only, no PII
    terms_accepted_at = Column(DateTime, nullable=True)


def init_db():
    # create_all is not multi-worker safe on first boot — workers can race
    # creating the same sequence/table. Treat "already exists" as success.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        msg = str(e).lower()
        if "already exists" not in msg:
            raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
