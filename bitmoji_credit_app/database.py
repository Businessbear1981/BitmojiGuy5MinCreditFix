# BitmojiGuy 5-Min Credit Fix — SQLite Persistence Layer
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001

import os
import json
import sqlite3
import hashlib
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

DB_PATH = os.environ.get('DB_PATH', 'creditfix.db')

# App-level encryption key (not per-session — used for persistent storage)
def _app_fernet():
    secret = os.environ.get('SECRET_KEY', 'ae-labs-credit-fix-dev-key-change-me')
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()[:32])
    return Fernet(key)


def _encrypt(data):
    return _app_fernet().encrypt(data.encode() if isinstance(data, str) else json.dumps(data).encode())


def _decrypt(token):
    return _app_fernet().decrypt(token).decode()


def _decrypt_json(token):
    return json.loads(_app_fernet().decrypt(token).decode())


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            confirmation TEXT,
            state TEXT,
            status TEXT DEFAULT 'started',
            paid INTEGER DEFAULT 0,
            paid_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            name_enc BLOB,
            email_enc BLOB,
            phone_enc BLOB,
            referral_source TEXT DEFAULT '',
            profile_enc BLOB,
            follow_up_30_sent INTEGER DEFAULT 0,
            follow_up_60_sent INTEGER DEFAULT 0,
            follow_up_90_sent INTEGER DEFAULT 0,
            follow_up_30_date TEXT,
            follow_up_60_date TEXT,
            follow_up_90_date TEXT,
            purge_after TEXT,
            initials TEXT,
            dispute_count INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_conf ON clients(confirmation);
        CREATE INDEX IF NOT EXISTS idx_purge ON clients(purge_after);
        CREATE INDEX IF NOT EXISTS idx_followup ON clients(paid, follow_up_30_sent, follow_up_60_sent, follow_up_90_sent);
        CREATE INDEX IF NOT EXISTS idx_session ON clients(session_id);
    """)
    # Migrate existing tables — add columns if missing
    for col, coldef in [('phone_enc', 'BLOB'), ('referral_source', "TEXT DEFAULT ''"),
                         ('dispute_count', 'INTEGER DEFAULT 0'),
                         ('dispatched_at', 'TEXT'), ('watcher_subscribed', 'INTEGER DEFAULT 0'),
                         ('watcher_paid_at', 'TEXT'), ('notify_method', "TEXT DEFAULT ''"),
                         ('notify_handle_enc', 'BLOB'),
                         ('reference_number', 'TEXT')]:
        try:
            conn.execute(f"ALTER TABLE clients ADD COLUMN {col} {coldef}")
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.close()


def save_client(profile):
    """Upsert a client profile into SQLite with encrypted PII."""
    conn = get_db()
    now = datetime.utcnow().isoformat()
    purge = (datetime.utcnow() + timedelta(days=90)).isoformat()

    # Compute follow-up dates from paid_at
    fu30 = fu60 = fu90 = None
    if profile.get('paid_at'):
        try:
            paid_dt = datetime.fromisoformat(profile['paid_at'])
            fu30 = (paid_dt + timedelta(days=30)).isoformat()
            fu60 = (paid_dt + timedelta(days=60)).isoformat()
            fu90 = (paid_dt + timedelta(days=90)).isoformat()
        except (ValueError, TypeError):
            pass

    name_enc = _encrypt(profile.get('name', ''))
    email_enc = _encrypt(profile.get('email', ''))
    phone_enc = _encrypt(profile.get('phone', ''))
    notify_handle_enc = _encrypt(profile.get('notify_handle', ''))
    profile_enc = _encrypt(profile)
    dispute_count = len(profile.get('dispute_items', []))

    conn.execute("""
        INSERT INTO clients (session_id, confirmation, state, status, paid, paid_at,
                             created_at, updated_at, name_enc, email_enc, phone_enc,
                             referral_source, profile_enc,
                             follow_up_30_date, follow_up_60_date, follow_up_90_date,
                             purge_after, initials, dispute_count,
                             dispatched_at, watcher_subscribed, watcher_paid_at,
                             notify_method, notify_handle_enc, reference_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            confirmation=excluded.confirmation, state=excluded.state,
            status=excluded.status, paid=excluded.paid, paid_at=excluded.paid_at,
            updated_at=excluded.updated_at, name_enc=excluded.name_enc,
            email_enc=excluded.email_enc, phone_enc=excluded.phone_enc,
            referral_source=excluded.referral_source,
            profile_enc=excluded.profile_enc,
            follow_up_30_date=excluded.follow_up_30_date,
            follow_up_60_date=excluded.follow_up_60_date,
            follow_up_90_date=excluded.follow_up_90_date,
            purge_after=excluded.purge_after, initials=excluded.initials,
            dispute_count=excluded.dispute_count,
            dispatched_at=excluded.dispatched_at,
            watcher_subscribed=excluded.watcher_subscribed,
            watcher_paid_at=excluded.watcher_paid_at,
            notify_method=excluded.notify_method,
            notify_handle_enc=excluded.notify_handle_enc,
            reference_number=excluded.reference_number
    """, (
        profile['id'], profile.get('confirmation'), profile.get('state', ''),
        profile.get('status', 'started'), 1 if profile.get('paid') else 0,
        profile.get('paid_at'), profile.get('created_at', now), now,
        name_enc, email_enc, phone_enc,
        profile.get('referral_source', ''), profile_enc,
        fu30, fu60, fu90, purge, (profile.get('name', '??')[:2]).upper(),
        dispute_count,
        profile.get('dispatched_at'), 1 if profile.get('watcher_subscribed') else 0,
        profile.get('watcher_paid_at'), profile.get('notify_method', ''),
        notify_handle_enc, profile.get('confirmation')
    ))
    conn.commit()
    conn.close()


def load_client_by_session(sid):
    """Load and decrypt a client profile by session_id."""
    conn = get_db()
    row = conn.execute("SELECT profile_enc FROM clients WHERE session_id = ?", (sid,)).fetchone()
    conn.close()
    if row and row['profile_enc']:
        try:
            return _decrypt_json(row['profile_enc'])
        except Exception:
            return None
    return None


def load_client_by_confirmation(code):
    """Load minimal info by confirmation code (no PII decryption)."""
    conn = get_db()
    row = conn.execute("""
        SELECT session_id, confirmation, state, status, paid, paid_at, created_at,
               updated_at, initials, follow_up_30_sent, follow_up_60_sent, follow_up_90_sent
        FROM clients WHERE confirmation = ?
    """, (code,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_clients_admin():
    """Get all clients for admin dashboard with decrypted PII."""
    conn = get_db()
    rows = conn.execute("""
        SELECT session_id, confirmation, state, status, paid, paid_at, created_at,
               updated_at, initials, name_enc, email_enc, phone_enc, referral_source,
               dispute_count, follow_up_30_sent, follow_up_60_sent, follow_up_90_sent
        FROM clients ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    results = []
    for r in rows:
        entry = dict(r)
        # Decrypt PII for admin view
        for field, enc_field in [('name', 'name_enc'), ('email', 'email_enc'), ('phone', 'phone_enc')]:
            try:
                entry[field] = _decrypt(r[enc_field]) if r[enc_field] else ''
            except Exception:
                entry[field] = ''
            del entry[enc_field]
        results.append(entry)
    return results


def get_due_followups(day):
    """Get clients needing follow-up at the given day mark (30, 60, or 90)."""
    now = datetime.utcnow().isoformat()
    conn = get_db()
    if day == 30:
        rows = conn.execute("""
            SELECT session_id, profile_enc FROM clients
            WHERE paid = 1 AND follow_up_30_sent = 0 AND follow_up_30_date <= ?
        """, (now,)).fetchall()
    elif day == 60:
        rows = conn.execute("""
            SELECT session_id, profile_enc FROM clients
            WHERE paid = 1 AND follow_up_30_sent = 1 AND follow_up_60_sent = 0 AND follow_up_60_date <= ?
        """, (now,)).fetchall()
    elif day == 90:
        rows = conn.execute("""
            SELECT session_id, profile_enc FROM clients
            WHERE paid = 1 AND follow_up_60_sent = 1 AND follow_up_90_sent = 0 AND follow_up_90_date <= ?
        """, (now,)).fetchall()
    else:
        rows = []
    conn.close()

    results = []
    for r in rows:
        try:
            profile = _decrypt_json(r['profile_enc'])
            results.append(profile)
        except Exception:
            pass
    return results


def mark_followup_sent(session_id, day):
    conn = get_db()
    col = f'follow_up_{day}_sent'
    conn.execute(f"UPDATE clients SET {col} = 1, updated_at = ? WHERE session_id = ?",
                 (datetime.utcnow().isoformat(), session_id))
    conn.commit()
    conn.close()


def delete_expired_clients():
    """Purge all client records older than 90 days."""
    cutoff = datetime.utcnow().isoformat()
    conn = get_db()
    cursor = conn.execute("DELETE FROM clients WHERE purge_after <= ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted:
        print(f"[PURGE] Deleted {deleted} expired client records")
    return deleted


def get_stats():
    """Get aggregate stats for admin dashboard."""
    conn = get_db()
    row = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN paid = 1 THEN 1 ELSE 0 END) as paid,
               SUM(CASE WHEN paid = 0 THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN follow_up_30_sent = 1 THEN 1 ELSE 0 END) as fu30,
               SUM(CASE WHEN follow_up_60_sent = 1 THEN 1 ELSE 0 END) as fu60,
               SUM(CASE WHEN follow_up_90_sent = 1 THEN 1 ELSE 0 END) as fu90
        FROM clients
    """).fetchone()
    # Referral source breakdown
    ref_rows = conn.execute("""
        SELECT referral_source, COUNT(*) as count
        FROM clients WHERE referral_source IS NOT NULL AND referral_source != ''
        GROUP BY referral_source ORDER BY count DESC
    """).fetchall()
    conn.close()
    return {
        'total': row['total'] or 0,
        'paid': row['paid'] or 0,
        'pending': row['pending'] or 0,
        'revenue': (row['paid'] or 0) * 24.99,
        'fu30': row['fu30'] or 0,
        'fu60': row['fu60'] or 0,
        'fu90': row['fu90'] or 0,
        'referral_sources': {r['referral_source']: r['count'] for r in ref_rows},
    }
