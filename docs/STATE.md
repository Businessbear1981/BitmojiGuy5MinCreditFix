# BitmojiGuy 5-Min Credit Fix — State

> **Status:** PRE-LAUNCH (near-launch; blocked on Sean's inputs + one open frontend decision)
> **Last updated:** 2026-07-14 (agent-infra install) · **Last verified:** 2026-07-14 (frontend URL, repo tree; journey e2e verified 2026-07-14 on Kevin's branch)
> **One-liner:** $24.99 credit-dispute letters — detect from the customer's own report, one letter per bureau, mailed on an escalating postage ladder, nothing held at rest.
> **Current state:** Working product on Kevin's unpushed branch; **main still carries the abandoned DB layer and three competing frontends.** Launch blockers are Sean-side (letters, Click2Mail funding, Stripe keys) + the canonical-frontend decision.
> **Links:** `AGENTS.md` (charter/SOP) · `docs/decisions/` (ADRs) · GitHub Issues (work tracking)

This is the shared, repo-level context document — what is actually built, wired, and live.
It is updated **via PR, in the same PR as the change that moved the state**. Read it at
session start; never re-explain history that's already recorded here.

Facts carry confidence tags: `verified` (checked against ground truth on the stated date) ·
`asserted` (stated, not re-checked) · `assumed` (best guess).

---

## Live topology

| Service | URL | Status | Last verified |
|---|---|---|---|
| Frontend (Next.js, Vercel) | `bitmoji-guy5-min-credit-fix.vercel.app` | LIVE, 200 | 2026-07-14 `verified` |
| Backend (Flask, Railway) | Railway-generated domain (see Vercel `NEXT_PUBLIC_FLASK_URL`) | deployed | `asserted` |
| Database | **none by design** (ADR-0001) — but see gaps: main's code still references one | — |
| Mail (Click2Mail) | not funded yet — nothing can mail | `asserted` (blocked on Sean) |
| Stripe | test/dev mode — live keys + webhook secret pending from Sean | `asserted` |

## Branch reality (read this before touching code)

- **`main`** = Sean's Jul-10 "full snapshot" + `creditfix-next-import/`. It still contains the Supabase/psycopg2 `database.py`, the dead FastAPI `backend/` (with a committed `creditfix.db`), and a Vite-boilerplate README. `verified` 2026-07-14.
- **`ko/no-storage-rewire-cleanup`** (Kevin's machine, **not pushed**) = the working product: in-memory `database.py` (no DB), Cipher wired into an all-in-memory upload path, consent gate (FE + server 422), ADMIN_KEY fails closed, localStorage session persistence across the Stripe redirect, $24.99 everywhere, dead code removed. `next build` clean; browser walk + curl e2e green 2026-07-14. `verified` then.
- Reconciling these two is the main engineering task — via PR, not by re-doing the work on main.

## What is real vs. mock

| Module | State |
|---|---|
| Report upload → parse → dispute detection (pdfplumber + regex, 5 categories) | **Real** |
| Consolidated letter generation (1/bureau, FCRA/FDCPA citations) | **Real** (Sean's 3–4 perfected letter versions still pending; an unwired fancier `dispute_engine/` also exists) |
| Postage escalation ladder (`click2mail_integration.py`) | **Built**, unfunded — nothing mails until Sean funds Click2Mail |
| Stripe Checkout + manual Cash App/Chime + admin release | **Built**, test keys only |
| Consent gate + no-storage hardening | **Real on Kevin's branch**, absent on main |
| Watcher ($10.99 follow-up + affiliate) | **Stub** — deliberately unscoped; keep light |
| Legacy Flask Jinja UI + `/step/*` pages | **Dead code**, marked LEGACY (Kevin's branch), kept for Sean |

## Known gaps that will bite

1. **Canonical frontend undecided** — `frontend/` themed journey vs Sean's `creditfix-next-import/` (which regresses price to $19.99, drops consent + session persistence). Recommendation on record: keep `frontend/`. Needs Sean's confirmation; don't polish either until decided.
2. **main violates the hold-nothing posture** (live DB layer + committed `backend/creditfix.db`) — merging Kevin's branch fixes this.
3. **Nothing can actually mail or charge** until Sean supplies: final letters, funded Click2Mail + creds, live Stripe keys + webhook secret, and the dojo free-report link.
4. Armor-forge UX is clunky (dead-feeling step 1/3; sword/glow unconfirmed) — polish, not blocker.
5. Single-worker constraint: any Railway scale-up or restart between manual pay and admin release loses the session (accepted for MVP, ADR-0001).

## Active work

Tracked in GitHub Issues + PRs on `Businessbear1981/BitmojiGuy5MinCreditFix`. Venture is **parked** as of 2026-07-14 pending Sean's inputs above; first session back should (a) get the frontend decision from Sean, (b) push + PR Kevin's `ko/no-storage-rewire-cleanup` branch rebased on main.
