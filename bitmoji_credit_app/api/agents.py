# 5 Minutes to Credit Wellness — Watcher Pipeline Agents
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# Three pipeline agents: Agent30, Agent60, Agent90.
# Each queries the pipeline table, generates follow-up letters,
# sends notifications, and logs actions to the ledger.

import os
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy.orm import Session

from api.database import (
    Client, PipelineEntry, get_db, utcnow,
    load_client, mark_followup_sent, save_client,
)
from api.encryption import encrypt, decrypt, decrypt_json
from api.ledger import write_block, log_action
from api.followup import generate_followup_letters


def send_email(to_addr: str, subject: str, body: str) -> bool:
    """Send email via SMTP. Returns True if sent."""
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_user = os.environ.get("SMTP_USER", "")
    if not smtp_host or not smtp_user:
        print(f"[AGENT EMAIL SKIP] No SMTP -> {to_addr}: {subject}")
        return False
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = os.environ.get("FROM_EMAIL", "noreply@aelabs.com")
        msg["To"] = to_addr
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(smtp_host, int(os.environ.get("SMTP_PORT", "587"))) as s:
            s.starttls()
            s.login(smtp_user, os.environ.get("SMTP_PASS", ""))
            s.sendmail(msg["From"], to_addr, msg.as_string())
        return True
    except Exception as e:
        print(f"[AGENT EMAIL ERROR] {e}")
        return False


def enroll_client(db: Session, profile: dict):
    """Add a watcher-subscribed client to the pipeline."""
    dispatched = profile.get("dispatched_at", utcnow().isoformat())
    try:
        dispatch_dt = datetime.fromisoformat(dispatched) if isinstance(dispatched, str) else dispatched
    except (ValueError, TypeError):
        dispatch_dt = utcnow()

    existing = db.query(PipelineEntry).filter(PipelineEntry.session_id == profile["id"]).first()
    if existing:
        return

    write_block(db, profile["id"], "enroll", {
        "confirmation": profile.get("confirmation", ""),
        "dispatched_at": dispatch_dt.isoformat(),
    })

    entry = PipelineEntry(
        session_id=profile["id"],
        confirmation=profile.get("confirmation", ""),
        client_name=profile.get("name", ""),
        client_email=profile.get("email", ""),
        client_phone=profile.get("phone", ""),
        state=profile.get("state", ""),
        notify_method=profile.get("notify_method", "email"),
        notify_handle=profile.get("notify_handle", profile.get("email", "")),
        dispatched_at=dispatch_dt,
        day_30_due=dispatch_dt + timedelta(days=30),
        day_60_due=dispatch_dt + timedelta(days=60),
        day_90_due=dispatch_dt + timedelta(days=90),
    )
    db.add(entry)
    db.commit()


def _process_bucket(db: Session, day: int, agent_name: str):
    """Generic processor for a day bucket (30, 60, or 90)."""
    now = utcnow()
    q = db.query(PipelineEntry).filter(PipelineEntry.stage == "active")

    if day == 30:
        q = q.filter(PipelineEntry.day_30_done == False, PipelineEntry.day_30_due <= now)
    elif day == 60:
        q = q.filter(PipelineEntry.day_30_done == True, PipelineEntry.day_60_done == False, PipelineEntry.day_60_due <= now)
    elif day == 90:
        q = q.filter(PipelineEntry.day_60_done == True, PipelineEntry.day_90_done == False, PipelineEntry.day_90_due <= now)

    queue = q.all()
    processed = 0

    for deal in queue:
        sid = deal.session_id
        profile = load_client(db, sid, decrypt_json)
        letter_count = 0

        if profile:
            letters = generate_followup_letters(profile, day)
            letter_count = len(letters)
            profile.setdefault("follow_up_letters", {})[str(day)] = letters
            profile.setdefault("follow_up_history", []).append({
                "day": day,
                "date": now.isoformat(),
                "letter_count": letter_count,
                "agent": agent_name,
            })
            save_client(db, profile, encrypt)
            mark_followup_sent(db, sid, day)

        # Send notification
        delivered = False
        if deal.notify_method == "email" and deal.notify_handle:
            day_labels = {30: "30-Day Follow-Up", 60: "60-Day Escalation", 90: "90-Day Final Demand"}
            subject = f"5 Minutes to Credit Wellness — {day_labels[day]} for {deal.confirmation}"
            body = _build_notification_body(day, deal.client_name, deal.confirmation, deal.state, letter_count)
            delivered = send_email(deal.notify_handle, subject, body)

        # Update pipeline
        if day == 30:
            deal.day_30_done = True
            deal.day_30_done_at = now
        elif day == 60:
            deal.day_60_done = True
            deal.day_60_done_at = now
        elif day == 90:
            deal.day_90_done = True
            deal.day_90_done_at = now
            deal.stage = "complete"

        deal.letters_generated = (deal.letters_generated or 0) + letter_count
        deal.notifications_sent = (deal.notifications_sent or 0) + 1
        deal.last_agent_run = now
        db.commit()

        log_action(db, sid, agent_name, "processed", json.dumps({
            "letters": letter_count,
            "notify": deal.notify_method,
            "delivered": delivered,
            "confirmation": deal.confirmation,
        }))

        processed += 1
        print(f"[{agent_name}] Processed {deal.confirmation} — {letter_count} letters")

    return processed


