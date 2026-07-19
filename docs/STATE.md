# BitmojiGuy 5-Min Credit Fix — State

> **Status:** PRE-LAUNCH (release candidate on PR #3; blocked on Sean's provider keys + deploy logins)
> **Last updated:** 2026-07-18 (FastAPI takeover) · **Last verified:** 2026-07-18 (tests, build, API e2e, browser walk on Kevin's branch)
> **One-liner:** $24.99 credit-dispute letters — detect from the customer's own report, one letter per bureau, mailed on an escalating postage ladder, encrypted at rest and hard-deleted within 24h.
> **Links:** `AGENTS.md` (charter/SOP) · `docs/decisions/` (ADRs) · `docs/compliance/croa-positioning.md` · GitHub Issues (work tracking)

This is the shared, repo-level context document — what is actually built, wired, and live.
It is updated **via PR, in the same PR as the change that moved the state**. Read it at
session start; never re-explain history that's already recorded here.

Facts carry confidence tags: `verified` (checked against ground truth on the stated date) ·
`asserted` (stated, not re-checked) · `assumed` (best guess).

---

## Live topology

| Service | URL | Status | Last verified |
|---|---|---|---|
| Frontend (Next.js, Vercel) | `bitmoji-guy5-min-credit-fix.vercel.app` | LIVE but serving the **old** build; redeploy from PR #3 pending | 2026-07-14 `asserted` |
| Backend (FastAPI, Railway) | to be (re)deployed from PR #3 — old Flask deploy is obsolete | pending | — |
| Database | Postgres (Railway or Supabase), **encrypted-ephemeral** per ADR-0002; SQLite in dev | pending provisioning | — |
| Mail (Lob) | integration built with postage ladder; needs `LOB_API_KEY` | `verified` code, `asserted` no key | 2026-07-18 |
| Stripe | Checkout + webhook built; live keys + webhook secret pending from Sean | `asserted` | — |

## Branch reality (read this before touching code)

- **`main`** = Sean's Jul-10 snapshot + merged agent-infra PR #2. Still carries the legacy Flask app and three competing frontends. `verified` 2026-07-18.
- **`ko/fastapi-takeover`** (pushed to `Kayo-11` fork, **PR #3 open**) = the canonical release candidate:
  - One FastAPI backend (`backend/`, evolved from Sean's BITMOJIGUY_CREDIT_ALL work) + one Next.js frontend (`frontend/`, from creditfix-next). Everything else deleted.
  - Field-level AES-256-GCM PII encryption at rest + 24h hard delete (ADR-0002 supersedes ADR-0001 hold-nothing).
  - Stateless HMAC terms tokens, in-memory PDF parse/generation, DB-derived fishbowl queues → multi-worker safe (`railway.toml` runs 2 uvicorn workers).
  - Frontend: typed API client, 5-step wizard wired end-to-end, consent gate, localStorage session resume, Stripe redirect polling, /terms /privacy /admin pages. $24.99 everywhere.
  - `ruff` clean · 14/14 pytest · eslint clean · `next build` clean · API e2e + browser walk green. `verified` 2026-07-18.

## What is real vs. mock

| Module | State |
|---|---|
| Report upload → parse (PyMuPDF) → dispute detection (Claude w/ keyword fallback) | **Real** |
| Letter generation (per-bureau + per-creditor, FCRA/FDCPA citations, in-memory PDF) | **Real** (Sean's perfected letter texts still pending — drop-in swap in `ae_creditfix/templates.py`) |
| Postage ladder (Lob: First Class r1 → Certified r2 → Certified+RR r3) | **Built**, needs `LOB_API_KEY` |
| Stripe Checkout ($24.99) + webhook + demo mode | **Built**, test/demo only until live keys |
| PII encryption at rest + 24h purge loop | **Real**, covered by tests |
| Terms/consent gate (FE + server-side token) | **Real** |
| Admin dashboard (/admin, key-gated stats) | **Real** |
| CI (GitHub Actions: ruff+pytest, eslint+build) | **Written**, not pushed — token lacks `workflow` scope |

## Known gaps that will bite

1. **Launch inputs from Sean:** live Stripe keys + webhook secret, Lob API key, his perfected letter texts, and the merge of PR #3 (Kevin has no write access to this repo).
2. **Deploy logins:** Railway + Vercel CLI sessions on Kevin's machine are expired; re-login needed before infra work.
3. **Production Postgres not provisioned** — dev runs SQLite; `DATABASE_URL` must be set on Railway.
4. **CROA/state-CSO legal review pending** — see `docs/compliance/croa-positioning.md` action list; needed before scaling paid volume.
5. Old Vercel deployment still serves the pre-takeover frontend — must be repointed to `frontend/` on the new branch/main.

## Active work

PR #3 (`Kayo-11:ko/fastapi-takeover` → `main`) is the release candidate. Next session: deploy runbook in `deploy/RUNBOOK.md` — provision Postgres, set env, deploy Railway + Vercel, then live-keys dry run when Sean surfaces.
