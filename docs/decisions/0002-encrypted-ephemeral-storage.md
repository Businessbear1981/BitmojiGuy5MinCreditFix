# 0002 — Encrypted-ephemeral storage (supersedes 0001)

> **Status:** ACCEPTED (pending Sean's ack — flagged 2026-07-18)
> **Date:** 2026-07-18
> **Decision:** Consumer data may be persisted, but only **field-level encrypted at rest** (AES-256-GCM) and only for a **hard 24-hour TTL**, after which it is irreversibly deleted. Strict "no data at rest" (ADR-0001) is retired.

## Context

ADR-0001 mandated a pure in-memory store. That posture forced a single worker
(sessions split across processes), lost every in-flight session on deploy or
restart — including *paid* sessions awaiting mail-out — and broke the Stripe
redirect flow whenever the dyno recycled. Sean's own FastAPI backend (pushed
2026-07-10) reintroduced a database, signalling he is comfortable with an
ephemeral persistence model. Legally, breach-notification statutes across all
50 states key on **unencrypted** data; encrypted-at-rest with short retention
is the stronger, more defensible posture — in-memory possession was never a
legal shield. The real compliance exposure (CROA positioning, disclosures) is
independent of the storage choice and is tracked separately.

## Options considered

- **Strict hold-nothing (ADR-0001):** minimal surface, but operationally
  fragile — single worker, restart-wipes paid sessions, no horizontal scale.
- **Plaintext DB with 24h purge (Sean's push as-is):** operationally sound but
  PII sits readable in Postgres and its backups. Unacceptable.
- **Encrypted-ephemeral (chosen):** every PII column (name, address, DOB, SSN
  last-4, phone, email, items, letters, tracking) is AES-256-GCM encrypted via
  a server-held key (`PII_ENCRYPTION_KEY`, env-only); an hourly reaper
  hard-deletes rows and encrypted upload files older than 24h.

## Decision

- `database.py` uses `EncryptedString` / `EncryptedJSON` type decorators
  (`crypto_fields.py`); plaintext PII never reaches the database or its logs.
- Uploads are encrypted with a per-session key (Cypher) before touching disk;
  generated letter PDFs are never written to disk — rebuilt in memory on demand.
- `cleanup.py` purges rows + upload dirs past `SESSION_TTL_HOURS` (default 24).
- Multi-worker deployment is now safe (state is in the DB, terms tokens are
  HMAC-signed and stateless); `railway.toml` runs uvicorn with 2 workers.
- Follow-up rounds remain customer-driven re-runs (unchanged from ADR-0001).

## Consequences

- Deploy restarts no longer lose sessions; paid cases survive to mail-out.
- The DB host sees only ciphertext; a DB-level breach without the app env key
  exposes no readable PII, aligning with state breach-notification safe harbors.
- Key rotation requires a re-encryption pass or simply waiting out the 24h TTL.
- Anything wanting retention beyond 24h must supersede this ADR.

## Links

- Supersedes `0001-hold-nothing-no-data-at-rest.md` · Sean's FastAPI push
  2026-07-10 (`backend/`) · KO venture decision log 2026-07-18.
