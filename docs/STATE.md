# BitmojiGuy 5-Min Credit Fix — State

> **Status:** LIVE in test/demo mode on `bitmojiguycredittool.tech` (themed journey + full e2e); real charges blocked on Sean's live keys + PR #3 merge
> **Last updated:** 2026-08-31 (dispute engine + relief pathways, PR #5) · **Last verified:** 2026-07-19 (pytest 19/19, build clean, local browser e2e of Cash App→admin release→gate). **PR #5 code is NOT test-verified — see "Active work".**
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
| Manual pay (Cash App `$5mincreditfix` / Chime `$AELabsPay`): confirmation code → customer pays Sean directly → admin verifies + releases from /admin (unlock, mail r1, email PDF) | **Real** (2026-07-19), covered by tests; stairway polls and auto-advances on release |
| PII encryption at rest + 24h purge loop | **Real**, covered by tests |
| Terms/consent gate (FE + server-side token) | **Real** |
| Admin dashboard (/admin, key-gated stats) | **Real** |
| CI (GitHub Actions: ruff+pytest, eslint+build) | **Written**, not pushed — token lacks `workflow` scope |
| Relief pathways backend (`relief_pathways.py`, `student_loans.py`, `medical_relief.py`) — emits `student_loans` + `medical` sections, all-`.gov` links, anti-scam "no such thing as a debt-relief grant" block | **Built**, routes exist at `main.py:1073` (`GET /api/case/{id}/relief`) and `:1110` (`/relief/summary`) `verified` 2026-08-31. Logic not test-verified. |
| Relief frontend (`components/relief/ReliefPanel.tsx`) | **Built but NOT WIRED** — zero imports, zero render sites in `frontend/`. Invisible to customers today. `verified` 2026-08-31 |
| Signature capture (`components/sign/SignaturePad.tsx` + `main.py:500` `/sign`, `:536` `/signature-status`) | Backend **built**; frontend component **NOT WIRED** — zero imports. `verified` 2026-08-31 |
| `dispute_engine/` package (categories, tiers, legal_library, analyst, compose, letter_generator, adapter) | **Built**, ~3,800 lines. Reachability from `main.py` not yet audited. `asserted` |
| Watcher backend (`watcher.py`, `watcher_loop.py`) | **Built**, routes at `main.py:928`–`:1022`. `/watcher` page previously noted "not live". `asserted` |

## Known gaps that will bite

1. **Launch inputs from Sean:** live Stripe keys + webhook secret, Lob API key, his perfected letter texts, and the merge of PR #3 (Kevin has no write access to this repo).
2. **Deploy logins:** Railway + Vercel CLI sessions on Kevin's machine are expired; re-login needed before infra work.
3. **Production Postgres not provisioned** — dev runs SQLite; `DATABASE_URL` must be set on Railway.
4. **CROA/state-CSO legal review pending** — see `docs/compliance/croa-positioning.md` action list; needed before scaling paid volume.
5. Old Vercel deployment still serves the pre-takeover frontend — must be repointed to `frontend/` on the new branch/main.
6. **Relief feature is dead code on the frontend.** Backend endpoints are live, but nothing renders `ReliefPanel`. Wiring it into `/koi-pond` (step 3, item review) needs: a `sessionId` in scope on that page (it currently reads items from a localStorage cache via `getDisputes()`, not the server — use `getApiSessionId()`), an `apiBase`, and typed helpers in `lib/api.ts`. `verified` 2026-08-31
7. **Relief types are duplicated, not shared.** `ReliefPanel` declares its own seven shapes locally and bypasses `lib/api.ts` with raw `fetch`. `lib/types.ts` has `medical_debt` in `BUCKET_LABELS` but **no `student_loan` bucket**, and `CaseStatus` has no `signed`/`signed_at` field. `verified` 2026-08-31
8. **No ADR for the relief/forgiveness module.** ADRs stop at 0002. A relief path that guides customers toward federal programs has CROA/state-CSO surface area and needs its own decision record alongside `docs/compliance/croa-positioning.md`.
9. **PR #5 is unverified.** No pytest run, no `next build`, no lint, no endpoint exercised. Do not merge on the strength of "it starts".

## Active work

PR #3 (`Kayo-11:ko/fastapi-takeover` → `main`) is the release candidate. Next session: deploy runbook in `deploy/RUNBOOK.md` — provision Postgres, set env, deploy Railway + Vercel, then live-keys dry run when Sean surfaces.

**PR #5 (`sean/letters-engine` → `main`), opened 2026-08-31** — dispute engine + relief pathways + supporting backend modules. 38 files, +10,621/−374, commit `b03e7d8`.

- Adds `dispute_engine/` package; `student_loans.py`, `relief_pathways.py`, `medical_relief.py`; `equifax_parser.py`, `letter_preview.py`, `print_packet.py`, `signature.py`, `calibration.py`, `disclosures.py`, `outcomes.py`, `provenance.py`, `scoring.py`, `watcher.py`, `watcher_loop.py`; frontend `ReliefPanel.tsx` + `SignaturePad.tsx`.
- **Verification status:** local dev environment built from scratch this session (no `node_modules`, no venv existed; `python` is not on PATH on Sean's box — only the `py` launcher). Backend venv on Python 3.12.10, 45 packages, `pip install` exit 0. `npm install` exit 0. Both servers start: uvicorn `Application startup complete` on `127.0.0.1:8000`, Next.js 16.2.3 `Ready in 16.3s` on `:3000`. `verified` 2026-08-31.
- **Not verified:** no pytest, no `next build`, no ruff/eslint, no HTTP request issued against any route. Startup ≠ working.
- Backend boots with **no `.env`**, falling back to `config.py` defaults — Stripe/Lob/Anthropic paths are inert until keys are supplied.
- Next: wire `ReliefPanel` into `/koi-pond`, add the `student_loan` bucket to `lib/types.ts`, move relief shapes into `lib/types.ts` + helpers into `lib/api.ts`, write the relief ADR, then run the test suite and a browser walk before asking Kevin to merge.
