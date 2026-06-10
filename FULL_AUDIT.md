# BitmojiGuy 5-Min CreditFix — FULL PROJECT AUDIT

**Generated:** 2026-05-10
**Auditor:** Claude Opus 4.6 (1M context)
**Project Root:** `C:/Users/sgill/BitmojiGuy5MinCreditFix`

---

## Table of Contents

1. [Frontend Pages](#frontend-pages)
2. [Frontend Components](#frontend-components)
3. [Frontend Lib/Store](#frontend-libstore)
4. [Frontend Config](#frontend-config)
5. [Backend Core](#backend-core)
6. [Backend Dispute Engine](#backend-dispute-engine)
7. [Deploy Config](#deploy-config)
8. [End-to-End Data Flow](#end-to-end-data-flow)
9. [Deployment Status](#deployment-status)

---

## Frontend Pages

### 1. frontend/app/page.tsx
Lines: 379
Purpose: Landing page — cinematic hero with orbiting kanji navigation and "Begin" CTA

Functions/Components:
- Home (line 15-378): Default export, renders full landing page with orbital ring, seascape background, pricing, and admin button

API Calls:
- None (pure display page)

Navigation:
- onClick → /map (line 280): "Begin Your Credit Fix" button
- onClick → /admin (line 347): "Admin Dashboard" button
- onClick → each scene route (line 108): Orbital kanji buttons navigate to /map, /dojo, /koi-pond, /garden, /stairway, /gate, /watcher

Data Flow:
- READS: `/seascape.jpg`, `/logo.png` (local assets), useShojiNav hook
- WRITES: Nothing

Issues Found:
- Video placeholders for "BitmojiGuy Intro" and "Atom Adam" (lines 301-343) are still placeholder divs — no actual video content

---

### 2. frontend/app/map/page.tsx
Lines: 205
Purpose: Step 1 — User intake form (name, email, phone, address, state, bureau, dispute reason)

Functions/Components:
- Step1Page (line 51-204): Default export, intake form with validation and submit handler
- update (line 66-67): Generic form field updater
- handleSubmit (line 69-83): Validates firstName + email, calls submitIntake API, navigates to /dojo

API Calls:
- POST /api/start (line 73): Via `submitIntake()` — sends name, email, phone, address, state

Navigation:
- onClick → /dojo (line 82): On successful submit (or error — continues anyway for demo)

Data Flow:
- READS: useShojiNav hook, local form state
- WRITES: Intake data to Flask backend via POST /api/start

Issues Found:
- Bureau and disputeReason collected in form but NOT sent to backend (line 73-79 only sends name, email, phone, address, state)
- Error is silently caught (line 80) — backend down still navigates forward

---

### 3. frontend/app/dojo/page.tsx
Lines: 342
Purpose: Step 2 — Document upload (Photo ID, Proof of Address, Credit Report) with armor warrior visualization

Functions/Components:
- DojoPage (line 38-228): Default export, manages 3 upload slots with armor metaphor
- UploadSlot (line 230-341): Sub-component for each file upload with drag-drop support
- handleFile (line 56-67): Uploads file via API, updates slot state and wizard store

API Calls:
- POST /api/upload (line 59): Via `uploadDocument(file, key)` — sends file as FormData with type='id'|'address'|'report'

Navigation:
- onClick → /map (line 189): Back button
- onClick → /koi-pond (line 200): Continue button (disabled until all 3 uploads complete)

Data Flow:
- READS: useWizardStore (upload state), useShojiNav
- WRITES: Files to Flask via POST /api/upload, updates wizardStore upload flags

Issues Found:
- Step label says "Step 2 of 7" (line 113) but landing shows 5-click flow
- Background image loaded from CloudFront CDN URL (line 73)

---

### 4. frontend/app/koi-pond/page.tsx
Lines: 323
Purpose: Step 3 — Review and authorize parsed disputes; toggle individual items on/off

Functions/Components:
- KoiPondPage (line 38-322): Default export, fetches disputes, displays toggleable list
- toggle (line 67-69): Toggles dispute authorization for individual items
- handleContinue (line 73-99): Sends authorized disputes to /api/review, navigates to /garden

API Calls:
- GET /api/disputes (line 49): Via `getDisputes()` — fetches parsed dispute items from session
- POST /api/review (line 87): Via `reviewDisputes(authorized, [])` — sends authorized items, generates letters

Navigation:
- onClick → /dojo (line 288): Back button
- onClick → /garden (line 90): On successful review

Data Flow:
- READS: Dispute items from Flask backend
- WRITES: Authorized disputes to Flask via POST /api/review (triggers letter generation)

Issues Found:
- Background image from CloudFront CDN (line 105)
- If no disputes found, tells user to go back to Dojo — no inline upload option

---

### 5. frontend/app/garden/page.tsx
Lines: 389
Purpose: Step 4 — Display generated letters in a 3-column grid with rake animation and letter preview modal

Functions/Components:
- GardenPage (line 30-388): Default export, fetches letters, shows generation animation, displays grid
- openLetter (line 39-49): Fetches individual letter detail for modal preview

API Calls:
- GET /api/letters (line 55): Via `getLetters()` — fetches all generated letters
- GET /api/letters/{index} (line 42): Via `getLetterById(index)` — fetches single letter detail

Navigation:
- onClick → /koi-pond (line 257): Back button
- onClick → /stairway (line 268): Continue to payment

Data Flow:
- READS: Letters from Flask, letter detail for modal
- WRITES: Nothing

Issues Found:
- Letters endpoint requires payment (Flask returns 403 if unpaid) but Garden page is before Stairway (payment). This means in production, the GET /api/letters call will fail for unpaid users — the page falls back to 15 demo placeholder letters (line 187-192)
- Background from CloudFront CDN (line 90)

---

### 6. frontend/app/stairway/page.tsx
Lines: 268
Purpose: Step 5 — Payment page ($24.99) with Stripe card, Cash App, and Chime options

Functions/Components:
- StairwayPage (line 12-267): Default export, handles 3 payment methods
- handleCard (line 18-37): Creates Stripe checkout session or marks paid in dev mode, queues for admin release
- handleManual (line 42-62): Handles Cash App / Chime manual payment, shows pending confirmation

API Calls:
- POST /api/create-checkout (line 21): Via `createCheckout()` — creates Stripe checkout session
- POST /api/manual-pay (line 44): Via `manualPay(method)` — records pending manual payment
- POST /api/admin/queue-for-release (line 27, 49): Via `queueForRelease()` — queues submission for admin review

Navigation:
- onClick → /gate (line 27, 50): After successful payment
- onClick → /garden (line 250): Back to letters

Data Flow:
- READS: useWizardStore (setPaid), useShojiNav
- WRITES: Payment status to Flask, queues for admin release

Issues Found:
- Cash App handle `$AELabsCreditFix` and Chime handle `$AELabsPay` are hardcoded in UI (lines 204, 219)
- In dev mode (no Stripe key), payment is auto-approved and navigates to /gate

---

### 7. frontend/app/gate/page.tsx
Lines: 249
Purpose: Step 6 — Dispatch letters via certified mail with postage class selection

Functions/Components:
- GatePage (line 12-248): Default export, handles dispatch via Click2Mail or generates local confirmation
- handleDispatch (line 19-44): Sends POST to /api/send-certified, falls back to local confirmation code on error

API Calls:
- POST /api/send-certified (line 24): Direct fetch (not via api.ts) — sends mailClass preference

Navigation:
- onClick → /stairway (line 218): Back button
- onClick → /watcher (line 229): Continue to tracking (only after dispatch confirmation)

Data Flow:
- READS: useShojiNav, NEXT_PUBLIC_FLASK_URL env var
- WRITES: Dispatch request to Flask

Issues Found:
- Uses direct fetch() call (line 24) instead of the `sendCertified()` wrapper from api.ts
- On fetch error (Flask down), still generates a fake confirmation code (line 39) — user sees success even if nothing was dispatched
- No payment verification on this page — relies on backend to check

---

### 8. frontend/app/watcher/page.tsx
Lines: 442
Purpose: Step 7 — 30/60/90 day tracking dashboard with subscription ($10.99), milestone timeline, partner offers

Functions/Components:
- WatcherPage (line 81-441): Default export, shows tracking status or subscription gate
- handleSubscribe (line 106-123): Subscribes to watcher via API
- handleFollowup (line 125-138): Fetches follow-up letters for a specific milestone day

API Calls:
- GET /api/watcher/status (line 94): Via `getWatcherStatus()` — fetches tracking data
- POST /api/watcher/subscribe (line 110): Via `subscribeWatcher()` — subscribes with notification preference
- GET /api/followup-letters/{day} (line 129): Via `getFollowupLetters(day)` — fetches follow-up letters

Navigation:
- onClick → /gate (line 417): Back button
- onClick → / (line 425): Return to start
- External links → Partner apply URLs (lines 46-78): Chime, Cleo, Amex Platinum, Capital One Secured, Capital One Quicksilver

Data Flow:
- READS: Watcher tracking status, follow-up letters, notification history
- WRITES: Watcher subscription to Flask

Issues Found:
- Partner promo codes (AECREDITFIX, AELABS2025, AE-AMEX-PLAT, etc.) appear to be placeholder/aspirational — no affiliate tracking
- Watcher uses local `/watcher.png` for background (line 146) unlike other pages that use CDN

---

### 9. frontend/app/admin/page.tsx
Lines: 746
Purpose: Admin dashboard — login gate, case management, pipeline stats, notification queue, release queue

Functions/Components:
- AdminPage (line 76-745): Default export, full admin dashboard with tabs
- fetchData (line 92-117): Fetches submissions, pipeline, pending notifications in parallel
- handleLogin (line 123-140): Authenticates admin via /admin/auth
- approvePayment (line 142-155): Approves pending manual payment
- sendDMNotification (line 157-170): Marks social media DM as sent
- runAction (line 172-183): Runs admin endpoint (agents, follow-ups, purge)
- exportCSV (line 185-198): Exports filtered cases as CSV
- getFiltered (line 200-213): Filters cases by search, status, source

API Calls:
- POST /admin/auth (line 126): Admin login with key
- GET /admin/api/submissions (line 95): Fetch all cases + stats
- GET /admin/api/pipeline (line 96): Fetch watcher pipeline stats + agent log
- GET /admin/api/pending-notifications (line 97): Fetch pending social DMs
- POST /admin/api/approve-payment (line 145): Approve manual payment
- POST /api/watcher/notify (line 161): Mark notification sent
- POST /admin/api/run-agents (line 418): Trigger all watcher agents
- POST /admin/api/run-followups (line 419): Trigger follow-up check
- POST /admin/api/run-purge (line 420): Trigger 90-day data purge

Navigation:
- onClick → / (line 279, 317): Back to app

Data Flow:
- READS: Admin stats, case entries (with full PII), pipeline data, agent log, pending DMs
- WRITES: Payment approvals, notification logs, agent runs

Issues Found:
- Admin auth uses session cookie — not token-based, relies on Flask session

---

### 10. frontend/app/interstitial/page.tsx
Lines: 45
Purpose: Placeholder interstitial page — "Phase 4 — Art of War Interstitial" with single button

Functions/Components:
- InterstitialPage (line 5-44): Default export, simple placeholder

Navigation:
- onClick → /step/1 (line 26): "Enter the Dojo" button

Data Flow:
- READS: useShojiNav
- WRITES: Nothing

Issues Found:
- Links to /step/1 which is a legacy route (see below)
- Appears to be unused/orphaned — no other page links here

---

### 11-15. frontend/app/step/1-5/page.tsx
Lines: N/A
Purpose: Legacy step pages — step/1 exists (as .tsx and .tsx.bak), step/2-5 exist but are likely superseded by the scene-based flow

Issues Found:
- These are LEGACY pages from an earlier 5-step wizard flow
- The current app uses scene-based routing (/map, /dojo, /koi-pond, etc.)
- step/1/page.tsx appears to be a copy of the map/page.tsx intake form
- step/2-5 may be stale code — the main flow skips them entirely

---

## Frontend Components

### 16. frontend/components/Providers.tsx
Lines: 29
Purpose: Root provider wrapper — mounts ShojiNavProvider, ParticleEffects, ShojiDoors, CinematicVignette globally

Functions/Components:
- GlobalDoors (line 8-11): Reads shojiOpen state, passes to ShojiDoors
- Providers (line 13-28): Wraps children with ShojiNavProvider, renders global effects

Data Flow:
- READS: useShojiNav (shojiOpen state)
- WRITES: Nothing

Dependencies: ShojiNavProvider, ShojiDoors, ParticleEffects, CinematicVignette

---

### 17. frontend/components/warrior/ArmorWarrior.tsx
Lines: 266
Purpose: SVG warrior figure that progressively gains armor pieces as documents upload

Functions/Components:
- ArmorWarrior (line 22-265): Animated warrior with 3 armor pieces (helm, breastplate, sword)
  - Uses framer-motion AnimatePresence for spring animations
  - Tracks armor count changes for flash/shake effects

Data Flow:
- READS: idUploaded, addressUploaded, reportUploaded, swordUnsheathed props
- WRITES: Nothing

Dependencies: framer-motion

Issues Found:
- References `/bitmoji-armored.png` (line 72) — static asset must be in public/

---

### 18. frontend/components/shoji/ShojiDoors.tsx
Lines: 73
Purpose: Animated sliding shoji door transition effect — left/right panels slide open/closed

Functions/Components:
- ShojiDoors (line 13-72): Framer-motion animated dual-panel door overlay

Data Flow:
- READS: isOpen prop
- WRITES: Nothing

Dependencies: framer-motion

---

### 19. frontend/components/nav/TopNav.tsx
Lines: 134
Purpose: Top navigation bar with logo/stopwatch SVG, 7 step dots, and tagline

Functions/Components:
- TopNav (line 12-133): Navigation bar with clickable step dots

Navigation:
- onClick → /map, /dojo, /koi-pond, /garden, /stairway, /gate, /watcher (line 71): Step dots navigate to corresponding routes

Data Flow:
- READS: currentStep prop, useShojiNav
- WRITES: Nothing

Issues Found:
- Step dots are always clickable (no guard preventing forward navigation without completing steps)

---

### 20. frontend/components/sidebar/WizardSidebar.tsx
Lines: 123
Purpose: Left sidebar with MrBeeks mascot, speech bubble, and step navigation

Functions/Components:
- WizardSidebar (line 33-122): Sidebar with step list and mascot

Navigation:
- onClick → each step route (line 76): All 7 step routes are clickable

Data Flow:
- READS: step prop, mascotSpeech prop, useShojiNav
- WRITES: Nothing

---

### 21. frontend/components/scene/SceneLayout.tsx
Lines: 163
Purpose: Cinematic scene wrapper with 6 visual layers (background, overlay, lighting, breathing motif, vignette, grain, kanji watermark)

Functions/Components:
- SceneLayout (line 11-82): Multi-layer visual wrapper using preset configs
- BreathingMotif (line 84-162): SVG-based animated motifs (ripples, embers, petals, scrolls, mist)

Data Flow:
- READS: preset prop, loads from PRESETS map
- WRITES: Nothing

Dependencies: ./scenePresets (ScenePresetKey, PRESETS)

---

### 22. frontend/components/dojo/CreditReportGuide.tsx
Lines: 356
Purpose: Expandable guide for obtaining free credit reports — fetches data from Flask API

Functions/Components:
- CreditReportGuide (line 38-355): Fetches guide + bureau info, renders steps, bureau contacts, FAQ

API Calls:
- GET /api/credit-report-guide (line 48): Fetches step-by-step guide
- GET /api/credit-report-bureaus (line 49): Fetches bureau contact info

Data Flow:
- READS: Guide data from Flask
- WRITES: Nothing

Dependencies: lucide-react (ExternalLink, CheckCircle, AlertCircle)

---

### 23. frontend/components/effects/ParticleEffects.tsx
Lines: 57
Purpose: Cherry blossom particle system — spawns floating particles every 800ms

Functions/Components:
- ParticleEffects (line 5-56): Continuous particle generator with auto-cleanup

Issues Found:
- Creates new particles every 800ms indefinitely — potential memory/performance concern on long sessions

---

### 24. frontend/components/effects/CinematicVignette.tsx
Lines: 36
Purpose: Animated vignette overlay with breathing box-shadow effect

Functions/Components:
- CinematicVignette (line 11-35): Fixed-position overlay with framer-motion animated shadow

Dependencies: framer-motion

---

### 25. frontend/components/effects/DepthOfField.tsx
Lines: 39
Purpose: Wrapper component adding CSS blur and radial gradient depth effect

Functions/Components:
- DepthOfField (line 12-38): Applies foreground/background blur to children

Issues Found:
- Not referenced by any page — appears unused in current codebase

---

### 26. frontend/components/effects/SoundDesign.tsx
Lines: 100
Purpose: WebAudio API ambient sound generator — plays subtle oscillator tones per scene

Functions/Components:
- SoundDesign (line 10-99): Audio-only component, initializes on first click/touch, plays sine wave tones

Issues Found:
- Not referenced by any page or Providers — appears unused in current codebase

---

### 27. frontend/components/mascot/MrBeeks.tsx
Lines: 78
Purpose: SVG mascot — yellow duck character with sign text

Functions/Components:
- MrBeeks (line 7-77): SVG-rendered duck mascot with optional sign card

---

### 28. frontend/components/admin/ReleaseQueue.tsx
Lines: 387
Purpose: Admin release queue — approve/reject pending submissions for mailing

Functions/Components:
- ReleaseQueue (line 26-386): Full CRUD for pending release queue with activity log
- fetchPendingQueue (line 35-47): Fetches pending queue via X-Admin-Key header
- fetchReleaseLog (line 50-62): Fetches release activity log
- handleApprove (line 65-88): Approves release for a session
- handleReject (line 91-117): Rejects release with reason

API Calls:
- GET /api/admin/pending-queue (line 37): With X-Admin-Key header
- GET /api/admin/release-log (line 52): With X-Admin-Key header
- POST /api/admin/approve-release (line 68): Approve submission
- POST /api/admin/reject-release (line 93): Reject submission

Issues Found:
- ADMIN_KEY is exposed in frontend code (line 8): `const ADMIN_KEY = process.env.NEXT_PUBLIC_ADMIN_KEY ?? 'ae-admin-2025'` — this leaks the admin key to the client bundle
- Polls every 10 seconds (line 122-126) — could be heavy on backend

---

## Frontend Lib/Store

### 29. frontend/lib/api.ts
Lines: 177
Purpose: Central API client — all Flask backend communication functions

Functions/Components:
- submitIntake (line 3-10): POST /api/start — intake form submission
- uploadDocument (line 12-17): POST /api/upload — file upload with FormData
- getDisputes (line 19-21): GET /api/disputes — fetch parsed disputes
- getLetters (line 23-25): GET /api/letters — fetch all generated letters
- getLetterById (line 27-29): GET /api/letters/{index} — fetch single letter
- createCheckout (line 31-38): POST /api/create-checkout — Stripe checkout
- reviewDisputes (line 40-47): POST /api/review — submit authorized disputes
- manualPay (line 49-56): POST /api/manual-pay — Cash App/Chime payment
- getFollowupLetters (line 58-60): GET /api/followup-letters/{day} — follow-up letters
- getWatcherStatus (line 62-64): GET /api/watcher/status — tracking status
- subscribeWatcher (line 66-73): POST /api/watcher/subscribe — watcher subscription
- getCreditReportGuide (line 79-81): GET /api/credit-report-guide
- getCreditReportBureaus (line 83-85): GET /api/credit-report-bureaus
- parseCreditReport (line 87-94): POST /api/parse-credit-report
- getCreditReportStatus (line 96-98): GET /api/credit-report-status
- queueForRelease (line 104-111): POST /api/admin/queue-for-release
- sendCertified (line 113-120): POST /api/send-certified
- adminAuth (line 130-136): POST /admin/auth
- adminGetSubmissions (line 139-141): GET /admin/api/submissions
- adminGetPipeline (line 143-145): GET /admin/api/pipeline
- adminGetPendingNotifications (line 147-149): GET /admin/api/pending-notifications
- adminApprovePayment (line 151-158): POST /admin/api/approve-payment
- adminNotifyClient (line 160-166): POST /api/watcher/notify
- adminRunAction (line 168-176): POST to arbitrary admin endpoint

Data Flow:
- READS: NEXT_PUBLIC_FLASK_URL env var (defaults to http://localhost:5000)
- WRITES: All API calls include credentials: 'include' for session cookies

---

### 30. frontend/lib/adminApi.ts
Lines: 54
Purpose: Admin operations console API client — more advanced admin functions

Functions/Components:
- adminLogin (line 18-19): POST /op-console/api/login — TOTP-based login
- adminLogout (line 20): POST /op-console/api/logout
- setupOperator (line 21-22): POST /op-console/api/setup-operator
- getQueue (line 25): GET /op-console/api/queue
- getConsumer (line 26): GET /op-console/api/consumer/{sid}
- getStats (line 27): GET /op-console/api/stats
- getNotifications (line 28): GET /op-console/api/notifications
- toggleRelease (line 31-32): POST /op-console/api/toggle-release
- releaseLetters (line 33-34): POST /op-console/api/release
- revokeLetters (line 35-36): POST /op-console/api/revoke
- markMailed (line 37-38): POST /op-console/api/mark-mailed
- logResponse (line 39-40): POST /op-console/api/log-response
- addNote (line 41-42): POST /op-console/api/add-note
- getAuditLog (line 43-44): GET /op-console/api/audit-log
- getUnmatchedPayments (line 47): GET /op-console/api/unmatched-payments
- logUnmatchedPayment (line 48-49): POST /op-console/api/unmatched-payments/log
- linkUnmatchedPayment (line 50-51): POST /op-console/api/unmatched-payments/{id}/link
- resolveUnmatchedPayment (line 52-53): POST /op-console/api/unmatched-payments/{id}/resolve

Issues Found:
- All /op-console/api/* endpoints have NO corresponding Flask routes in app.py — this entire API module is orphaned/aspirational
- TOTP-based auth (adminLogin with totp_code) is not implemented in backend

---

### 31. frontend/lib/meshy.ts
Lines: 121
Purpose: Meshy AI 3D model generation API client for scene assets and characters

Functions/Components:
- meshyPost (line 7-17): POST to Meshy API v2
- meshyGet (line 19-24): GET from Meshy API v2
- generateWarrior (line 28-36): Generate samurai warrior 3D model
- getWarriorModel (line 38-51): Poll warrior model generation status
- generateScene (line 55-63): Generate scene 3D model
- getSceneModel (line 65-72): Poll scene model status
- checkAllJobs (line 76-96): Batch status check for multiple tasks
- SCENE_PROMPTS (line 100-108): Pre-defined prompts for all scene assets
- generateMrBeeks (line 112-120): Generate mascot 3D model

API Calls:
- POST https://api.meshy.ai/openapi/v2/text-to-3d: Multiple generation endpoints
- GET https://api.meshy.ai/openapi/v2/text-to-3d/{taskId}: Status polling

Issues Found:
- MESHY_API_KEY read from server env var (line 5) — this module is meant for server-side use but lives in frontend/lib
- Not referenced by any current page — used for asset generation pipeline, not runtime

---

### 32. frontend/lib/parseReport.ts
Lines: 439
Purpose: Client-side credit report parser — extracts text from files, scans for disputes using regex

Functions/Components:
- extractTextFromFile (line 114-162): File format detection via magic bytes (PDF, ZIP/DOCX, image, HTML, text)
- extractTextFromZipDoc (line 164-189): DOCX/ODT text extraction from ZIP archives
- extractTextFromPdf (line 191-220): PDF text extraction via pdfjs-dist (dynamic import with fallback)
- parseTextForDisputes (line 239-259): Regex-based dispute category detection (7 types)
- extractStructuredAccounts (line 261-312): Structured account extraction using known creditor list
- classifyDisputeItems (line 314-340): SOL-aware dispute classification
- parseDate (line 342-367): Multi-format date parser
- parseReport (line 378-438): Main export — orchestrates full parse pipeline

Data Flow:
- READS: File object, state code
- WRITES: Returns ParseResult with items, rawText, parsedCategories, accountCount

Issues Found:
- Client-side parser is a fallback — the primary parse happens on Flask backend
- Not directly imported by any current page — may be unused in the current flow
- Contains 47 known creditor names hardcoded (line 68-78)

---

### 33. frontend/store/wizardStore.ts
Lines: 40
Purpose: Zustand store for wizard state — tracks uploads, form data, payment status

Functions/Components:
- useWizardStore (line 30-39): Zustand store with:
  - currentStep: number
  - uploads: { idUploaded, addressUploaded, reportUploaded, swordUnsheathed }
  - formData: { firstName, lastName, address, state, bureau, disputeReason }
  - paid: boolean
  - setStep, setUpload, setFormData, setPaid: mutators

Issues Found:
- formData in store is never populated — map/page.tsx uses local useState instead
- Store state is ephemeral (no persistence) — lost on page refresh

---

### 34. frontend/lib/shojiNav.tsx
Lines: 59
Purpose: Shoji door navigation system — context provider that coordinates door close/open animations with route changes

Functions/Components:
- useShojiNav (line 18-20): Hook returning { shojiOpen, setShojiOpen, navigateTo }
- ShojiNavProvider (line 22-58): Context provider managing door animation state
  - Doors start CLOSED (line 24)
  - navigateTo: closes doors → waits 1100ms → router.push → doors reopen after 300ms (line 39-51)

Data Flow:
- READS: useRouter, usePathname from next/navigation
- WRITES: Controls ShojiDoors animation state

---

## Frontend Config

### 35. frontend/package.json
Lines: 34
Purpose: Frontend dependency manifest

Key Dependencies:
- next: 16.2.3
- react: 19.2.4
- framer-motion: ^12.38.0
- zustand: ^5.0.12
- three: ^0.183.2, @react-three/fiber: ^9.6.0, @react-three/drei: ^10.7.7
- lucide-react: ^1.14.0
- tailwindcss: ^4

Issues Found:
- Three.js + R3F dependencies are installed but NOT used by any current page — no 3D rendering in active codebase
- Next.js 16.2.3 is very recent

---

### 36. frontend/vercel.json
Lines: 27
Purpose: Vercel deployment configuration with security headers

Config:
- buildCommand: npm run build
- framework: nextjs
- Headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection on all routes

Issues Found:
- No CORS or CSP headers configured
- No redirects configured

---

### 37. frontend/app/layout.tsx
Lines: 34
Purpose: Root layout — loads Google Fonts, wraps in Providers

Functions/Components:
- RootLayout (line 27-33): Mounts Cinzel Decorative, Cinzel, Rajdhani fonts via next/font/google

Dependencies: Providers.tsx, globals.css

---

### 38. frontend/components/scene/scenePresets.ts
Lines: 130
Purpose: Scene preset definitions — background images, accent colors, kanji, lighting, breathing motifs for 8 scene types

Presets:
- landing: /seascape.jpg, gold accent
- warrior: /maproom.jpg, gold accent, embers
- water: /koipond-meshy.png, green accent, ripples
- wisdom: /scrollroom.jpg, purple accent, scrolls
- gold: /sandgarden.jpg, orange accent, embers
- nirvana: CloudFront CDN URL (dragon gate), red accent, petals
- interstitial: /interstitial.jpg, gold accent, mist
- command: /wartable.jpg, bronze accent, scrolls

---

## Backend Core

### 38. bitmoji_credit_app/app.py
Lines: 2461
Purpose: Flask application — complete backend with all API routes, dispute parsing, letter generation, payment processing, admin dashboard

Functions/Components:
- _derive_key (line 111-114): SHA-256 key derivation from session+IP+timestamp
- encrypt_data / decrypt_data (line 117-123): Fernet encryption/decryption
- store_submission (line 129-149): Encrypt and store submission, update admin log
- load_submission (line 152-159): Decrypt and load submission
- create_client_profile (line 183-218): Factory for structured client profile JSON
- parse_text_for_disputes (line 296-306): Regex-based dispute detection (7 categories)
- extract_structured_accounts (line 337-370): Line-by-line creditor matching with known creditor list
- classify_dispute_items (line 410-433): Auto-classify with SOL checking
- extract_text_from_pdf (line 436-446): pdfplumber text extraction (max 30 pages)
- extract_text_from_image (line 449-455): pytesseract OCR (optional)
- extract_text_from_docx (line 459-465): python-docx text extraction
- extract_text_from_html (line 469-477): BeautifulSoup HTML text extraction
- parse_uploaded_files (line 480-509): Multi-format file parser orchestrator
- generate_letters (line 1350-1454): Generate 1 combined letter per bureau (3 total)
- build_state_law_block (line 1314-1347): Build comprehensive state-specific legal paragraph
- send_confirmation_email (line 1461-1481): SMTP email sender
- _mark_paid (line 1510-1525): Mark submission paid, compute follow-up dates, save to DB
- _background_jobs (line 2251-2267): Hourly background loop (enroll, run agents, purge)

Routes:
- GET / (line 1532): Render Jinja2 index template
- GET /health (line 1537): Health check
- POST /api/start (line 1543): Create session, intake data
- POST /api/upload (line 1571): Upload + parse documents
- GET /api/disputes (line 1620): Get parsed dispute items
- POST /api/review (line 1631): Authorize disputes, generate letters
- POST /api/create-checkout (line 1671): Create Stripe checkout session
- POST /api/manual-pay (line 1700): Record manual payment (pending)
- POST /admin/api/approve-payment (line 1720): Admin approve payment
- GET /api/payment-success (line 1735): Stripe redirect callback
- POST /api/stripe-webhook (line 1746): Stripe webhook handler
- GET /api/letters (line 1770): Get letters (requires payment)
- GET /api/letters/{index} (line 1782): Get single letter detail
- POST /api/send-certified (line 1813): Dispatch via Click2Mail
- POST /api/watcher/subscribe (line 1866): Subscribe to watcher ($10.99)
- GET /api/watcher/payment-success (line 1935): Watcher Stripe callback
- GET /api/watcher/status (line 1948): Get watcher tracking status
- POST /api/watcher/notify (line 1996): Send milestone notification
- GET /admin/api/pending-notifications (line 2070): Get pending social DMs
- GET /api/status/{confirmation} (line 2104): Lookup by confirmation code
- GET /admin/login (line 2114): Admin login page
- POST /admin/auth (line 2119): Admin authentication
- GET /admin (line 2127): Admin dashboard (Jinja2)
- GET /admin/api/submissions (line 2135): Admin API — all cases + stats
- POST /admin/api/run-followups (line 2143): Trigger follow-up engine
- POST /admin/api/run-purge (line 2153): Trigger 90-day purge
- POST /admin/api/run-agents (line 2160): Trigger all watcher agents
- POST /admin/api/run-sage (line 2171): Trigger Triple Sage AI refresh
- GET /admin/api/pipeline (line 2184): Get pipeline stats + agent log
- GET /admin/api/pipeline/queue (line 2195): Get agent queues
- GET /admin/api/chain (line 2208): View blockchain ledger
- GET /admin/api/chain/{session_id} (line 2219): View chain for client
- GET /api/followup-letters/{day} (line 2231): Get follow-up letters (30/60/90)
- POST /api/admin/queue-for-release (line 2290): Queue for admin review
- POST /api/admin/approve-release (line 2307): Admin approve release
- POST /api/admin/reject-release (line 2329): Admin reject release
- GET /api/admin/pending-queue (line 2352): View pending releases
- GET /api/admin/release-log (line 2366): View release log
- GET /api/credit-report-guide (line 2385): Credit report guide
- GET /api/credit-report-bureaus (line 2395): Bureau contact info
- POST /api/parse-credit-report (line 2405): Parse uploaded credit report
- GET /api/credit-report-status (line 2446): Credit report status

Data Flow:
- READS: request data, encrypted in-memory submissions dict, SQLite DB
- WRITES: submissions dict, admin_log list, SQLite via database module

Letter Templates (lines 582-1159):
- 7 dispute types x 3 variants = 21 templates (collections, late_payments, wrong_addresses, unknown_accounts, aged_debt, inquiries, identity_theft) + 3 MOV demand templates
- State law database for all 50 states + DC (lines 516-568)
- Federal case law citations per dispute type (lines 1168-1208)
- Statutory citations per dispute type (lines 1212-1265)
- State-specific case precedent for TX, CA, WA, FL, NY, IL, GA (lines 1269-1311)

Issues Found:
- In-memory `submissions` dict is ephemeral — lost on server restart (SQLite is backup)
- PRICE_CENTS = 2499 ($24.99) but CLAUDE.md says $19.99 — documentation is stale
- generate_letters now creates 1 combined letter per bureau (3 total), not 15 individual letters — but UI says "15 letters" in multiple places
- Payment success redirect goes to `/#step-5` (line 1743) which is the old Jinja2 flow, not the Next.js flow
- Background thread starts at module import time (line 2277-2278)

---

### 39. bitmoji_credit_app/database.py
Lines: 286
Purpose: SQLite persistence layer with Fernet encryption for PII

Functions/Components:
- _app_fernet (line 16-19): App-level encryption key from SECRET_KEY
- init_db (line 41-84): Create clients table with schema migration
- save_client (line 87-150): Upsert client profile with encrypted PII
- load_client_by_session (line 153-163): Load + decrypt profile
- load_client_by_confirmation (line 166-176): Lookup by confirmation (no PII decrypt)
- get_all_clients_admin (line 179-199): All clients with decrypted PII for admin
- get_due_followups (line 202-232): Query clients needing follow-up by day
- mark_followup_sent (line 235-241): Mark follow-up as sent
- delete_expired_clients (line 244-254): Purge records older than 90 days
- get_stats (line 257-285): Aggregate stats (total, paid, pending, revenue, referral sources)

DB Schema (clients table):
- id, session_id (unique), confirmation, state, status, paid, paid_at
- created_at, updated_at, name_enc (encrypted), email_enc, phone_enc
- referral_source, profile_enc (full encrypted profile blob)
- follow_up_30/60/90_sent, follow_up_30/60/90_date, purge_after
- initials, dispute_count, dispatched_at, watcher_subscribed, watcher_paid_at
- notify_method, notify_handle_enc

---

### 40. bitmoji_credit_app/followup.py
Lines: 248
Purpose: Follow-up letter engine — generates 30/60/90 day escalation letters

Functions/Components:
- generate_followup_letters (line 135-194): Generate follow-up letters for a specific day mark
- check_and_send_followups (line 197-247): Main job — iterates 30/60/90 tiers, generates + emails

Letter Templates:
- 30-day: "Failure to Respond" — cites FCRA 611(a)(1), threatens CFPB/FTC/AG
- 60-day: "Partial Compliance / Inadequate Response" — cites Cushman v. TransUnion, demands MOV
- 90-day: "CFPB and Attorney General Notice" — simultaneous regulatory filings, FCRA 616 damages

---

### 41. bitmoji_credit_app/agents.py
Lines: 615
Purpose: Watcher AI agent pipeline — 3 agents for 30/60/90 day follow-ups with blockchain audit trail

Functions/Components:
- init_ledger (line 42-111): Create pipeline, agent_log, chain tables; genesis block
- enroll_client (line 114-154): Add client to pipeline ledger with blockchain entry
- _write_block (line 157-169): Append block to hash chain (SHA-256 linked)
- log_action (line 172-186): Log agent action with blockchain entry
- verify_chain (line 189-207): Verify entire hash chain integrity
- get_chain (line 210-218): Get chain blocks
- get_pipeline_stats (line 221-235): Aggregate pipeline stats
- get_recent_agent_log (line 238-244): Recent agent activity
- Agent30 (line 278-372): 30-day non-compliance agent
- Agent60 (line 379-463): 60-day escalation agent
- Agent90 (line 470-564): 90-day legal action agent (marks stage=complete)
- run_all_agents (line 571-584): Orchestrator — runs all 3 agents
- enroll_from_db (line 587-614): Scan DB for unenrolled watcher clients

Ledger DB Schema:
- pipeline: session_id, confirmation, client info, stage, day_30/60/90 due/done, letters_generated, notifications_sent
- agent_log: session_id, agent, action, detail, created_at
- chain: block_id, prev_hash, timestamp, session_id, action, data, block_hash (blockchain)

---

### 42. bitmoji_credit_app/click2mail_integration.py
Lines: 531
Purpose: Click2Mail API integration for certified mail dispatch with admin release workflow

Functions/Components:
- generate_dispute_letter_pdf (line 79+): ReportLab PDF generation for dispute letters
- dispatch_certified_mail: Dispatch letters via Click2Mail REST API
- admin_release_manager: Admin release queue management
- click2mail_client: Click2Mail API client

Bureau Addresses:
- Equifax: PO Box 740256, Atlanta, GA 30374
- TransUnion: PO Box 2000, Chester, PA 19016
- Experian: PO Box 4500, Allen, TX 75013

Regulatory Addresses:
- CFPB: 1700 G Street NW, Washington DC 20552
- FTC: 600 Pennsylvania Avenue NW, Washington DC 20580

Dependencies: reportlab, requests

---

### 43. bitmoji_credit_app/credit_report_hook.py
Lines: 380
Purpose: AnnualCreditReport.com integration — credit report parsing workflow

Functions/Components:
- CreditReportParser (line 38+): Parse PDF/CSV/TXT credit reports
  - PATTERNS dict for account_number, creditor_name, balance, status, dates, etc.
  - parse_text: Extract accounts from raw text
  - _split_into_accounts: Section splitting
  - _extract_account_info: Per-account field extraction
  - _classify_disputes: Categorize accounts into dispute types

DisputeCategory Enum: COLLECTIONS, LATE_PAYMENTS, CHARGE_OFFS, INQUIRIES, IDENTITY_FRAUD, MIXED_FILES, OUTDATED_INFO, INCORRECT_ADDRESS, UNAUTHORIZED_ACCOUNTS, PAID_ACCOUNTS, OTHER

---

### 44. bitmoji_credit_app/triple_sage_admin.py
Lines: 314
Purpose: Admin-only AI orchestration layer for template refresh using Grok + Claude + Manus

Functions/Components:
- TripleSageAdmin (line 13+): Admin orchestration class
  - Uses GROK_API_KEY, CLAUDE_API_KEY, MANUS_API_KEY env vars
  - admin_trigger_template_refresh: Refresh letter templates
  - admin_view_activity_log: View audit trail

Issues Found:
- Requires 3 separate AI API keys (Grok, Claude, Manus) — likely not configured in production
- Closed-loop design — no user-facing AI exposure

---

### 45. bitmoji_credit_app/requirements.txt
Lines: 16
Purpose: Python dependency manifest

Dependencies:
- Flask 3.0.0, Flask-CORS 4.0.0, Flask-Session 0.5.0
- stripe 7.4.0, pdfplumber 0.10.3, reportlab 4.0.7
- cryptography 41.0.7, beautifulsoup4 4.12.2
- Pillow >= 10.4.0 (for OCR)
- gunicorn 21.2.0, SQLAlchemy 2.0.23 (not actually used — raw sqlite3)

Issues Found:
- SQLAlchemy is listed but the codebase uses raw sqlite3 — unnecessary dependency
- httpx 0.27.0 listed but only `requests` is used
- Flask-Session 0.5.0 listed but standard Flask sessions are used

---

### 46. bitmoji_credit_app/Procfile
Lines: 1
Purpose: Heroku/Render process type definition

Content: `web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

---

### 47. bitmoji_credit_app/render.yaml
Lines: 39
Purpose: Render deployment config (inner — simpler version)

Config:
- Service: bitmoji-credit-fix, Python web service
- Disk: /data, 1GB for SQLite databases
- Env vars: SECRET_KEY (auto), ADMIN_KEY, Stripe keys, SMTP config

---

## Backend Dispute Engine

### 48. bitmoji_credit_app/dispute_engine/__init__.py
Lines: 8
Purpose: Package docstring — describes v3 engine components

---

### 49. bitmoji_credit_app/dispute_engine/analyst.py
Lines: 436
Purpose: Violation theory matching — maps parsed items to legal theories

Functions/Components:
- _parse_date: Multi-format date parser
- _is_debt_buyer: Check against known debt buyer entity list
- _is_negative: Check for negative status keywords
- _days_until_falloff: Calculate days until FCRA 7-year fall-off

Issues Found:
- This v3 engine appears to be a NEWER rebuild that is NOT integrated into app.py
- app.py uses its own inline parsing engine (lines 225-509)

---

### 50. bitmoji_credit_app/dispute_engine/legal_library.py
Lines: 917
Purpose: Verified statutory and case law reference library with violation theory definitions

Content:
- VIOLATION_THEORIES dict with entries like 'improper_chain_of_ownership'
- Each theory has statutory_anchors, regulatory_anchors, case_law with verified flags
- State law lookup functions

---

### 51. bitmoji_credit_app/dispute_engine/letter_generator.py
Lines: 623
Purpose: v3 comprehensive per-bureau letter composition

Functions/Components:
- _build_section_1_audit: Account audit section
- Bureau addresses for all 3 bureaus
- Organized by violation theory blocks, not by item

Issues Found:
- NOT integrated into app.py — app.py uses its own `generate_letters()` function

---

### 52. bitmoji_credit_app/dispute_engine/parsing_engine.py
Lines: 607
Purpose: v3 credit report parser with normalized data model

Functions/Components:
- empty_consumer_profile, empty_file_metadata, empty_account: Data model factories
- Regex-based field extraction

Issues Found:
- NOT integrated into app.py — app.py uses its own inline parser

---

### 53. bitmoji_credit_app/dispute_engine/pdf_renderer.py
Lines: 169
Purpose: Sanitized PDF renderer for Click2Mail dispatch

Functions/Components:
- _sanitize_text (line 34-40): Scans for branding leaks (AE Labs, BitmojiGuy, etc.)
- render_letter_pdf (line 43+): Generate clean PDF using ReportLab

Dependencies: reportlab

---

## Deploy Config

### 54. render.yaml (root level)
Lines: 45
Purpose: Root-level Render deployment config (comprehensive version)

Config:
- Service name: bitmoji-creditfix-api
- Plan: starter
- Python 3.11.0
- Build: pip install from bitmoji_credit_app/requirements.txt
- Start: cd bitmoji_credit_app && gunicorn
- Disk: /data, 1GB (for creditfix.db and watcher_ledger.db)
- FRONTEND_URL: https://bitmoji-guy5-min-credit-fix.vercel.app
- DB_PATH: /data/creditfix.db
- LEDGER_DB: /data/watcher_ledger.db
- Env vars: SECRET_KEY (auto-generated), ADMIN_KEY, Stripe keys, Click2Mail key, SMTP config

---

## End-to-End Data Flow

### 1. User lands on / → clicks "Begin Your Credit Fix"

```
/ (page.tsx)
  └─ navigateTo('/map') via ShojiDoors animation
     └─ Doors close (1.1s) → router.push('/map') → Doors open (0.3s)
```

The landing page is a cinematic hero with orbiting kanji buttons, seascape.jpg background, price display ($24.99), and two video placeholders. No API calls on this page.

### 2. /map → fills form → clicks Continue

```
/map (step 1 page, aliased as map/page.tsx)
  └─ User fills: firstName, lastName, address, phone, email, state, bureau, disputeReason
  └─ handleSubmit():
     ├─ POST /api/start → Flask creates session, encrypts data, stores in memory + SQLite
     │   Returns: { ok, session_id, name, confirmation }
     │   Flask sets session cookie with submission_id
     └─ navigateTo('/dojo')
```

Note: `bureau` and `disputeReason` are collected but NOT sent to the backend.

### 3. /dojo → uploads files → what API is called → what comes back

```
/dojo (step 2)
  └─ 3 upload slots: Photo ID, Proof of Address, Credit Report
  └─ Each upload calls: POST /api/upload (FormData with file + type)
     Flask:
     ├─ Saves file to temp dir
     ├─ Parses text (PDF via pdfplumber, images via OCR, DOCX via python-docx, HTML via BeautifulSoup)
     ├─ Runs parse_text_for_disputes() → regex matching for 7 dispute categories
     ├─ Runs extract_structured_accounts() → known creditor matching
     ├─ Runs classify_dispute_items() → SOL checking, dispute box assignment
     ├─ Deletes temp file
     └─ Returns: { ok, files_received, parsed_disputes, dispute_items, parsed_accounts }

  └─ ArmorWarrior animates: Helm (ID) → Breastplate (Address) → Sword (Report)
  └─ When all 3 uploaded: "March to the Koi Pond →" button enables
  └─ navigateTo('/koi-pond')
```

### 4. /koi-pond → where do disputes come from → what does review do

```
/koi-pond (step 3)
  └─ useEffect: GET /api/disputes
     Flask returns: { dispute_items: [...] } from session's parsed data
  
  └─ User sees toggleable list of all detected negative items
     Each item shows: dispute type badge, creditor name, account#, amount, date, SOL status
  
  └─ handleContinue():
     POST /api/review with authorized items
     Flask:
     ├─ Stores authorized disputes
     ├─ Sorts by "Gilmore Order" (wrong_addresses first → late_payments last)
     ├─ Generates letters: 1 combined letter per bureau (3 total)
     │   Each letter includes ALL dispute items organized by category
     │   Includes federal + state statutory citations
     │   Includes federal + state case law
     ├─ Generates new confirmation code (AE-YYYYMMDD-XXXXX)
     └─ Returns: { ok, confirmation, dispute_types, letter_count, items }
  
  └─ navigateTo('/garden')
```

### 5. /garden → where do letters come from → can user see them

```
/garden (step 4)
  └─ useEffect: GET /api/letters
     Flask: Returns 403 if not paid → garden falls back to 15 demo placeholders
     Flask: Returns letters array if paid
  
  └─ Rake animation counts up to letter count
  
  └─ Letter grid (3 columns) with "View Letter" buttons
     Each click: GET /api/letters/{index}
     Flask returns: { letter: { bureau, body, client_name, client_address, confirmation, bureau_full_address } }
     Displayed in modal overlay
  
  └─ Users CAN preview letters before payment (if Flask returns them)
     But Flask gates /api/letters behind payment check
     So in practice, users see demo placeholders until paid
  
  └─ navigateTo('/stairway')
```

### 6. /stairway → what payment methods → what happens on success

```
/stairway (step 5)
  └─ Three payment options:
  
  1. STRIPE CARD:
     POST /api/create-checkout
     └─ If no Stripe key: dev_mode=true, auto-marks paid
     └─ If Stripe configured: returns checkout_url → window.location.href redirect
     └─ On Stripe success: redirected to /api/payment-success → marks paid → redirect to /#step-5
  
  2. CASH APP ($AELabsCreditFix):
     POST /api/manual-pay { method: 'cashapp' }
     └─ Status set to 'pending_payment', returns confirmation code
     └─ User must send $24.99 and include confirmation in memo
     └─ Admin manually approves in dashboard
  
  3. CHIME ($AELabsPay):
     Same flow as Cash App
  
  └─ On payment success:
     ├─ wizardStore.setPaid(true)
     ├─ POST /api/admin/queue-for-release (queues for admin review)
     └─ navigateTo('/gate')
```

### 7. /gate → what triggers dispatch → what checks payment

```
/gate (step 6)
  └─ Postage class picker: First Class ($3/letter) or Certified Mail ($8/letter)
  
  └─ handleDispatch():
     POST /api/send-certified { mailClass: 'Certified Mail' | 'First Class' }
     Flask:
     ├─ Checks session + payment status
     ├─ If Click2Mail integration available:
     │   └─ Calls dispatch_certified_mail() → Click2Mail REST API
     │      Requires admin release approval first
     │      Returns: { ok, sent, job_ids, mail_class }
     ├─ If Click2Mail NOT available: returns error
     └─ Frontend: On error, generates local confirmation code (AE-XXXXX)
  
  └─ After confirmation:
     └─ "Continue to The Watcher →" button appears
     └─ navigateTo('/watcher')
```

### 8. /watcher → what tracking data exists → what subscriptions

```
/watcher (step 7)
  └─ useEffect: GET /api/watcher/status
     Flask returns tracking object:
     ├─ dispatched: bool
     ├─ subscribed: bool (watcher_subscribed)
     ├─ days_since_dispatch: number
     ├─ milestones: { day_30, day_60, day_90 } each with { days_remaining, reached, letter_sent }
     ├─ notify_method, notify_handle
     └─ notifications_sent: array of past notifications
  
  └─ If NOT subscribed: SUBSCRIPTION GATE
     Price: $10.99
     Notification preference: Email, Snapchat, TikTok, Instagram
     POST /api/watcher/subscribe { notify_method, notify_handle, payment_method }
     └─ If Stripe: creates checkout session → redirect
     └─ If manual/dev: activates immediately, enrolls in agent pipeline
  
  └─ If subscribed: ACTIVE TRACKING
     3 milestone cards (30/60/90 day) with:
     ├─ Countdown progress bars
     ├─ FCRA statute citations
     ├─ "Download Letter" buttons → GET /api/followup-letters/{day}
     └─ Notification history log
  
  └─ PARTNER OFFERS section:
     5 credit card offers (Chime, Cleo, Amex Platinum, Cap One Secured, Cap One Quicksilver)
     Each with promo code and external "Apply Now" link
```

---

## Deployment Status

### GitHub Repository
- Not a git repo at `C:/Users/sgill/BitmojiGuy5MinCreditFix` (no .git directory detected)
- May be deployed from a different location or via direct upload

### Vercel (Frontend)
- Project URL: https://bitmoji-guy5-min-credit-fix.vercel.app (per render.yaml FRONTEND_URL)
- Framework: Next.js 16.2.3
- Build: `npm run build`
- vercel.json configured with security headers
- Environment variables needed:
  - `NEXT_PUBLIC_FLASK_URL` — Flask backend URL (defaults to http://localhost:5000)
  - `NEXT_PUBLIC_ADMIN_KEY` — Admin key (SECURITY RISK: exposed to client)

### Render (Backend)
- Service name: bitmoji-creditfix-api (per root render.yaml)
- Alternate service name: bitmoji-credit-fix (per inner render.yaml)
- Plan: starter
- Runtime: Python 3.11.0 + gunicorn
- Persistent disk: /data (1GB) for creditfix.db + watcher_ledger.db
- Environment variables configured:
  - `SECRET_KEY` — auto-generated by Render
  - `ADMIN_KEY` — manual sync
  - `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_WEBHOOK_SECRET` — manual sync
  - `CLICK2MAIL_API_KEY` — manual sync
  - `FRONTEND_URL` — https://bitmoji-guy5-min-credit-fix.vercel.app
  - `DB_PATH` — /data/creditfix.db
  - `LEDGER_DB` — /data/watcher_ledger.db
  - `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `FROM_EMAIL` — manual sync

### CORS Configuration
- Flask CORS (app.py line 86-89):
  ```python
  CORS(app, supports_credentials=True, origins=[
      'http://localhost:3000', 'http://localhost:3001',
      os.environ.get('FRONTEND_URL', 'http://localhost:3000'),
  ])
  ```
- Only allows localhost:3000, localhost:3001, and the configured FRONTEND_URL
- credentials: include (session cookies cross-origin)

### Critical Deployment Issues

1. **ADMIN_KEY EXPOSED IN CLIENT BUNDLE**: `frontend/components/admin/ReleaseQueue.tsx` line 8 exposes `NEXT_PUBLIC_ADMIN_KEY` (default: `ae-admin-2025`) to the browser. Anyone can view source and get the admin key.

2. **TWO RENDER CONFIGS**: Root `render.yaml` and `bitmoji_credit_app/render.yaml` have different service names and slightly different configs. Only one should be used.

3. **PRICE INCONSISTENCY**: CLAUDE.md says $19.99, app.py uses $24.99 (PRICE_CENTS = 2499), all frontend pages show $24.99.

4. **LETTER COUNT MISMATCH**: UI text references "15 letters" in multiple places (garden, stairway), but `generate_letters()` now produces 1 combined letter per bureau = 3 total letters.

5. **STEP NUMBERING CONFUSION**: Landing page implies "5 Clicks, 5 Minutes" but internal navigation shows "Step X of 7". Legacy step/1-5 routes exist alongside scene-based routes.

6. **UNUSED DEPENDENCIES**: Three.js, R3F, @react-three/drei installed but not used. SQLAlchemy in requirements.txt but raw sqlite3 used. httpx installed but not used.

7. **DISPUTE ENGINE v3 NOT INTEGRATED**: The `dispute_engine/` package (analyst.py, legal_library.py, letter_generator.py, parsing_engine.py, pdf_renderer.py) is a more sophisticated rebuild that is NOT wired into app.py. The app still uses its inline parsing engine.

8. **ADMIN API GAP**: `frontend/lib/adminApi.ts` references `/op-console/api/*` endpoints that don't exist in the Flask backend.

9. **FAKE CONFIRMATION ON ERROR**: Gate page generates fake confirmation codes when Flask is unreachable (line 39), making users think dispatch succeeded.

10. **SESSION-BASED ENCRYPTION FRAGILITY**: Data is encrypted with session_id + client_IP + timestamp. If the user's IP changes (mobile network switch, VPN), they lose access to their encrypted data.
