# BitmojiGuy 5-Min Credit Fix — Agent Charter

> This file is the portable core for any agent or human working in this repo.
> Read it first, then read `docs/STATE.md` for what is actually built and live.

## What this is

Consumer credit-dispute platform (AE Labs / Arden Edge Capital, code AE.CC.001). A customer pulls their own credit report, the app detects disputable items and prepares one consolidated FCRA/FDCPA letter per bureau (Equifax, Experian, TransUnion), the customer pays **$24.99** one-time, and the letters are mailed on an escalating postage ladder (First Class → day 30 Certified → day 60 Certified + Return Receipt → day 90+ Certified + CFPB/FTC escalation). Optional "Watcher" follow-up at $10.99/mo — keep it light (reminder + affiliate promos), don't over-build. Principals: Sean Gilmore (owner/founder), Kevin Olson (build partner). "Done" at the current stage = a real paid, mailed dry run.

**The load-bearing product decision: the platform holds NO consumer data at rest** (ADR-0001). Client records live only in the worker's RAM for the active session; follow-up rounds are the customer re-running the flow. See gotchas — main does not fully honor this yet.

## Architecture map

| Layer | What | Canonical production |
|---|---|---|
| Backend | Flask in `bitmoji_credit_app/` — sessions, parsing, letters, Stripe, admin | Railway (`railway.toml`; gunicorn **single worker `-w 1`**, required) |
| Frontend | Next.js 16 in `frontend/` — the themed "journey" (map → dojo → koi-pond → garden → stairway → gate → watcher) | Vercel `bitmoji-guy5-min-credit-fix.vercel.app`, talks to Flask via `NEXT_PUBLIC_FLASK_URL` |
| Payments | Stripe Checkout (card) + manual Cash App `$AELabsCreditFix` / Chime `$AELabsPay` (admin-released) | keys pending from Sean |
| Mail | Click2Mail (`click2mail_integration.py`) | account/funding pending from Sean |
| Storage | **None by design** (ADR-0001) | — |

```
BitmojiGuy5MinCreditFix/
├── bitmoji_credit_app/     Flask — ACTIVE backend (app.py, cypher, click2mail, letters)
├── frontend/               Next.js themed journey — canonical UI (pending Sean's confirmation)
├── creditfix-next-import/  Sean's simpler alt frontend (Jul 10) — reference only, see gotchas
├── backend/                DEAD FastAPI app — do not build on; contains a committed creditfix.db
├── supabase/               legacy migrations from the abandoned persistence layer
├── docs/
│   ├── STATE.md            current built/wired/live state (read at session start)
│   └── decisions/          ADRs
├── _backups/, remotion-video/, *AUDIT*.md   reference/marketing artifacts — leave alone
└── railway.toml            Railway build/deploy config
```

Local dev: Flask on `127.0.0.1:5055` (macOS AirPlay squats on 5000), frontend on 3000 with `NEXT_PUBLIC_FLASK_URL` pointed at 5055. (NEST uses 8000/8100 — don't collide.)

## Session protocol

1. **Start:** read this file, then `docs/STATE.md`, then any GitHub Issue you're picking up.
2. **Work:** the Issue is the unit of scope. Verify load-bearing claims against ground truth (live endpoints, Railway/Vercel dashboards) before high-stakes changes.
3. **Finish (write-back is the definition of done):** if the session changed project state — infra, flows, decisions, what's-wired status — update `docs/STATE.md` **in the same PR**. Durable choices get an ADR in `docs/decisions/`.

## Git SOP

- All work on short-lived branches named `{person}/{slug}` (e.g. `sean/letters`, `ko/watcher`); merge via PR; **never direct-to-main, never force-push**.
- Commit at natural checkpoints with conventional messages (`feat:`, `fix:`, `docs:`, `chore:`).
- Push the branch and open a PR at session end.
- Work tracking: GitHub Issues + PRs on `Businessbear1981/BitmojiGuy5MinCreditFix`.

## Guardrails (hard rules)

- **Never push to main.** PRs only.
- **Never persist consumer data at rest** — no DB, no disk writes of PII/credit data, ever (ADR-0001). Uploaded report bytes are encrypted in memory, parsed from streams, dropped.
- **Never touch production environment** — Railway/Vercel env vars, Stripe/Click2Mail config — without explicit confirmation from a principal.
- **Never commit secrets** or data files. Keys live in env vars; the repo carries `.env.example` only.
- **Never scale past one gunicorn worker** — session state is in-memory; `-w 1` in `railway.toml` is load-bearing.
- **Never delete Sean's artifacts** (`creditfix-next-import/`, `_backups/`, `remotion-video/`, audit docs) without his ok — preservation is the norm here.
- Letters must cite specific FCRA/FDCPA sections; price changes touch `PRICE_CENTS` in `app.py` AND every frontend surface.

## Known gotchas

- **main contradicts the no-storage posture:** `bitmoji_credit_app/database.py` on main is still the Supabase/psycopg2 persistence layer, and `backend/creditfix.db` (SQLite) is committed. The completed no-storage rewire + hardened journey live on Kevin's branch `ko/no-storage-rewire-cleanup` (local, not yet pushed) — reconcile via PR rather than re-doing the work.
- **Three frontends exist; canonical is UNDECIDED (Sean's call pending):** (1) `frontend/` themed journey — recommended: consent gate, localStorage session fix, $24.99; (2) legacy Flask Jinja `templates/index.html`; (3) `creditfix-next-import/` — Sean's Jul-10 simpler build, but it regresses ($19.99 price, no consent gate → backend 422s, no session persistence across the Stripe redirect, drops the samurai armor). Mine #3 for layout only; don't build on it.
- **Price mismatch on main:** backend `PRICE_CENTS = 2499`; `creditfix-next-import` shows $19.99. Canonical price is **$24.99**.
- **Stripe redirect kills naive sessions:** the backend session id must survive the full-page Stripe round-trip — localStorage persistence (on Kevin's branch), not JS module state. Cookies don't work cross-origin Vercel↔Railway.
- **Admin release vs hold-nothing tension:** admin-released manual payments need the session still in RAM — one worker, no restart between pay and release. Acceptable for MVP.
- **Dev-mode checkout** (no Stripe key) marks paid in the session blob but doesn't sync the admin store — dev-only quirk.
- **Root `README.md` on main is Vite boilerplate** — wrong stack description; trust this file and `docs/STATE.md`.

## Where things live

| What | Where |
|---|---|
| Current built/wired/live state | `docs/STATE.md` |
| Durable decisions (ADRs) | `docs/decisions/` |
| Work tracking | GitHub Issues + PRs on `Businessbear1981/BitmojiGuy5MinCreditFix` |
| Letter templates + citations | `LETTER_GENERATOR_CITATIONS.md`, `bitmoji_credit_app/` |
| Frontend walkthrough | `FRONTEND_OVERVIEW.md` (partially stale — pre-dates the journey hardening) |
