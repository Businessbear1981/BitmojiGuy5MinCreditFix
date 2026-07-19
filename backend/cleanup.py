"""
Auto-cleanup: hard-delete all session data older than SESSION_TTL_HOURS
(ADR-0002 encrypted-ephemeral). Runs as a background task on app startup.
"""
import asyncio
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from config import SESSION_TTL_HOURS
from database import CaseRecord, SessionLocal

CLEANUP_INTERVAL_SECONDS = 3600  # check every hour

# Directories that hold encrypted session files
DATA_DIRS = [
    Path(__file__).resolve().parent / "uploads",
]


def purge_expired_sessions() -> int:
    """Delete DB records and files for expired sessions. Returns count purged."""
    cutoff = datetime.utcnow() - timedelta(hours=SESSION_TTL_HOURS)
    db = SessionLocal()

    try:
        expired = db.query(CaseRecord).filter(CaseRecord.created_at < cutoff).all()
        count = 0

        for record in expired:
            sid = record.session_id
            for base in DATA_DIRS:
                session_dir = base / sid
                if session_dir.is_dir():
                    shutil.rmtree(session_dir, ignore_errors=True)

            db.delete(record)
            count += 1

        if count:
            db.commit()
            # Log session count only — never log PII
            print(f"[cleanup] purged {count} expired session(s)")
        return count
    finally:
        db.close()


async def cleanup_loop():
    """Background loop that runs purge every hour."""
    while True:
        try:
            purge_expired_sessions()
        except Exception as e:
            # Log error type only, never data contents
            print(f"[cleanup] error: {type(e).__name__}")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