def _build_notification_body(day: int, name: str, conf: str, state: str, letter_count: int) -> str:
    if day == 30:
        return (
            f"Hi {name},\n\n"
            f"Your 30-day FCRA response window has closed for dispute {conf}.\n\n"
            f"The bureaus had 30 days to respond under FCRA Section 611(a)(1). "
            f"Your {letter_count} follow-up letters are ready.\n\n"
            f"Log in to download and send via certified mail.\n\n"
            f"-- Your Credit Dispute Team\nRef: {conf}"
        )
    elif day == 60:
        return (
            f"Hi {name},\n\n"
            f"60 days since your initial dispute {conf}.\n\n"
            f"Your escalation letters cite Cushman v. Trans Union Corp. and Johnson v. MBNA — "
            f"demanding the METHOD OF VERIFICATION.\n\n"
            f"Your {letter_count} escalation letters are ready.\n\n"
            f"-- Your Credit Dispute Team\nRef: {conf}"
        )
    else:
        return (
            f"Hi {name},\n\n"
            f"90 days. Legal action threshold for dispute {conf}.\n\n"
            f"You now have standing to:\n"
            f"- File a CFPB complaint at consumerfinance.gov/complaint\n"
            f"- File an FTC complaint at reportfraud.ftc.gov\n"
            f"- Pursue FCRA Section 616 damages ($100-$1,000/violation)\n\n"
            f"Your {letter_count} final demand letters are ready.\n\n"
            f"-- Your Credit Dispute Team\nRef: {conf}"
        )


def run_all_agents(db: Session) -> dict:
    """Run all three pipeline agents in sequence."""
    results = {}
    for day, name in [(30, "agent_30"), (60, "agent_60"), (90, "agent_90")]:
        try:
            count = _process_bucket(db, day, name)
            results[name] = {"processed": count, "status": "ok"}
        except Exception as e:
            results[name] = {"processed": 0, "status": "error", "error": str(e)}
            print(f"[ORCHESTRATOR ERROR] {name}: {e}")
    return results


def enroll_from_db(db: Session) -> int:
    """Scan DB for watcher-subscribed clients not yet in pipeline and enroll them."""
    existing_sids = {r.session_id for r in db.query(PipelineEntry.session_id).all()}
    clients = (
        db.query(Client)
        .filter(Client.watcher_subscribed == True, Client.dispatched_at.isnot(None))
        .all()
    )
    enrolled = 0
    for client in clients:
        if client.session_id in existing_sids:
            continue
        profile = load_client(db, client.session_id, decrypt_json)
        if not profile:
            continue
        enroll_client(db, profile)
        enrolled += 1
    if enrolled:
        print(f"[ENROLLOR] Added {enrolled} new clients to watcher pipeline")
    return enrolled


def get_pipeline_stats(db: Session) -> dict:
    """Get pipeline aggregate stats."""
    from sqlalchemy import func
    row = db.query(
        func.count(PipelineEntry.id).label("total"),
        func.sum(func.cast(PipelineEntry.stage == "active", Integer)).label("active"),
        func.sum(func.cast(PipelineEntry.stage == "complete", Integer)).label("complete"),
        func.sum(PipelineEntry.letters_generated).label("total_letters"),
        func.sum(PipelineEntry.notifications_sent).label("total_notifications"),
    ).first()
    from sqlalchemy import Integer
    return {
        "total": row.total or 0,
        "active": row.active or 0,
        "complete": row.complete or 0,
        "total_letters": row.total_letters or 0,
        "total_notifications": row.total_notifications or 0,
    }
