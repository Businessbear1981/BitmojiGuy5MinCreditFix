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
    """
    Delete DB records and files for expired sessions. Returns count purged.

    Two clocks, not one. The default is unchanged: a case is destroyed
    `SESSION_TTL_HOURS` after it was created, which is what the privacy page
    promises and what every consumer gets unless they ask otherwise.

    A consumer who subscribes to the Watcher is asking otherwise. Tracking a
    90-day statutory ladder is impossible if the case is gone on day one, so
    subscribing sets `watcher_retain_until` and this loop honours it — the
    case survives until that date and is then destroyed on the normal
    schedule. The extension is opt-in, bounded, shown to the consumer in
    `watcher.retention_notice()` before they agree to it, and reversible:
    cancelling clears the field, and the case is collected on the next pass.

    Retention is never open-ended. A record whose `watcher_retain_until` has
    passed is purged like any other, whether or not it is still marked
    subscribed.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=SESSION_TTL_HOURS)
    db = SessionLocal()

    try:
        candidates = db.query(CaseRecord).filter(CaseRecord.created_at < cutoff).all()
        expired = [
            r for r in candidates
            if not (getattr(r, "watcher_retain_until", None)
                    and r.watcher_retain_until > now)
        ]
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
