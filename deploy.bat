@echo off
REM ═════════════════════════════════════════════════════════════════════════════
REM BitmojiGuy Five-Minute Credit Fix — Windows Deployment
REM ═════════════════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

echo.
echo 🚀 BitmojiGuy Deployment Script
echo ================================
echo.

REM Check if npm is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ npm not found. Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if vercel is installed
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo 📦 Installing Vercel CLI...
    call npm install -g vercel
)

set /p VERCEL_TOKEN="Enter your Vercel token: "

echo.
echo 1️⃣  Deploying Frontend to Vercel...
echo -----------------------------------
cd frontend
call vercel deploy --prod --token=%VERCEL_TOKEN%
for /f "tokens=*" %%i in ('vercel ls --token=%VERCEL_TOKEN% 2^>nul ^| findstr "bitmoji" ^| for /f "tokens=2" %%j in ('findstr /r "."') do @echo %%j') do set FRONTEND_URL=%%i
cd ..

if "!FRONTEND_URL!"=="" (
    echo ⚠️  Could not get frontend URL. Please check Vercel deployment.
    pause
    exit /b 1
)

echo ✅ Frontend deployed to: !FRONTEND_URL!

echo.
echo 2️⃣  Creating Render Backend Service...
echo --------------------------------------
echo.
echo ⚠️  IMPORTANT: Complete these steps manually on Render:
echo.
echo 1. Go to: https://dashboard.render.com
echo 2. Click: New Web Service
echo 3. Connect GitHub repo: BitmojiGuy5MinCreditFix
echo 4. Fill in:
echo    - Name: bitmoji-creditfix-api
echo    - Environment: Python 3
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: gunicorn -w 4 -b 0.0.0.0:$PORT bitmoji_credit_app.app:app
echo.
echo 5. Add Environment Variables:
echo    FLASK_ENV=production
echo    SECRET_KEY=ae-labs-production-2025-secret-key
echo    ADMIN_KEY=ae-admin-2025
echo    STRIPE_SECRET_KEY=sk_test_YOUR_KEY
echo    CLICK2MAIL_API_KEY=YOUR_KEY
echo    FRONTEND_URL=!FRONTEND_URL!
echo.
echo 6. Click: Create Web Service
echo 7. Wait 2-3 minutes for deployment
echo 8. Copy your backend URL and paste it below
echo.

set /p BACKEND_URL="Enter your Render backend URL (e.g., https://bitmoji-api.onrender.com): "

echo.
echo 3️⃣  Updating Frontend with Backend URL...
echo -------------------------------------------
cd frontend
call vercel env add NEXT_PUBLIC_FLASK_URL "!BACKEND_URL!" --token=%VERCEL_TOKEN%
call vercel deploy --prod --token=%VERCEL_TOKEN%
cd ..

echo.
echo ✅ DEPLOYMENT COMPLETE!
echo.
echo Live URLs:
echo   Frontend: !FRONTEND_URL!
echo   Backend:  !BACKEND_URL!
echo   Admin:    !FRONTEND_URL!/admin
echo   Admin Key: ae-admin-2025
echo.
echo Next steps:
echo 1. Test the user flow: !FRONTEND_URL!
echo 2. Test admin dashboard: !FRONTEND_URL!/admin
echo 3. Use admin key: ae-admin-2025
echo.
pause
