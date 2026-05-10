#!/bin/bash

# ═════════════════════════════════════════════════════════════════════════════
# BitmojiGuy Five-Minute Credit Fix — One-Command Deployment
# ═════════════════════════════════════════════════════════════════════════════

set -e

echo "🚀 BitmojiGuy Deployment Script"
echo "================================"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

echo ""
echo "1️⃣  Deploying Frontend to Vercel..."
echo "-----------------------------------"
cd frontend
vercel deploy --prod --token=$VERCEL_TOKEN
FRONTEND_URL=$(vercel ls --token=$VERCEL_TOKEN | grep "bitmoji" | head -1 | awk '{print $2}')
echo "✅ Frontend deployed to: $FRONTEND_URL"
cd ..

echo ""
echo "2️⃣  Creating Render Backend Service..."
echo "--------------------------------------"
echo ""
echo "⚠️  IMPORTANT: Complete these steps manually on Render:"
echo ""
echo "1. Go to: https://dashboard.render.com"
echo "2. Click: New Web Service"
echo "3. Connect GitHub repo: BitmojiGuy5MinCreditFix"
echo "4. Fill in:"
echo "   - Name: bitmoji-creditfix-api"
echo "   - Environment: Python 3"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: gunicorn -w 4 -b 0.0.0.0:\$PORT bitmoji_credit_app.app:app"
echo ""
echo "5. Add Environment Variables:"
echo "   FLASK_ENV=production"
echo "   SECRET_KEY=ae-labs-production-2025-secret-key"
echo "   ADMIN_KEY=ae-admin-2025"
echo "   STRIPE_SECRET_KEY=sk_test_YOUR_KEY"
echo "   CLICK2MAIL_API_KEY=YOUR_KEY"
echo "   FRONTEND_URL=$FRONTEND_URL"
echo ""
echo "6. Click: Create Web Service"
echo "7. Wait 2-3 minutes for deployment"
echo "8. Copy your backend URL and paste it below"
echo ""

read -p "Enter your Render backend URL (e.g., https://bitmoji-api.onrender.com): " BACKEND_URL

echo ""
echo "3️⃣  Updating Frontend with Backend URL..."
echo "-------------------------------------------"
cd frontend
vercel env add NEXT_PUBLIC_FLASK_URL "$BACKEND_URL" --token=$VERCEL_TOKEN
vercel deploy --prod --token=$VERCEL_TOKEN
cd ..

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "Live URLs:"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo "  Admin:    $FRONTEND_URL/admin"
echo "  Admin Key: ae-admin-2025"
echo ""
echo "Next steps:"
echo "1. Test the user flow: $FRONTEND_URL"
echo "2. Test admin dashboard: $FRONTEND_URL/admin"
echo "3. Use admin key: ae-admin-2025"
echo ""
