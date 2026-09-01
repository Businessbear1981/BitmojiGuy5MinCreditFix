"""
The background pass that actually sends the reminders.

`watcher.py` computes when a milestone is due. Nothing in the request path
ever fires a notification, because a consumer who never reopens the site is
exactly the consumer who needs the reminder — and they will never make the
request that would trigger it. So this loop runs alongside `cleanup_loop`.

── Every send is recorded before it is attempted ──────────────────────────

The log entry is written and committed *before* the SMTP call, then updated
with the result. That ordering is deliberate: a crash mid-send leaves a row
marked undelivered, which is recoverable and visible. The opposite ordering
loses the record of an email that did go out, and the consumer gets the same
reminder every hour until the process stops crashing.

── Idempotency is by (milestone, case), not by time ───────────────────────

`_already_sent()` checks the case's own notification log rather than any
scheduler state, so restarting the process, running two workers, or resuming
after an outage cannot double-send. A duplicate reminder is not catastrophic,
but it reads as a system that is not in control of itself, and this product
asks people to trust it with a credit file.

── It never sends to a channel it cannot deliver on ───────────────────────

Only `email` is deliverable — see `watcher.CHANNELS`. A case somehow carrying
a Snapchat handle is skipped and logged as undeliverable rather than silently
marked sent.
"""
from __future__ import annotations

import asyncio
from datetime import datetime

import config
import watcher
from database import CaseRecord, SessionLocal
from email_sender import send_watcher_reminder

# Hourly is ample for day-granularity milestones and keeps the load trivial.
CHECK_INTERVAL_SECONDS = 3600


def _already_sent(record: CaseRecord, day: int) -> bool:
    return any(
        isinstance(n, dict) and n.get("day") == day
        for n in (record.watcher_notifications or [])
    )


def _log(record, db, day: int, method: str, delivered: bool, note: str = "") -> None:
    """Append one entry. Reassigns the list so SQLAlchemy sees the mutation."""
    entries = list(record.watcher_notifications or [])
    entries.append({
        "day": day,
        "method": method,
        "sent_at": datetime.utcnow().isoformat(timespec="seconds"),
        "delivered": delivered,
        "note": note,
    })
    record.watcher_notifications = entries
    db.commit()


def send_due_notifications() -> int:
    """One pass. Returns how many reminders were dispatched."""
    db = SessionLocal()
    sent = 0
    try:
        subscribers = (
            db.query(CaseRecord)
            .filter(CaseRecord.watcher_subscribed.is_(True))
            .all()
        )

        for record in subscribers:
            method = record.watcher_notify_method or "email"
            handle = record.watcher_notify_handle or ""
            channel = watcher.CHANNELS.get(method, {})

            milestones = watcher.milestones_for(record)
            for key, ms in milestones.items():
                day = ms["day"]
                if not ms["reached"] or _already_sent(record, day):
                    continue

                if not channel.get("available") or not handle:
                    # Record the miss rather than pretending it went out.
                    _log(record, db, day, method, False,
                         "channel cannot be delivered to")
                    continue

                # Write first, then attempt — see the module docstring.
                _log(record, db, day, method, False, "sending")
                ok = False
                try:
                    ok = send_watcher_reminder(
                        to_email=handle,
                        client_name=record.name or "",
                        session_id=record.session_id,
                        milestone=ms,
                        frontend_url=config.FRONTEND_URL,
                    )
                except Exception as e:
                    print(f"[watcher] send error: {type(e).__name__}")

                entries = list(record.watcher_notifications or [])
                if entries:
                    entries[-1]["delivered"] = bool(ok)
                    entries[-1]["note"] = "" if ok else "delivery failed"
                    record.watcher_notifications = entries
                    db.commit()

                if ok:
                    sent += 1

        if sent:
            # Count only. Never log a handle, a name, or a session id.
            print(f"[watcher] sent {sent} reminder(s)")
        return sent
    finally:
        db.close()


async def watcher_loop():
    """Background loop, started from the app lifespan alongside cleanup."""
    while True:
        try:
            send_due_notifications()
        except Exception as e:
            print(f"[watcher] error: {type(e).__name__}")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
