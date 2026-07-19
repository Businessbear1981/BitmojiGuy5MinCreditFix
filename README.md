# AE 5-Min Credit Fix

Consumer credit-dispute platform (AE Labs / Arden Edge Capital). Upload your
credit report, the app detects disputable items, generates FCRA-compliant
dispute letters for all three bureaus, and mails them after a one-time
$24.99 payment.

**Agent/contributor context lives in [AGENTS.md](AGENTS.md)** — read it first,
then [docs/STATE.md](docs/STATE.md) for current state.

## Layout

| Path | What |
|---|---|
| `backend/` | FastAPI API — cases, report parsing, letter engine, Stripe, Lob mail |
| `frontend/` | Next.js customer app (Vercel) |
| `docs/` | State + architecture decision records |
| `remotion-video/` | Marketing video project |

## Quick start

```bash
# Backend (Python 3.12+)
cd backend
pip install -r requirements.txt
cp ../.env.example .env   # fill in what you need; dev works with defaults
uvicorn main:app --reload --port 8000

# Frontend (Node 22)
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Tests: `cd backend && pytest`.

## Data posture

PII is stored **encrypted at the field level** and **hard-deleted after 24
hours** (ADR-0002, superseding ADR-0001). Uploaded documents are encrypted
with a per-session key before touching disk and purged on the same schedule.
