# Automated Deployment Setup (One-Time Only)

## What This Does
Once you complete these steps, every time you push code to GitHub, it automatically deploys to both Render (backend) and Vercel (frontend). **You never have to manually deploy again.**

---

## Step 1: Get Render API Key (2 minutes)

1. Go to: https://dashboard.render.com/account/api-tokens
2. Click: **Create API Token**
3. Name it: `GitHub Deploy`
4. Copy the token
5. Go to: https://github.com/Businessbear1981/BitmojiGuy5MinCreditFix/settings/secrets/actions
6. Click: **New repository secret**
7. Name: `RENDER_API_KEY`
8. Paste the token
9. Click: **Add secret**

---

## Step 2: Get Render Service ID (2 minutes)

1. Go to: https://dashboard.render.com
2. Click on your backend service (e.g., `bitmoji-creditfix-api`)
3. Copy the URL from the address bar (e.g., `https://dashboard.render.com/services/web/srv-abc123def456`)
4. Extract the service ID: `srv-abc123def456`
5. Go to: https://github.com/Businessbear1981/BitmojiGuy5MinCreditFix/settings/secrets/actions
6. Click: **New repository secret**
7. Name: `RENDER_SERVICE_ID`
8. Paste: `srv-abc123def456`
9. Click: **Add secret**

---

## Step 3: Get Vercel Token (2 minutes)

1. Go to: https://vercel.com/account/tokens
2. Click: **Create Token**
3. Name: `GitHub Deploy`
4. Expiration: 90 days
5. Copy the token
6. Go to: https://github.com/Businessbear1981/BitmojiGuy5MinCreditFix/settings/secrets/actions
7. Click: **New repository secret**
8. Name: `VERCEL_TOKEN`
9. Paste the token
10. Click: **Add secret**

---

## Step 4: Get Vercel Project IDs (2 minutes)

1. Go to: https://vercel.com/dashboard
2. Click on your project
3. Go to: **Settings** → **General**
4. Copy: **Project ID**
5. Go to: https://github.com/Businessbear1981/BitmojiGuy5MinCreditFix/settings/secrets/actions
6. Click: **New repository secret**
7. Name: `VERCEL_PROJECT_ID`
8. Paste the ID
9. Click: **Add secret**

10. Copy: **ORG ID** (from the URL or settings)
11. Click: **New repository secret**
12. Name: `VERCEL_ORG_ID`
13. Paste the ID
14. Click: **Add secret**

---

## Done!

Now whenever you push code:
```bash
git add .
git commit -m "your message"
git push origin master
```

**Automatically:**
1. ✅ Code deploys to Render (backend)
2. ✅ Code deploys to Vercel (frontend)
3. ✅ Both go live in 2-3 minutes
4. ✅ You get notified when done

---

## Verify It Works

1. Make a small change to a file
2. Push to GitHub
3. Go to: https://github.com/Businessbear1981/BitmojiGuy5MinCreditFix/actions
4. Watch the deployment run automatically
5. Check your live URLs to see the changes

---

## Troubleshooting

**Deployment failed?**
- Check: https://github.com/Businessbear1981/BitmojiGuy5MinCreditFix/actions
- Click the failed workflow
- Read the error message
- Fix the issue and push again

**Still stuck?**
- Verify all 4 secrets are added correctly
- Make sure Render & Vercel services are created first
- Check that service IDs are correct

---

That's it! You're done. Never manually deploy again.
