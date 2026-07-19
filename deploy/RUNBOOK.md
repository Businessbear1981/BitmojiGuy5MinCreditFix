# Deploy Runbook — AE 5-Min Credit Fix

Everything below is copy-paste ready. Prereqs: `railway login` and `vercel login`
(both CLI sessions were expired as of 2026-07-18).

## 0. Generate production secrets (once)

```bash
python3 - <<'EOF'
import base64, os, secrets
print("PII_ENCRYPTION_KEY=" + base64.urlsafe_b64encode(os.urandom(32)).decode())
print("TERMS_TOKEN_SECRET=" + secrets.token_urlsafe(48))
print("CYPHER_SERVER_SECRET=" + secrets.token_urlsafe(48))
print("ADMIN_KEY=" + secrets.token_urlsafe(32))
EOF
```

Store these in a password manager. **Losing `PII_ENCRYPTION_KEY` mid-TTL makes
in-flight sessions undecryptable** (acceptable — they purge within 24h — but
don't rotate casually while sessions are live).

## 1. Backend — Railway

```bash
cd projects/clients/bitmojiguy-credit-fix
railway link          # pick (or create) the creditfix project
railway add -d postgres   # provisions Postgres, injects DATABASE_URL
```

Set variables (Stripe/Lob keys come from Sean; DEMO_MODE=true lets us launch
the flow before mail/email providers are live):

```bash
railway variables \
  --set "ENVIRONMENT=production" \
  --set "PII_ENCRYPTION_KEY=..." \
  --set "TERMS_TOKEN_SECRET=..." \
  --set "CYPHER_SERVER_SECRET=..." \
  --set "ADMIN_KEY=..." \
  --set "STRIPE_SECRET_KEY=sk_live_..." \
  --set "STRIPE_WEBHOOK_SECRET=whsec_..." \
  --set "LOB_API_KEY=live_..." \
  --set "LOB_WEBHOOK_SECRET=..." \
  --set "SENDGRID_API_KEY=..." \
  --set "FROM_EMAIL=noreply@ardanedgecapital.com" \
  --set "FRONTEND_URL=https://<vercel-domain>" \
  --set "ALLOWED_ORIGINS=https://<vercel-domain>" \
  --set "DEMO_MODE=false"
```

Deploy (root `railway.toml` already runs `uvicorn main:app --workers 2` from
`backend/` with `/api/health` as the healthcheck):

```bash
railway up
railway domain        # note the API URL
curl https://<railway-domain>/api/health   # expect {"status":"ok"}
```

## 2. Frontend — Vercel

```bash
cd frontend
vercel link           # pick the existing bitmoji-guy5-min-credit-fix project
vercel env add NEXT_PUBLIC_API_URL production   # paste https://<railway-domain>
vercel --prod
```

Then set `FRONTEND_URL` / `ALLOWED_ORIGINS` on Railway to the final Vercel
domain if it changed, and redeploy the backend.

## 3. Stripe webhook

In the Stripe dashboard (Sean's account): add endpoint
`https://<railway-domain>/api/webhooks/stripe` for `checkout.session.completed`,
copy the signing secret into `STRIPE_WEBHOOK_SECRET`.

## 4. Lob webhook

In the Lob dashboard: add endpoint `https://<railway-domain>/api/webhook/lob`
(tracking events), copy the secret into `LOB_WEBHOOK_SECRET`.

## 5. Post-deploy smoke test

```bash
API=https://<railway-domain>
curl -s $API/api/health
curl -s $API/api/fishbowl/status
# Full paid dry run: walk the site with a Stripe test card (or live $24.99 +
# immediate refund), confirm PDF download, email arrival, and Lob letter in
# the Lob dashboard (test env first).
```

## 6. CI (blocked)

`.github/workflows/ci.yml` exists locally but can't be pushed — the gh OAuth
token lacks the `workflow` scope. Fix with `gh auth refresh -s workflow`, then
commit and push the workflow file.

## Launch gates checklist

- [ ] Sean: live Stripe keys + webhook secret
- [ ] Sean: Lob API key (or Kevin creates account — billable, confirm first)
- [ ] Sean: perfected letter texts → `backend/ae_creditfix/templates.py`
- [ ] Sean: merge PR #3 (Kevin has no write access)
- [ ] Kevin: `railway login` + `vercel login`
- [ ] Legal: CROA memo action list (`docs/compliance/croa-positioning.md`)
