-- BitmojiGuy 5-Min Credit Fix — Initial Schema
-- AE Labs (c) 2025 Sean Gilmore / Arden Edge Capital

CREATE TABLE IF NOT EXISTS clients (
    id           BIGSERIAL PRIMARY KEY,
    session_id   TEXT UNIQUE NOT NULL,
    confirmation TEXT,
    state        TEXT,
    status       TEXT DEFAULT 'started',
    paid         BOOLEAN DEFAULT FALSE,
    paid_at      TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL,
    name_enc     BYTEA,
    email_enc    BYTEA,
    phone_enc    BYTEA,
    referral_source  TEXT DEFAULT '',
    profile_enc      BYTEA,
    follow_up_30_sent BOOLEAN DEFAULT FALSE,
    follow_up_60_sent BOOLEAN DEFAULT FALSE,
    follow_up_90_sent BOOLEAN DEFAULT FALSE,
    follow_up_30_date TIMESTAMPTZ,
    follow_up_60_date TIMESTAMPTZ,
    follow_up_90_date TIMESTAMPTZ,
    purge_after      TIMESTAMPTZ,
    initials         TEXT,
    dispute_count    INTEGER DEFAULT 0,
    dispatched_at    TIMESTAMPTZ,
    watcher_subscribed BOOLEAN DEFAULT FALSE,
    watcher_paid_at  TIMESTAMPTZ,
    notify_method    TEXT DEFAULT '',
    notify_handle_enc BYTEA,
    reference_number TEXT
);

CREATE INDEX IF NOT EXISTS idx_conf      ON clients(confirmation);
CREATE INDEX IF NOT EXISTS idx_purge     ON clients(purge_after);
CREATE INDEX IF NOT EXISTS idx_session   ON clients(session_id);
CREATE INDEX IF NOT EXISTS idx_followup  ON clients(paid, follow_up_30_sent, follow_up_60_sent, follow_up_90_sent);
