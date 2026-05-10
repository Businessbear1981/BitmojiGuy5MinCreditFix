# Deploy BitmojiGuy — Simple Step-by-Step Guide

**Total time: 10 minutes**

---

## PART 1: DEPLOY BACKEND TO RENDER (5 minutes)

### Step 1: Go to Render
1. Open browser
2. Go to: https://dashboard.render.com
3. Log in (or create account)

### Step 2: Create New Service
1. Click: **New +** button (top right)
2. Select: **Web Service**
3. Click: **Connect GitHub**
4. Find: `BitmojiGuy5MinCreditFix`
5. Click: **Connect**

### Step 3: Configure Service
Fill in these fields:

| Field | Value |
|-------|-------|
| **Name** | `bitmoji-creditfix-api` |
| **Environment** | `Python 3` |
| **Region** | `Oregon` (or closest to you) |
| **Branch** | `master` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -w 4 -b 0.0.0.0:$PORT bitmoji_credit_app.app:app` |

### Step 4: Add Environment Variables
Scroll down to **Environment** section. Click **Add Environment Variable** and add these:

| Key | Value |
|-----|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | `ae-labs-production-2025-secret-key` |
| `ADMIN_KEY` | `ae-admin-2025` |
| `STRIPE_SECRET_KEY` | `sk_test_YOUR_STRIPE_KEY_HERE` |
| `CLICK2MAIL_API_KEY` | `YOUR_CLICK2MAIL_KEY_HERE` |
| `FRONTEND_URL` | `https://your-vercel-domain.vercel.app` |

**Note:** You'll update `FRONTEND_URL` after deploying Vercel.

### Step 5: Deploy
1. Click: **Create Web Service**
2. Wait 2-3 minutes for deployment
3. When done, you'll see a green checkmark
4. Copy your backend URL (looks like: `https://bitmoji-creditfix-api.onrender.com`)
5. **Save this URL** — you'll need it for Vercel

---

## PART 2: DEPLOY FRONTEND TO VERCEL (5 minutes)

### Step 1: Go to Vercel
1. Open browser
2. Go to: https://vercel.com
3. Log in (or create account)

### Step 2: Create New Project
1. Click: **Add New** (top right)
2. Select: **Project**
3. Click: **Import Git Repository**
4. Find: `BitmojiGuy5MinCreditFix`
5. Click: **Import**

### Step 3: Configure Project
Fill in these fields:

| Field | Value |
|-------|-------|
| **Project Name** | `bitmoji-creditfix` |
| **Framework** | `Next.js` |
| **Root Directory** | `frontend` |

### Step 4: Add Environment Variables
Scroll down to **Environment Variables** section. Add these:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_FLASK_URL` | `https://your-render-backend-url.onrender.com` |
| `NEXT_PUBLIC_ADMIN_KEY` | `ae-admin-2025` |

**Replace** `your-render-backend-url` with the URL you copied from Render (Step 1, Part 1, Step 5).

### Step 5: Deploy
1. Click: **Deploy**
2. Wait 1-2 minutes for deployment
3. When done, you'll see a green checkmark
4. Copy your frontend URL (looks like: `https://bitmoji-creditfix.vercel.app`)
5. **Save this URL** — this is your live app

---

## PART 3: UPDATE RENDER WITH VERCEL URL (1 minute)

### Step 1: Go Back to Render
1. Go to: https://dashboard.render.com
2. Click on: `bitmoji-creditfix-api` service

### Step 2: Update Environment Variable
1. Click: **Environment** tab
2. Find: `FRONTEND_URL`
3. Click: **Edit**
4. Change value to your Vercel URL (from Part 2, Step 5)
5. Click: **Save**
6. Service will redeploy automatically (1-2 minutes)

---

## PART 4: TEST YOUR DEPLOYMENT (2 minutes)

### Test User Flow
1. Open your Vercel URL: `https://your-domain.vercel.app`
2. Click: **Start Your Free Review**
3. Fill in the form
4. Click: **Continue**
5. You should see the Dojo page

### Test Admin Dashboard
1. Go to: `https://your-domain.vercel.app/admin`
2. Enter admin key: `ae-admin-2025`
3. You should see the admin dashboard
4. Click: **Release** tab
5. You should see pending submissions

### If Something Breaks
1. Check browser console for errors (F12)
2. Check Render logs: https://dashboard.render.com → service → logs
3. Check Vercel logs: https://vercel.com → project → deployments

---

## DONE! 🎉

Your app is now live:
- **Frontend:** `https://your-domain.vercel.app`
- **Backend:** `https://your-domain.onrender.com`
- **Admin:** `https://your-domain.vercel.app/admin`
- **Admin Key:** `ae-admin-2025`

---

## Quick Reference

| Platform | URL | What It Does |
|----------|-----|--------------|
| **Render** | https://dashboard.render.com | Backend API |
| **Vercel** | https://vercel.com | Frontend website |
| **GitHub** | https://github.com/Businessbear1981/BitmojiGuy5MinCreditFix | Source code |

---

## Troubleshooting

**"Cannot reach backend"**
- Check `NEXT_PUBLIC_FLASK_URL` in Vercel is correct
- Make sure Render service is running (green checkmark)

**"Admin key invalid"**
- Check `NEXT_PUBLIC_ADMIN_KEY` in Vercel is `ae-admin-2025`
- Check `ADMIN_KEY` in Render is `ae-admin-2025`

**"Payment failed"**
- Check `STRIPE_SECRET_KEY` in Render is correct
- Make sure you're in Stripe test mode

**"Click2Mail error"**
- Check `CLICK2MAIL_API_KEY` in Render is correct
- Make sure API key is not expired

---

**Questions? Check the logs or ask for help!**
