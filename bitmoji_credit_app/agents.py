# BitmojiGuy 5-Min Credit Fix — Watcher AI Agents
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# Three pipeline agents that run the Watcher follow-up system:
#   Agent30  — 30-day non-compliance bucket
#   Agent60  — 60-day escalation bucket
#   Agent90  — 90-day legal action bucket
#
# Each agent:
#   1. Queries the ledger for clients in its bucket
#   2. Generates follow-up letters
#   3. Sends notifications (email or queues social DMs)
#   4. Logs all actions to the ledger
#   5. Advances the client to the next stage

import os
import json
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import database

# ═════════════════════════════════════════════════════════════════════════════
# LEDGER — tracks every client's pipeline stage and agent actions
# ═════════════════════════════════════════════════════════════════════════════

LEDGER_DB = os.environ.get('LEDGER_DB', 'watcher_ledger.db')


def _get_ledger():
    conn = sqlite3.connect(LEDGER_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_ledger():
    conn = _get_ledger()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pipeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            confirmation TEXT,
            client_name TEXT,
            client_email TEXT,
            client_phone TEXT,
            state TEXT,
            notify_method TEXT DEFAULT 'email',
            notify_handle TEXT,
            dispatched_at TEXT NOT NULL,
            stage TEXT DEFAULT 'active',
            day_30_due TEXT,
            day_30_done INTEGER DEFAULT 0,
            day_30_done_at TEXT,
            day_60_due TEXT,
            day_60_done INTEGER DEFAULT 0,
            day_60_done_at TEXT,
            day_90_due TEXT,
            day_90_done INTEGER DEFAULT 0,
            day_90_done_at TEXT,
            letters_generated INTEGER DEFAULT 0,
            notifications_sent INTEGER DEFAULT 0,
            last_agent_run TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_pipe_stage ON pipeline(stage);
        CREATE INDEX IF NOT EXISTS idx_pipe_30 ON pipeline(day_30_done, day_30_due);
        CREATE INDEX IF NOT EXISTS idx_pipe_60 ON pipeline(day_60_done, day_60_due);
        CREATE INDEX IF NOT EXISTS idx_pipe_90 ON pipeline(day_90_done, day_90_due);

        CREATE TABLE IF NOT EXISTS agent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            agent TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_alog_sid ON agent_log(session_id);
        CREATE INDEX IF NOT EXISTS idx_alog_agent ON agent_log(agent);
    """)
    conn.close()


def enroll_client(profile):
    """Add a watcher-subscribed client to the pipeline ledger."""
    conn = _get_ledger()
    dispatched = profile.get('dispatched_at', datetime.utcnow().isoformat())
    try:
        dispatch_dt = datetime.fromisoformat(dispatched)
    except (ValueError, TypeError):
        dispatch_dt = datetime.utcnow()
        dispatched = dispatch_dt.isoformat()

    conn.execute("""
        INSERT OR IGNORE INTO pipeline
        (session_id, confirmation, client_name, client_email, client_phone, state,
         notify_method, notify_handle, dispatched_at,
         day_30_due, day_60_due, day_90_due, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        profile['id'],
        profile.get('confirmation', ''),
        profile.get('name', ''),
        profile.get('email', ''),
        profile.get('phone', ''),
        profile.get('state', ''),
        profile.get('notify_method', 'email'),
        profile.get('notify_handle', profile.get('email', '')),
        dispatched,
        (dispatch_dt + timedelta(days=30)).isoformat(),
        (dispatch_dt + timedelta(days=60)).isoformat(),
        (dispatch_dt + timedelta(days=90)).isoformat(),
        datetime.utcnow().isoformat(),
    ))
    conn.commit()
    conn.close()


