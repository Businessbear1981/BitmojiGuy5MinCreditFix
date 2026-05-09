"""
Auto-cleanup: delete all session data older than 24 hours.
Runs as a background task on app startup.
"""
import asyncio
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import delete
from database import SessionLocal, CaseRecord


EXPIRE_HOURS = 24
CLEANUP_INTERVAL_SECONDS = 3600  # check every hour

# Directories that hold encrypted session files
DATA_DIRS = [
    Path(__file__).resolve().parent / "uploads",
    Path(__file__).resolve().parent / "session_data",
    Path(__file__).resolve().parent / "generated_pdfs",
]


def purge_expired_sessions():
    """Delete DB records and files for sessions older than 24 hours."""
    cutoff = datetime.utcnow() - timedelta(hours=EXPIRE_HOURS)
    db = SessionLocal()

    try:
        expired = db.query(CaseRecord).filter(CaseRecord.created_at < cutoff).all()
        count = 0

        for record in expired:
            sid = record.session_id
            # Remove session files from all data directories
            for base in DATA_DIRS:
                session_dir = base / sid
                if session_dir.is_dir():
                    shutil.rmtree(session_dir, ignore_errors=True)
                # Also check for flat files named with session_id
                for f in base.glob(f"*{sid}*"):
                    f.unlink(missing_ok=True)

            # Remove PDF if it exists
            if record.letter_pdf_path:
                pdf = Path(record.letter_pdf_path)
                pdf.unlink(missing_ok=True)

            db.delete(record)
            count += 1

        if count:
            db.commit()
            # Log session count only — never log PII
            print(f"[cleanup] purged {count} expired session(s)")
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
