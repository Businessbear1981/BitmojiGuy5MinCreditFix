# BitmojiGuy Five-Minute Credit Fix — Deployment Guide

## Quick Start (5 minutes to live demo)

### 1. Deploy Backend to Render

```bash
# Push to GitHub
git add .
git commit -m "feat: Click2Mail integration, Credit Report Hook, Admin Release workflow"
git push origin main
```

Then on Render.com:
1. Create new **Web Service**
2. Connect GitHub repo
3. Set environment variables (from `.env.example`)
4. Deploy

**Key Variables:**
```
FLASK_ENV=production
SECRET_KEY=<generate-random-key>
ADMIN_KEY=ae-admin-2025
STRIPE_SECRET_KEY=sk_test_...
CLICK2MAIL_API_KEY=<your-key>
FRONTEND_URL=https://your-vercel-domain.vercel.app
```

### 2. Deploy Frontend to Vercel

```bash
cd frontend
vercel deploy --prod
```

**Key Variables:**
```
NEXT_PUBLIC_FLASK_URL=https://your-render-backend.onrender.com
NEXT_PUBLIC_ADMIN_KEY=ae-admin-2025
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER JOURNEY                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Intake (Step 1-2)  →  Upload (Dojo)  →  Review (Koi Pond) │
│                                                                 │
│  2. Payment (Stairway)  →  Queue for Admin Release             │
│                                                                 │
│  3. Admin Approves  →  Click2Mail Dispatch  →  Tracking        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Backend Flow

```
Flask Backend (Render)
├── /api/start                    (Intake)
├── /api/upload                   (Document upload + parsing)
├── /api/disputes                 (Extracted disputes)
├── /api/review                   (Dispute authorization)
├── /api/create-checkout          (Stripe payment)
├── /api/send-certified           (Dispatch - requires admin release)
│
├── Admin Release Queue
│   ├── /api/admin/queue-for-release      (Auto-queue after payment)
│   ├── /api/admin/approve-release        (Admin approves)
│   ├── /api/admin/reject-release         (Admin rejects)
│   ├── /api/admin/pending-queue          (View queue)
│   └── /api/admin/release-log            (Activity log)
│
├── Credit Report Hook
│   ├── /api/credit-report-guide          (AnnualCreditReport.com guide)
│   ├── /api/credit-report-bureaus        (Bureau contact info)
│   ├── /api/parse-credit-report          (Parse uploaded report)
│   └── /api/credit-report-status         (Check parse status)
│
└── Click2Mail Integration
    ├── PDF generation (ReportLab)
    ├── Base64 encoding
    ├── REST API v1 dispatch
    └── Job tracking
```

### Frontend Components

```
Next.js Frontend (Vercel)
├── /                             (Home)
├── /step/1-5                     (5-step wizard)
├── /dojo                         (Upload + Credit Report Guide)
├── /koi-pond                     (Dispute review)
├── /garden                       (Letter preview)
├── /stairway                     (Payment + Queue for Release)
├── /gate                         (Dispatch confirmation)
├── /watcher                      (Follow-up tracking)
├── /admin                        (Admin dashboard)
│   ├── Cases tab
│   ├── Pipeline tab
│   ├── Notifications tab
│   └── Release tab (NEW)
└── /map, /garden, /interstitial  (Cinematic scenes)
```

---

## Key Features Implemented

### ✅ Click2Mail Integration
- Professional PDF generation with ReportLab
- Proper REST API v1 authentication
- Base64 encoding for documents
- Escalation strategy (30/60/90 days)
- Bureau addresses + regulatory addresses

### ✅ Credit Report Hook
- AnnualCreditReport.com integration guide
- Credit report parser (PDF/CSV/TXT)
- Automatic dispute classification
- 7-year rule detection
- Bureau contact information

### ✅ Admin Release Workflow
- Auto-queue after payment
- Admin dashboard with pending queue
- Approve/reject with reasons
- Activity log tracking
- Real-time refresh

---

## Testing Checklist

### 1. User Flow
- [ ] Complete intake (Step 1-2)
- [ ] Upload documents (Dojo)
- [ ] View credit report guide
- [ ] Review disputes (Koi Pond)
- [ ] Process payment (Stairway)
- [ ] Verify auto-queue for admin release

### 2. Admin Flow
- [ ] Login to admin dashboard
- [ ] View pending releases
- [ ] Approve a release
- [ ] Verify Click2Mail dispatch
- [ ] Check activity log

### 3. Credit Report
- [ ] Upload credit report
- [ ] Verify parsing
- [ ] Check dispute extraction
- [ ] Confirm 7-year rule detection

### 4. Click2Mail
- [ ] Verify PDF generation
- [ ] Check base64 encoding
- [ ] Confirm API dispatch
- [ ] Track job status

---

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | Session encryption | Random 32-char string |
| `ADMIN_KEY` | Admin authentication | `ae-admin-2025` |
| `STRIPE_SECRET_KEY` | Stripe payments | `sk_test_...` |
| `CLICK2MAIL_API_KEY` | Click2Mail API | Your API key |
| `FRONTEND_URL` | CORS origin | `https://domain.vercel.app` |
| `NEXT_PUBLIC_FLASK_URL` | Backend URL (frontend) | `https://backend.onrender.com` |
| `NEXT_PUBLIC_ADMIN_KEY` | Admin key (frontend) | `ae-admin-2025` |

---

## Troubleshooting

### Backend won't start
```bash
# Check logs on Render
# Verify all env vars are set
# Check database connection
```

### Frontend can't reach backend
```bash
# Verify NEXT_PUBLIC_FLASK_URL is correct
# Check CORS settings in Flask
# Verify backend is running
```

### Click2Mail dispatch fails
```bash
# Check CLICK2MAIL_API_KEY
# Verify PDF generation works
# Check bureau addresses
```

### Admin release queue empty
```bash
# Verify payment flow calls queueForRelease()
# Check admin key in header
# Verify database is persisting
```

---

## Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Generate strong `SECRET_KEY`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/SSL
- [ ] Set up Sentry for error tracking
- [ ] Configure email notifications
- [ ] Test payment flow with Stripe test mode
- [ ] Test Click2Mail with test account
- [ ] Set up backup/restore procedures
- [ ] Document admin procedures
- [ ] Train admin team

---

## Support

For issues, contact: support@bitmojiguy.com
