# BitmojiGuy 5-Min Credit Fix — PostgreSQL Persistence Layer (Supabase)
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001

import os
import json
import hashlib
import base64
import threading
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

DATABASE_URL = os.environ.get('DATABASE_URL', '')
POOL_MIN = int(os.environ.get('DB_POOL_MIN', '1'))
POOL_MAX = int(os.environ.get('DB_POOL_MAX', '10'))
DB_CONNECT_TIMEOUT = int(os.environ.get('DB_CONNECT_TIMEOUT', '10'))

_pool = None
_pool_lock = threading.Lock()


# ─── ENCRYPTION ───────────────────────────────────────────────────────────────

def _app_fernet():
    secret = os.environ.get('SECRET_KEY', 'ae-labs-credit-fix-dev-key-change-me')
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()[:32])
    return Fernet(key)


def _encrypt(data):
    return _app_fernet().encrypt(
        data.encode() if isinstance(data, str) else json.dumps(data).encode()
    )


def _decrypt(token):
    if isinstance(token, memoryview):
        token = bytes(token)
    return _app_fernet().decrypt(token).decode()


def _decrypt_json(token):
    if isinstance(token, memoryview):
        token = bytes(token)
    return json.loads(_app_fernet().decrypt(token).decode())


# ─── CONNECTION POOL ──────────────────────────────────────────────────────────

def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                if not DATABASE_URL:
                    raise RuntimeError('DATABASE_URL is not set. Add it to your .env file.')
                _pool = ThreadedConnectionPool(
                    POOL_MIN, POOL_MAX, DATABASE_URL,
                    connect_timeout=DB_CONNECT_TIMEOUT,
                )
    return _pool


def get_db():
    conn = _get_pool().getconn()
    try:
        conn.cursor().execute('SELECT 1')
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        _get_pool().putconn(conn, close=True)
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=DB_CONNECT_TIMEOUT)
    return conn


