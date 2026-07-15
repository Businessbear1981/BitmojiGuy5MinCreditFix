# 0001 — Hold nothing: no consumer data at rest

> **Status:** ACCEPTED
> **Date:** 2026-07-14 (records the model confirmed with Sean 2026-07-04)
> **Decision:** The platform persists **no** consumer PII or credit data — no database, no disk. All client records live in the worker's encrypted RAM for the active session only.

## Context

The app had drifted into a Supabase Postgres persistence layer holding customer PII +
credit-report data for 90 days. Sean cited prior trouble for holding consumer data;
the product's compliance posture is that we prepare and mail letters but retain
nothing. Confirmed with Sean on 2026-07-04.

## Options considered

- **Hold nothing (chosen):** in-memory store with per-session Fernet keys; uploads
  encrypted in memory (AES-256-GCM Cipher), parsed from streams, dropped. Follow-up
  rounds = the customer re-runs the flow (re-pull report, re-upload proof). Minimal
  breach surface, minimal compliance burden.
- **Persist with retention policy:** enables server-driven follow-up mailings, but
  makes the platform a data holder — the exact exposure Sean wants to avoid.

## Decision

No DB, no disk writes of consumer data, ever. `database.py` is a pure in-memory store.
Consequent constraints are load-bearing:

- **Single gunicorn worker** (`-w 1` in `railway.toml`) — sessions must not split.
- Admin release of manual payments requires the session still in RAM (no restart
  between pay and release) — accepted for MVP.
- The customer, not the server, drives follow-up rounds.

## Consequences

- Deploy restarts wipe in-flight sessions — mail promptly after payment.
- Any feature that "just saves it for later" is off the table without superseding this ADR.
- main still carries the old persistence layer + a committed `backend/creditfix.db`;
  the conforming implementation is on branch `ko/no-storage-rewire-cleanup` (merge pending).

## Links

- `AGENTS.md` guardrails · repo `HANDOFF.md` (on the rewire branch) · Sean call 2026-07-04.
