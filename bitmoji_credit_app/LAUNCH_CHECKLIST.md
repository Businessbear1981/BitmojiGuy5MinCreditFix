# Launch Checklist — 5 Minutes to Credit Wellness

## Required Environment Variables (production will not start without these)

| Variable | Example | Notes |
|----------|---------|-------|
| `FLASK_ENV` | `production` | Enables all production guards |
| `SECRET_KEY` | 64+ random chars | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `STRIPE_SECRET_KEY` | `sk_live_...` | From Stripe dashboard |
| `STRIPE_PUBLISHABLE_KEY` | `pk_live_...` | From Stripe dashboard |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | From Stripe webhook config |
| `ADMIN_PASSWORD_HASH` | `$2b$12$...` | `python -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt()).decode())"` |

## Optional Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `ADMIN_USERNAME` | `admin` | Admin login username |
| `FRONTEND_URL` | `http://localhost:3000` | CORS origin for frontend |
| `SMTP_HOST` | (empty) | Email sending — skipped if not set |
| `SMTP_PORT` | `587` | |
| `SMTP_USER` | (empty) | |
| `SMTP_PASS` | (empty) | |
| `FROM_EMAIL` | `noreply@aelabs.com` | |
| `TESSERACT_CMD` | (empty) | Path to tesseract binary for OCR |
| `DB_PATH` | `creditfix.db` | SQLite database path |
| `SUBMISSION_TTL_SECONDS` | `7200` | In-memory session expiry (2 hours) |

## Pre-Launch Verification

- [ ] `FLASK_ENV=production` is set
- [ ] `SECRET_KEY` is a unique random string (not the dev default)
- [ ] `ADMIN_PASSWORD_HASH` is set (bcrypt hash, not plaintext)
- [ ] `STRIPE_SECRET_KEY` is a live key (not test key)
- [ ] `STRIPE_WEBHOOK_SECRET` is set and webhook is configured in Stripe dashboard
- [ ] HTTPS is enabled (reverse proxy or Render auto-SSL)
- [ ] Frontend `NEXT_PUBLIC_FLASK_URL` points to the production backend URL
- [ ] CORS `FRONTEND_URL` matches the actual frontend domain
- [ ] Stripe webhook endpoint is registered: `https://your-backend/api/stripe-webhook`
- [ ] Test a real payment end-to-end on staging before going live

## Data Lifecycle

| Data | Storage | Lifetime | Purge |
|------|---------|----------|-------|
| Uploaded files | Temp disk | Seconds | Deleted immediately after parsing |
| Parsed text / OCR output | In-memory only | Session TTL (2hr) | Auto-purged |
| Dispute items / letters | In-memory (encrypted) | Session TTL (2hr) | Auto-purged |
| Client PII (name/email/phone) | SQLite (encrypted) | 90 days | Auto-purged by background job |
| Follow-up metadata | SQLite | 90 days | Auto-purged |
| Payment state | SQLite | 90 days | Auto-purged |
| Admin log | In-memory | Process lifetime | No PII stored (initials + confirmation only) |

## Remaining Risks (honest assessment)

1. **No CSRF tokens yet** — Flask-WTF is available but not wired into the API routes. Acceptable for a JSON API consumed by a single frontend origin with SameSite cookies, but should be added for form-based admin routes.

2. **In-memory submissions lost on restart** — If the process restarts mid-session, users lose their workflow. Acceptable for limited launch. The database has their follow-up record.

3. **Background thread reliability** — Under gunicorn with multiple workers, the background thread runs in each worker. Could cause duplicate agent runs. For launch: use `--workers 1` or switch to external cron.

4. **No email verification** — Users can enter any email. Acceptable for limited launch since email is only used for follow-up notifications.

5. **Status lookup enumeration** — Rate-limited to 10/min but confirmation codes (AE-YYYYMMDD-XXXXX) are somewhat guessable. Low risk since status returns minimal info (no PII).

6. **Single-worker memory growth** — If traffic exceeds expectations, the in-memory submissions dict could grow. The TTL purge (every hour) mitigates this but monitor memory usage.

## Deployment Command (Render)

```
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

Use `--workers 1` for launch to avoid duplicate background thread issues. Scale workers after moving agents to external cron.