def log_action(session_id, agent, action, detail=''):
    conn = _get_ledger()
    conn.execute(
        "INSERT INTO agent_log (session_id, agent, action, detail, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, agent, action, detail, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def get_pipeline_stats():
    conn = _get_ledger()
    row = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN stage = 'active' THEN 1 ELSE 0 END) as active,
               SUM(CASE WHEN day_30_done = 1 AND day_60_done = 0 THEN 1 ELSE 0 END) as in_30,
               SUM(CASE WHEN day_60_done = 1 AND day_90_done = 0 THEN 1 ELSE 0 END) as in_60,
               SUM(CASE WHEN day_90_done = 1 THEN 1 ELSE 0 END) as in_90,
               SUM(CASE WHEN stage = 'complete' THEN 1 ELSE 0 END) as complete,
               SUM(letters_generated) as total_letters,
               SUM(notifications_sent) as total_notifications
        FROM pipeline
    """).fetchone()
    conn.close()
    return dict(row)


def get_recent_agent_log(limit=50):
    conn = _get_ledger()
    rows = conn.execute(
        "SELECT * FROM agent_log ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═════════════════════════════════════════════════════════════════════════════
# EMAIL SENDER — shared by all agents
# ═════════════════════════════════════════════════════════════════════════════

def send_email(to_addr, subject, body):
    """Send an email via SMTP. Returns True if sent, False otherwise."""
    smtp_host = os.environ.get('SMTP_HOST', '')
    smtp_user = os.environ.get('SMTP_USER', '')
    if not smtp_host or not smtp_user:
        print(f"[AGENT EMAIL SKIP] No SMTP → {to_addr}: {subject}")
        return False
    try:
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = os.environ.get('FROM_EMAIL', 'noreply@aelabs.com')
        msg['To'] = to_addr
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(smtp_host, int(os.environ.get('SMTP_PORT', 587))) as s:
            s.starttls()
            s.login(smtp_user, os.environ.get('SMTP_PASS', ''))
            s.sendmail(msg['From'], to_addr, msg.as_string())
        return True
    except Exception as e:
        print(f"[AGENT EMAIL ERROR] {e}")
        return False


# ═════════════════════════════════════════════════════════════════════════════
# AGENT 30 — Non-compliance. Bureaus failed to respond in 30 days.
# ═════════════════════════════════════════════════════════════════════════════

class Agent30:
    NAME = 'agent_30'
    DAY = 30

    @staticmethod
    def get_queue():
        """Get all clients whose 30-day window has passed but haven't been processed."""
        now = datetime.utcnow().isoformat()
        conn = _get_ledger()
        rows = conn.execute("""
            SELECT * FROM pipeline
            WHERE day_30_done = 0 AND day_30_due <= ? AND stage = 'active'
            ORDER BY day_30_due ASC
        """, (now,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def run(cls):
        """Process all clients in the 30-day bucket."""
        queue = cls.get_queue()
        processed = 0
        for deal in queue:
            sid = deal['session_id']
            name = deal['client_name']
            conf = deal['confirmation']
            notify = deal['notify_method']
            handle = deal['notify_handle']

            # 1. Generate 30-day follow-up letters
            profile = database.load_client_by_session(sid)
            if profile:
                from followup import generate_followup_letters
                letters = generate_followup_letters(profile, 30)
                letter_count = len(letters)

                # Store letters in client profile
                profile.setdefault('follow_up_letters', {})['30'] = letters
                profile.setdefault('follow_up_history', []).append({
                    'day': 30, 'date': datetime.utcnow().isoformat(),
                    'letter_count': letter_count, 'agent': cls.NAME,
                })
                database.save_client(profile)
                database.mark_followup_sent(sid, 30)
            else:
                letter_count = 0

            # 2. Send notification
            delivered = False
            if notify == 'email' and handle:
                subject = f'5-Min Credit Fix — 30-Day Follow-Up for {conf}'
                body = (
                    f"Hi {name},\n\n"
                    f"Your 30-day FCRA response window has closed for dispute {conf}.\n\n"
                    f"The bureaus had 30 days to respond under FCRA Section 611(a)(1). "
                    f"If they haven't responded, or gave a generic reply, your non-compliance "
                    f"letter is ready.\n\n"
                    f"What to do now:\n"
                    f"1. Log in and download your 30-day follow-up letter\n"
                    f"2. Print and mail via certified mail to all 3 bureaus\n"
                    f"3. Keep your certified mail receipt as evidence\n\n"
                    f"Your {letter_count} follow-up letters are ready.\n\n"
                    f"-- AE Labs Credit Team\n"
                    f"Ref: {conf}"
                )
                delivered = send_email(handle, subject, body)

            # 3. Update ledger
            conn = _get_ledger()
            conn.execute("""
                UPDATE pipeline SET
                    day_30_done = 1,
                    day_30_done_at = ?,
                    letters_generated = letters_generated + ?,
                    notifications_sent = notifications_sent + 1,
                    last_agent_run = ?
                WHERE session_id = ?
            """, (datetime.utcnow().isoformat(), letter_count,
                  datetime.utcnow().isoformat(), sid))
            conn.commit()
            conn.close()

            # 4. Log action
            log_action(sid, cls.NAME, 'processed', json.dumps({
                'letters': letter_count,
                'notify': notify,
                'handle': handle,
                'delivered': delivered,
                'confirmation': conf,
            }))

            processed += 1
            print(f"[{cls.NAME}] Processed {conf} — {letter_count} letters, notify={notify}, delivered={delivered}")

        return processed


# ═════════════════════════════════════════════════════════════════════════════
# AGENT 60 — Escalation. Boilerplate response or silence at 60 days.
# ═════════════════════════════════════════════════════════════════════════════

class Agent60:
    NAME = 'agent_60'
    DAY = 60

    @staticmethod
    def get_queue():
        now = datetime.utcnow().isoformat()
        conn = _get_ledger()
        rows = conn.execute("""
            SELECT * FROM pipeline
            WHERE day_30_done = 1 AND day_60_done = 0 AND day_60_due <= ? AND stage = 'active'
            ORDER BY day_60_due ASC
        """, (now,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def run(cls):
        queue = cls.get_queue()
        processed = 0
        for deal in queue:
            sid = deal['session_id']
            name = deal['client_name']
            conf = deal['confirmation']
            notify = deal['notify_method']
            handle = deal['notify_handle']

            profile = database.load_client_by_session(sid)
            if profile:
                from followup import generate_followup_letters
                letters = generate_followup_letters(profile, 60)
                letter_count = len(letters)
                profile.setdefault('follow_up_letters', {})['60'] = letters
                profile.setdefault('follow_up_history', []).append({
                    'day': 60, 'date': datetime.utcnow().isoformat(),
                    'letter_count': letter_count, 'agent': cls.NAME,
                })
                database.save_client(profile)
                database.mark_followup_sent(sid, 60)
            else:
                letter_count = 0

            delivered = False
            if notify == 'email' and handle:
                subject = f'5-Min Credit Fix — 60-Day Escalation for {conf}'
                body = (
                    f"Hi {name},\n\n"
                    f"60 days have passed since your initial dispute {conf}.\n\n"
                    f"If the bureaus responded with a generic 'verified' letter, that's not good enough. "
                    f"Federal courts have ruled that automated e-OSCAR verification doesn't satisfy FCRA requirements:\n\n"
                    f"  - Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997)\n"
                    f"  - Johnson v. MBNA America Bank, 357 F.3d 426 (4th Cir. 2004)\n\n"
                    f"What to do now:\n"
                    f"1. Log in and download your 60-day escalation letter\n"
                    f"2. This letter demands the METHOD OF VERIFICATION — the bureau must tell you exactly how they verified the disputed item\n"
                    f"3. Mail via certified mail with return receipt requested\n\n"
                    f"Your {letter_count} escalation letters are ready.\n\n"
                    f"-- AE Labs Credit Team\n"
                    f"Ref: {conf}"
                )
                delivered = send_email(handle, subject, body)

            conn = _get_ledger()
            conn.execute("""
                UPDATE pipeline SET
                    day_60_done = 1,
                    day_60_done_at = ?,
                    letters_generated = letters_generated + ?,
                    notifications_sent = notifications_sent + 1,
                    last_agent_run = ?
                WHERE session_id = ?
            """, (datetime.utcnow().isoformat(), letter_count,
                  datetime.utcnow().isoformat(), sid))
            conn.commit()
            conn.close()

            log_action(sid, cls.NAME, 'processed', json.dumps({
                'letters': letter_count, 'notify': notify,
                'handle': handle, 'delivered': delivered,
            }))

            processed += 1
            print(f"[{cls.NAME}] Processed {conf} — {letter_count} letters, notify={notify}, delivered={delivered}")

        return processed


# ═════════════════════════════════════════════════════════════════════════════
# AGENT 90 — Legal action. CFPB complaint, AG complaint, final demand.
# ═════════════════════════════════════════════════════════════════════════════

class Agent90:
    NAME = 'agent_90'
    DAY = 90

    @staticmethod
    def get_queue():
        now = datetime.utcnow().isoformat()
        conn = _get_ledger()
        rows = conn.execute("""
            SELECT * FROM pipeline
            WHERE day_60_done = 1 AND day_90_done = 0 AND day_90_due <= ? AND stage = 'active'
            ORDER BY day_90_due ASC
        """, (now,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def run(cls):
        queue = cls.get_queue()
        processed = 0
        for deal in queue:
            sid = deal['session_id']
            name = deal['client_name']
            conf = deal['confirmation']
            state = deal['state']
            notify = deal['notify_method']
            handle = deal['notify_handle']

            profile = database.load_client_by_session(sid)
            if profile:
                from followup import generate_followup_letters
                letters = generate_followup_letters(profile, 90)
                letter_count = len(letters)
                profile.setdefault('follow_up_letters', {})['90'] = letters
                profile.setdefault('follow_up_history', []).append({
                    'day': 90, 'date': datetime.utcnow().isoformat(),
                    'letter_count': letter_count, 'agent': cls.NAME,
                })
                database.save_client(profile)
                database.mark_followup_sent(sid, 90)
            else:
                letter_count = 0

            delivered = False
            if notify == 'email' and handle:
                subject = f'5-Min Credit Fix — 90-Day Legal Action for {conf}'
                body = (
                    f"Hi {name},\n\n"
                    f"90 days. The legal action threshold for dispute {conf}.\n\n"
                    f"You now have standing to pursue federal remedies:\n\n"
                    f"  1. FILE A CFPB COMPLAINT\n"
                    f"     Go to consumerfinance.gov/complaint\n"
                    f"     Reference your dispute confirmation: {conf}\n\n"
                    f"  2. FILE AN FTC COMPLAINT\n"
                    f"     Go to reportfraud.ftc.gov\n\n"
                    f"  3. CONTACT YOUR STATE ATTORNEY GENERAL ({state})\n"
                    f"     File a consumer protection complaint\n\n"
                    f"  4. FCRA DAMAGES (15 U.S.C. 1681n)\n"
                    f"     Statutory: $100-$1,000 per violation\n"
                    f"     Punitive damages as court allows\n"
                    f"     Attorney fees and court costs\n\n"
                    f"Your {letter_count} final demand letters are ready. These include simultaneous "
                    f"CFPB/FTC/AG complaint notice language.\n\n"
                    f"Log in to download and take action.\n\n"
                    f"-- AE Labs Credit Team\n"
                    f"Ref: {conf}"
                )
                delivered = send_email(handle, subject, body)

            # Mark stage as complete
            conn = _get_ledger()
            conn.execute("""
                UPDATE pipeline SET
                    day_90_done = 1,
                    day_90_done_at = ?,
                    stage = 'complete',
                    letters_generated = letters_generated + ?,
                    notifications_sent = notifications_sent + 1,
                    last_agent_run = ?
                WHERE session_id = ?
            """, (datetime.utcnow().isoformat(), letter_count,
                  datetime.utcnow().isoformat(), sid))
            conn.commit()
            conn.close()

            log_action(sid, cls.NAME, 'completed', json.dumps({
                'letters': letter_count, 'notify': notify,
                'handle': handle, 'delivered': delivered,
                'stage': 'complete',
            }))

            processed += 1
            print(f"[{cls.NAME}] COMPLETED {conf} — {letter_count} final letters, pipeline done")

        return processed


# ═════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR — runs all three agents in sequence
# ═════════════════════════════════════════════════════════════════════════════

def run_all_agents():
    """Run all three pipeline agents. Called by background thread or admin API."""
    init_ledger()
    results = {}
    for agent_cls in [Agent30, Agent60, Agent90]:
        try:
            count = agent_cls.run()
            results[agent_cls.NAME] = {'processed': count, 'status': 'ok'}
            if count:
                print(f"[ORCHESTRATOR] {agent_cls.NAME}: {count} clients processed")
        except Exception as e:
            results[agent_cls.NAME] = {'processed': 0, 'status': 'error', 'error': str(e)}
            print(f"[ORCHESTRATOR ERROR] {agent_cls.NAME}: {e}")
    return results


def enroll_from_db():
    """Scan the main DB for watcher-subscribed clients not yet in the ledger and enroll them."""
    init_ledger()
    conn = _get_ledger()
    existing = {r['session_id'] for r in conn.execute("SELECT session_id FROM pipeline").fetchall()}
    conn.close()

    all_clients = database.get_all_clients_admin()
    enrolled = 0
    for client in all_clients:
        sid = client.get('session_id', '')
        if sid in existing:
            continue
        # Load full profile to check watcher status
        profile = database.load_client_by_session(sid)
        if not profile:
            continue
        if not profile.get('watcher_subscribed'):
            continue
        if not profile.get('dispatched_at'):
            continue
        enroll_client(profile)
        log_action(sid, 'enrollor', 'enrolled', f"Client {profile.get('confirmation','')} added to pipeline")
        enrolled += 1

    if enrolled:
        print(f"[ENROLLOR] Added {enrolled} new clients to watcher pipeline")
    return enrolled