def release_db(conn):
    try:
        _get_pool().putconn(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def start_health_check_loop(interval=60):
    def _loop():
        import time
        while True:
            time.sleep(interval)
            try:
                conn = get_db()
                conn.cursor().execute('SELECT 1')
                release_db(conn)
            except Exception as e:
                print(f'[DB HEALTH ERROR] {e}')
    threading.Thread(target=_loop, daemon=True).start()


# ─── SCHEMA ───────────────────────────────────────────────────────────────────

def init_db():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id                 BIGSERIAL PRIMARY KEY,
                session_id         TEXT UNIQUE NOT NULL,
                confirmation       TEXT,
                state              TEXT,
                status             TEXT DEFAULT 'started',
                paid               BOOLEAN DEFAULT FALSE,
                paid_at            TIMESTAMPTZ,
                created_at         TIMESTAMPTZ NOT NULL,
                updated_at         TIMESTAMPTZ NOT NULL,
                name_enc           BYTEA,
                email_enc          BYTEA,
                phone_enc          BYTEA,
                referral_source    TEXT DEFAULT '',
                profile_enc        BYTEA,
                follow_up_30_sent  BOOLEAN DEFAULT FALSE,
                follow_up_60_sent  BOOLEAN DEFAULT FALSE,
                follow_up_90_sent  BOOLEAN DEFAULT FALSE,
                follow_up_30_date  TIMESTAMPTZ,
                follow_up_60_date  TIMESTAMPTZ,
                follow_up_90_date  TIMESTAMPTZ,
                purge_after        TIMESTAMPTZ,
                initials           TEXT,
                dispute_count      INTEGER DEFAULT 0,
                dispatched_at      TIMESTAMPTZ,
                watcher_subscribed BOOLEAN DEFAULT FALSE,
                watcher_paid_at    TIMESTAMPTZ,
                notify_method      TEXT DEFAULT '',
                notify_handle_enc  BYTEA,
                reference_number   TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_conf     ON clients(confirmation)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_purge    ON clients(purge_after)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_session  ON clients(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_followup ON clients(paid, follow_up_30_sent, follow_up_60_sent, follow_up_90_sent)")
        conn.commit()
        cur.close()
    finally:
        release_db(conn)


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def save_client(profile):
    conn = get_db()
    now = datetime.utcnow().isoformat()
    purge = (datetime.utcnow() + timedelta(days=90)).isoformat()

    fu30 = fu60 = fu90 = None
    if profile.get('paid_at'):
        try:
            paid_dt = datetime.fromisoformat(profile['paid_at'])
            fu30 = (paid_dt + timedelta(days=30)).isoformat()
            fu60 = (paid_dt + timedelta(days=60)).isoformat()
            fu90 = (paid_dt + timedelta(days=90)).isoformat()
        except (ValueError, TypeError):
            pass

    name_enc           = _encrypt(profile.get('name', ''))
    email_enc          = _encrypt(profile.get('email', ''))
    phone_enc          = _encrypt(profile.get('phone', ''))
    notify_handle_enc  = _encrypt(profile.get('notify_handle', ''))
    profile_enc        = _encrypt(profile)
    dispute_count      = len(profile.get('dispute_items', []))

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO clients (
                session_id, confirmation, state, status, paid, paid_at,
                created_at, updated_at, name_enc, email_enc, phone_enc,
                referral_source, profile_enc,
                follow_up_30_date, follow_up_60_date, follow_up_90_date,
                purge_after, initials, dispute_count,
                dispatched_at, watcher_subscribed, watcher_paid_at,
                notify_method, notify_handle_enc, reference_number
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT(session_id) DO UPDATE SET
                confirmation      = EXCLUDED.confirmation,
                state             = EXCLUDED.state,
                status            = EXCLUDED.status,
                paid              = EXCLUDED.paid,
                paid_at           = EXCLUDED.paid_at,
                updated_at        = EXCLUDED.updated_at,
                name_enc          = EXCLUDED.name_enc,
                email_enc         = EXCLUDED.email_enc,
                phone_enc         = EXCLUDED.phone_enc,
                referral_source   = EXCLUDED.referral_source,
                profile_enc       = EXCLUDED.profile_enc,
                follow_up_30_date = EXCLUDED.follow_up_30_date,
                follow_up_60_date = EXCLUDED.follow_up_60_date,
                follow_up_90_date = EXCLUDED.follow_up_90_date,
                purge_after       = EXCLUDED.purge_after,
                initials          = EXCLUDED.initials,
                dispute_count     = EXCLUDED.dispute_count,
                dispatched_at     = EXCLUDED.dispatched_at,
                watcher_subscribed = EXCLUDED.watcher_subscribed,
                watcher_paid_at   = EXCLUDED.watcher_paid_at,
                notify_method     = EXCLUDED.notify_method,
                notify_handle_enc = EXCLUDED.notify_handle_enc,
                reference_number  = EXCLUDED.reference_number
        """, (
            profile['id'], profile.get('confirmation'), profile.get('state', ''),
            profile.get('status', 'started'), bool(profile.get('paid')),
            profile.get('paid_at'), profile.get('created_at', now), now,
            name_enc, email_enc, phone_enc,
            profile.get('referral_source', ''), profile_enc,
            fu30, fu60, fu90, purge,
            (profile.get('name', '??')[:2]).upper(), dispute_count,
            profile.get('dispatched_at'), bool(profile.get('watcher_subscribed')),
            profile.get('watcher_paid_at'), profile.get('notify_method', ''),
            notify_handle_enc, profile.get('confirmation'),
        ))
        conn.commit()
        cur.close()
    finally:
        release_db(conn)


def load_client_by_session(sid):
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT profile_enc FROM clients WHERE session_id = %s", (sid,))
        row = cur.fetchone()
        cur.close()
        if row and row['profile_enc']:
            try:
                return _decrypt_json(row['profile_enc'])
            except Exception:
                return None
        return None
    finally:
        release_db(conn)


def load_client_by_confirmation(code):
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT session_id, confirmation, state, status, paid, paid_at, created_at,
                   updated_at, initials, follow_up_30_sent, follow_up_60_sent, follow_up_90_sent
            FROM clients WHERE confirmation = %s
        """, (code,))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    finally:
        release_db(conn)


def get_all_clients_admin():
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT session_id, confirmation, state, status, paid, paid_at, created_at,
                   updated_at, initials, name_enc, email_enc, phone_enc, referral_source,
                   dispute_count, follow_up_30_sent, follow_up_60_sent, follow_up_90_sent
            FROM clients ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        cur.close()
    finally:
        release_db(conn)

    results = []
    for r in rows:
        entry = dict(r)
        for field, enc_field in [('name', 'name_enc'), ('email', 'email_enc'), ('phone', 'phone_enc')]:
            try:
                entry[field] = _decrypt(r[enc_field]) if r[enc_field] else ''
            except Exception:
                entry[field] = ''
            del entry[enc_field]
        results.append(entry)
    return results


def get_due_followups(day):
    now = datetime.utcnow().isoformat()
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if day == 30:
            cur.execute("""
                SELECT session_id, profile_enc FROM clients
                WHERE paid = TRUE AND follow_up_30_sent = FALSE AND follow_up_30_date <= %s
            """, (now,))
        elif day == 60:
            cur.execute("""
                SELECT session_id, profile_enc FROM clients
                WHERE paid = TRUE AND follow_up_30_sent = TRUE AND follow_up_60_sent = FALSE
                  AND follow_up_60_date <= %s
            """, (now,))
        elif day == 90:
            cur.execute("""
                SELECT session_id, profile_enc FROM clients
                WHERE paid = TRUE AND follow_up_60_sent = TRUE AND follow_up_90_sent = FALSE
                  AND follow_up_90_date <= %s
            """, (now,))
        else:
            return []
        rows = cur.fetchall()
        cur.close()
    finally:
        release_db(conn)

    results = []
    for r in rows:
        try:
            results.append(_decrypt_json(r['profile_enc']))
        except Exception:
            pass
    return results


def mark_followup_sent(session_id, day):
    if day not in (30, 60, 90):
        raise ValueError(f'Invalid follow-up day: {day}')
    col = f'follow_up_{day}_sent'
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE clients SET {col} = TRUE, updated_at = %s WHERE session_id = %s",
            (datetime.utcnow().isoformat(), session_id)
        )
        conn.commit()
        cur.close()
    finally:
        release_db(conn)


def delete_expired_clients():
    cutoff = datetime.utcnow().isoformat()
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM clients WHERE purge_after <= %s", (cutoff,))
        deleted = cur.rowcount
        conn.commit()
        cur.close()
    finally:
        release_db(conn)
    if deleted:
        print(f'[PURGE] Deleted {deleted} expired client records')
    return deleted


def get_stats():
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN paid     THEN 1 ELSE 0 END) AS paid,
                SUM(CASE WHEN NOT paid THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN follow_up_30_sent THEN 1 ELSE 0 END) AS fu30,
                SUM(CASE WHEN follow_up_60_sent THEN 1 ELSE 0 END) AS fu60,
                SUM(CASE WHEN follow_up_90_sent THEN 1 ELSE 0 END) AS fu90
            FROM clients
        """)
        row = cur.fetchone()
        cur.execute("""
            SELECT referral_source, COUNT(*) AS count
            FROM clients
            WHERE referral_source IS NOT NULL AND referral_source != ''
            GROUP BY referral_source ORDER BY count DESC
        """)
        ref_rows = cur.fetchall()
        cur.close()
    finally:
        release_db(conn)

    return {
        'total':   int(row['total'] or 0),
        'paid':    int(row['paid'] or 0),
        'pending': int(row['pending'] or 0),
        'revenue': int(row['paid'] or 0) * 24.99,
        'fu30':    int(row['fu30'] or 0),
        'fu60':    int(row['fu60'] or 0),
        'fu90':    int(row['fu90'] or 0),
        'referral_sources': {r['referral_source']: r['count'] for r in ref_rows},
    }
