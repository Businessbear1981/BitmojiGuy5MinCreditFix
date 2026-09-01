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
| `dispute_engine/` package (categories, tiers, legal_library, analyst, compose, letter_generator, adapter) | **Real and wired** — `main.py:30-31`, `/api/admin/templates` (`:1148`), `/api/admin/buckets` (`:1137`), `/api/case/{id}/letters` (`:571,601`); compose reached via `ae_creditfix/letters.py:18`. `verified` 2026-08-31 |
| Watcher backend (`watcher.py`, `watcher_loop.py`) | **Real and wired** — routes `main.py:928`–`:1023`, loop registered in lifespan `main.py:75`. `verified` 2026-08-31 |
| Scoring ledger (`outcomes.py`) | **Inert.** Write fns `record_dispute`/`record_result`/`record_score` have **zero callers**; `init_outcomes()` never called; `outcomes.db` is 0 bytes. See gap 10. `verified` 2026-08-31 |
| Calibration (`calibration.py`) | **Dead code** — nothing imports it. `install_into_scoring()` (`:141`) never runs, so the Beta posterior never replaces `scoring.PRIORS`. `verified` 2026-08-31 |

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
10. **The scoring ledger never records, and a swallowed exception hides it.** `scoring.score_item` → `outcomes.removal_rate` (`scoring.py:98`) hits a table that was never created, raises `sqlite3.OperationalError`, and is swallowed by `except Exception: pass` (`scoring.py:101-102`). Every score therefore falls back to hardcoded `PRIORS`, and the `"measured (n=…)"` provenance label (`scoring.py:100`) is unreachable in this build. **Any confidence number the engine reports today is `HAND_SET`, not `MARKET_DERIVED`.** Fix = call `init_outcomes()` at startup (as `provenance.init_audit()` already is, `main.py:91`) and wire the three write fns. `verified` 2026-08-31
11. **Student-loan findings never reach a dispute letter.** `student_loans.attach_findings` (`student_loans.py:901`) — the function that merges findings into `item['categories']` for the letter generator — has zero callers. Findings render only in the `/relief` JSON panel, which is itself unmounted (gap 6). Net effect: the student-loan work is invisible in both surfaces. `verified` 2026-08-31
12. **Forgiveness program directory is stale against 2026 rules.** `FORGIVENESS_PROGRAMS` (`student_loans.py:93-205`) has 7 entries and covers IDR only as a generic `idr_forgiveness`. The strings **RAP, SAVE, IBR, PAYE, ICR appear nowhere in the codebase.** SAVE ended by court order and RAP became the primary income-driven plan on 2026-07-01 — a customer-facing panel that names neither is out of date. Pell/federal grants: no coverage at all. `verified` 2026-08-31
13. **No application-packet or pre-fill export exists.** Relief content lives only as JSON on two GET endpoints; it never reaches a PDF, the print packet, or any downloadable artifact (`print_packet.py`, `letter_preview.py`, `pdf_gen.py` contain zero relief/student-loan/medical references). There is also **no Method, Plaid, or any external liability-discovery integration** anywhere in the repo — the only outbound HTTP client is Lob in `mail_service.py`. Prior session notes claiming a Method client shipped are wrong. `verified` 2026-08-31
14. **Two broken `__main__` demo blocks.** `dispute_engine/analyst.py:681` and `letter_generator.py:580` both `from .parsing_engine import parse_report` — **`parsing_engine.py` does not exist** — and both hardcode a dead path from a different machine (`C:\Users\sgill\Downloads\...`). Harmless at import, but running either module directly fails immediately. Delete or repair.
15. **Toolchain drift:** `.python-version` pins **3.11.0**; the working venv is **3.12.10**. Pick one before CI is turned on.

## Active work

PR #3 (`Kayo-11:ko/fastapi-takeover` → `main`) is the release candidate. Next session: deploy runbook in `deploy/RUNBOOK.md` — provision Postgres, set env, deploy Railway + Vercel, then live-keys dry run when Sean surfaces.

**PR #5 (`sean/letters-engine` → `main`), opened 2026-08-31** — dispute engine + relief pathways + supporting backend modules. 38 files, +10,621/−374, commit `b03e7d8`.

- Adds `dispute_engine/` package; `student_loans.py`, `relief_pathways.py`, `medical_relief.py`; `equifax_parser.py`, `letter_preview.py`, `print_packet.py`, `signature.py`, `calibration.py`, `disclosures.py`, `outcomes.py`, `provenance.py`, `scoring.py`, `watcher.py`, `watcher_loop.py`; frontend `ReliefPanel.tsx` + `SignaturePad.tsx`.
- **Verification status:** local dev environment built from scratch this session (no `node_modules`, no venv existed; `python` is not on PATH on Sean's box — only the `py` launcher). Backend venv on Python 3.12.10, 45 packages, `pip install` exit 0. `npm install` exit 0. Both servers start: uvicorn `Application startup complete` on `127.0.0.1:8000`, Next.js 16.2.3 `Ready in 16.3s` on `:3000`. `verified` 2026-08-31.
- **Not verified:** no pytest, no `next build`, no ruff/eslint, no HTTP request issued against any route. Startup ≠ working.
- Backend boots with **no `.env`**, falling back to `config.py` defaults — Stripe/Lob/Anthropic paths are inert until keys are supplied.
- **Static audit run 2026-08-31** (read-only, two agents): import-graph reachability from `main.py`, stub/placeholder sweep, secret scan, `ast.parse` syntax check of all 22 new files. Results folded into the tables and gaps above. Headline: the code quality is high — **0 TODOs, 0 `NotImplementedError`, 0 `...` bodies, 0 bare `except:`, 0 syntax failures, 0 hardcoded secrets** across ~10,600 new lines — but four things are built and never called (gaps 6, 10, 11, and `calibration.py`).
- Next, in order: (1) call `init_outcomes()` at startup and wire the three write fns — gap 10 makes every confidence number `HAND_SET`; (2) call `attach_findings` so student-loan findings reach letters — gap 11; (3) wire `ReliefPanel` into `/koi-pond` + add the `student_loan` bucket to `lib/types.ts`; (4) refresh the forgiveness directory for RAP/post-SAVE — gap 12; (5) write the relief ADR; (6) then pytest + `next build` + browser walk before asking Kevin to merge.
