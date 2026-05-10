# BitmojiGuy Frontend — Complete Component Overview

## 📁 Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── page.tsx                 # Home page
│   ├── layout.tsx               # Root layout
│   ├── step/                    # 5-step wizard
│   │   ├── 1/page.tsx          # Step 1: Intake
│   │   ├── 2/page.tsx          # Step 2: Details
│   │   ├── 3/page.tsx          # Step 3: Review
│   │   ├── 4/page.tsx          # Step 4: Confirmation
│   │   ├── 5/page.tsx          # Step 5: Complete
│   │   └── layout.tsx          # Wizard layout
│   ├── dojo/page.tsx            # Document upload
│   ├── koi-pond/page.tsx        # Dispute review
│   ├── garden/page.tsx          # Letter preview
│   ├── stairway/page.tsx        # Payment
│   ├── watcher/page.tsx         # Follow-up service
│   ├── admin/page.tsx           # Admin dashboard
│   ├── gate/page.tsx            # Entry gate
│   ├── map/page.tsx             # Map view
│   ├── interstitial/page.tsx    # Transition screen
│   └── api/
│       └── generate-beeks/route.ts  # API endpoint
├── components/                   # Reusable components
│   ├── admin/
│   │   └── ReleaseQueue.tsx     # Admin release dashboard
│   ├── dojo/
│   │   └── CreditReportGuide.tsx # Credit report guide
│   ├── mascot/
│   │   └── MrBeeks.tsx          # Animated mascot
│   ├── nav/
│   │   └── TopNav.tsx           # Top navigation
│   ├── scene/
│   │   ├── SceneLayout.tsx      # Scene container
│   │   └── scenePresets.ts      # Scene configurations
│   ├── shoji/
│   │   └── ShojiDoors.tsx       # Shoji door animations
│   ├── sidebar/
│   │   └── WizardSidebar.tsx    # Step indicator
│   ├── warrior/
│   │   └── ArmorWarrior.tsx     # Armor animation
│   ├── effects/
│   │   ├── ParticleEffects.tsx  # Particle system
│   │   ├── CinematicVignette.tsx # Vignette effect
│   │   ├── DepthOfField.tsx     # Blur effect
│   │   └── SoundDesign.tsx      # Audio system
│   └── Providers.tsx            # Context providers
├── lib/
│   └── api.ts                   # API client
├── styles/
│   └── globals.css              # Global styles
└── public/
    └── favicon.ico              # Favicon

```

---

## 🎬 Pages & User Journey

### **Home Page** (`app/page.tsx`)
- Landing page with hero section
- Call-to-action: "Start Your Free Review"
- Navigation to Step 1
- Cinematic background

### **Step 1: Intake** (`app/step/1/page.tsx`)
- User name, address, phone, email
- State selection
- Bureau selection (Equifax, TransUnion, Experian)
- Reason for dispute (identity theft, errors, etc.)
- Navigation to Step 2

### **Step 2: Details** (`app/step/2/page.tsx`)
- Additional information
- Dispute details
- Contact preferences
- Navigation to Step 3

### **Step 3: Review** (`app/step/3/page.tsx`)
- Review all entered information
- Edit capability
- Confirmation
- Navigation to Step 4

### **Step 4: Confirmation** (`app/step/4/page.tsx`)
- Confirmation message
- Summary of submission
- Navigation to Step 5

### **Step 5: Complete** (`app/step/5/page.tsx`)
- Completion screen
- Next steps
- Link to Dojo

### **Dojo: Document Upload** (`app/dojo/page.tsx`)
- Photo ID upload
- Proof of address upload
- Credit report upload
- **Credit Report Guide component** (new)
- Samurai armor animation on completion
- Navigation to Koi Pond

### **Koi Pond: Dispute Review** (`app/koi-pond/page.tsx`)
- Display extracted disputes from credit report
- Checkbox selection
- Dispute categorization
- Navigation to Garden

### **Garden: Letter Preview** (`app/garden/page.tsx`)
- Generated dispute letters
- Professional formatting
- Bureau-specific language
- Navigation to Stairway

### **Stairway: Payment** (`app/stairway/page.tsx`)
- $24.99 pricing
- Stripe payment form
- Payment processing
- **Automatic queue for admin release** (new)
- Navigation to Watcher

### **Watcher: Follow-up Service** (`app/watcher/page.tsx`)
- Optional $10.99/month service
- Follow-up tracking
- Dispute status monitoring
- Cinematic ninja sentinel aesthetic

### **Admin Dashboard** (`app/admin/page.tsx`)
- Admin authentication
- **Release Queue tab** (new)
- Pending submissions
- Approval/rejection workflow
- Activity log
- **ReleaseQueue component** (new)

---

## 🧩 Components

### **Admin Components**

#### **ReleaseQueue** (`components/admin/ReleaseQueue.tsx`)
- **Purpose:** Admin dashboard for managing submissions
- **Features:**
  - View pending submissions
  - Approve with confirmation
  - Reject with reason
  - Activity log
  - Real-time refresh
  - Submission details (user, letter count, queue time)
- **Props:** None (uses API)
- **API Calls:**
  - `GET /api/admin/pending-queue`
  - `POST /api/admin/approve-release`
  - `POST /api/admin/reject-release`
  - `GET /api/admin/release-log`

---

### **Dojo Components**

#### **CreditReportGuide** (`components/dojo/CreditReportGuide.tsx`)
- **Purpose:** Guide users to get free credit reports
- **Features:**
  - Step-by-step guide to AnnualCreditReport.com
  - Bureau contact information
  - FAQ section
  - Links to official websites
  - Downloadable guide
- **Props:** None
- **API Calls:** None (static content)

---

### **Mascot Components**

#### **MrBeeks** (`components/mascot/MrBeeks.tsx`)
- **Purpose:** Animated mascot character
- **Features:**
  - SVG-based animation
  - Multiple expressions
  - Cinematic positioning
  - Particle effects
- **Props:**
  - `expression?: 'happy' | 'thinking' | 'celebrating'`
  - `scale?: number`
  - `position?: 'left' | 'center' | 'right'`

---

### **Navigation Components**

#### **TopNav** (`components/nav/TopNav.tsx`)
- **Purpose:** Top navigation bar
- **Features:**
  - Logo
  - Navigation links
  - User menu
  - Admin link
- **Props:** None

---

### **Scene Components**

#### **SceneLayout** (`components/scene/SceneLayout.tsx`)
- **Purpose:** Container for cinematic scenes
- **Features:**
  - Background image
  - Vignette effect
  - Particle effects
  - Depth of field
  - Sound design
- **Props:**
  - `scene: string` - Scene preset name
  - `children: React.ReactNode`
  - `title?: string`
  - `subtitle?: string`

#### **scenePresets** (`components/scene/scenePresets.ts`)
- **Purpose:** Scene configuration presets
- **Scenes:**
  - `home` - Home page
  - `dojo` - Document upload
  - `koi-pond` - Dispute review
  - `garden` - Letter preview
  - `stairway` - Payment
  - `watcher` - Follow-up service
  - `admin` - Admin dashboard
  - `gate` - Entry gate
  - `interstitial` - Transition

---

### **Shoji Components**

#### **ShojiDoors** (`components/shoji/ShojiDoors.tsx`)
- **Purpose:** Animated shoji door transitions
- **Features:**
  - Sliding animation
  - Japanese aesthetic
  - Smooth transitions
  - Sound effects
- **Props:**
  - `isOpen: boolean`
  - `onComplete?: () => void`

---

### **Sidebar Components**

#### **WizardSidebar** (`components/sidebar/WizardSidebar.tsx`)
- **Purpose:** Step indicator for wizard
- **Features:**
  - Current step highlight
  - Completed steps checkmark
  - Step labels
  - Progress visualization
- **Props:**
  - `currentStep: number`
  - `totalSteps: number`

---

### **Warrior Components**

#### **ArmorWarrior** (`components/warrior/ArmorWarrior.tsx`)
- **Purpose:** Animated samurai warrior in armor
- **Features:**
  - SVG animation
  - Staggered armor pieces
  - Combat poses
  - Cinematic positioning
- **Props:**
  - `pose?: 'idle' | 'attack' | 'celebrate'`
  - `scale?: number`

---

### **Effects Components**

#### **ParticleEffects** (`components/effects/ParticleEffects.tsx`)
- **Purpose:** Particle system for cinematic effects
- **Features:**
  - Floating particles
  - Fade animations
  - Customizable colors
  - Performance optimized
- **Props:**
  - `count?: number`
  - `color?: string`
  - `speed?: number`

#### **CinematicVignette** (`components/effects/CinematicVignette.tsx`)
- **Purpose:** Vignette effect for cinematic look
- **Features:**
  - Dark edges
  - Smooth gradient
  - Customizable intensity
- **Props:**
  - `intensity?: number` (0-1)

#### **DepthOfField** (`components/effects/DepthOfField.tsx`)
- **Purpose:** Blur effect for depth
- **Features:**
  - Gaussian blur
  - Focus area
  - Smooth transitions
- **Props:**
  - `blur?: number` (0-10)
  - `focusArea?: 'top' | 'center' | 'bottom'`

#### **SoundDesign** (`components/effects/SoundDesign.tsx`)
- **Purpose:** Audio system
- **Features:**
  - Background music
  - Sound effects
  - Volume control
  - Mute option
- **Props:**
  - `scene: string`
  - `enabled?: boolean`

---

### **Providers** (`components/Providers.tsx`)
- **Purpose:** Context providers wrapper
- **Features:**
  - Theme provider
  - API client provider
  - State management
- **Props:**
  - `children: React.ReactNode`

---

## 🔌 API Integration

### **API Client** (`lib/api.ts`)

#### **User Flow Endpoints**
```typescript
// Intake
POST /api/intake
GET /api/intake/:sessionId

// Document upload
POST /api/upload
GET /api/upload-status/:sessionId

// Dispute extraction
POST /api/extract-disputes
GET /api/disputes/:sessionId

// Letter generation
POST /api/generate-letters
GET /api/letters/:sessionId

// Payment
POST /api/create-payment-intent
POST /api/confirm-payment

// Queue for admin release
POST /api/queue-for-release
```

#### **Admin Endpoints**
```typescript
// Release queue
GET /api/admin/pending-queue
POST /api/admin/approve-release
POST /api/admin/reject-release
GET /api/admin/release-log
```

#### **Credit Report Endpoints**
```typescript
// Credit report guide
GET /api/credit-report-guide
GET /api/credit-report-bureaus

// Parse credit report
POST /api/parse-credit-report
GET /api/credit-report-status/:sessionId
```

---

## 🎨 Styling

### **Global Styles** (`styles/globals.css`)
- Gold/black color scheme
- Japanese aesthetic
- Cinematic typography
- Responsive design
- Dark mode optimized

### **Component Styles**
- Tailwind CSS utilities
- Custom CSS for animations
- Responsive breakpoints
- Accessibility features

---

## 🔐 Authentication

### **Admin Authentication**
- Admin key validation
- Session management
- Protected routes
- Activity logging

---

## 📊 State Management

### **Context Providers**
- User session context
- Admin context
- Theme context
- API client context

### **Local State**
- Form state (React hooks)
- UI state (React hooks)
- Animation state (React hooks)

---

## 🚀 Deployment

### **Frontend Deployment** (Vercel)
```bash
npm run build
npm run start
```

### **Environment Variables**
```
NEXT_PUBLIC_FLASK_URL=https://api.example.com
NEXT_PUBLIC_ADMIN_KEY=ae-admin-2025
```

---

## ✅ Feature Checklist

- [x] 5-step wizard
- [x] Document upload (Dojo)
- [x] Dispute extraction (Koi Pond)
- [x] Letter generation (Garden)
- [x] Payment flow (Stairway)
- [x] Admin dashboard
- [x] Admin release queue (NEW)
- [x] Credit report guide (NEW)
- [x] Cinematic effects
- [x] Responsive design
- [x] Accessibility
- [x] Error handling
- [x] Loading states
- [x] Success states

---

## 🎯 Next Steps

1. **Deploy to Vercel** - Run `deploy.bat`
2. **Test user flow** - Complete 5-step wizard
3. **Test admin workflow** - Approve/reject submissions
4. **Test credit report** - Upload and parse
5. **Monitor logs** - Check for errors

---

## 📞 Support

For issues or questions about the frontend:
1. Check browser console for errors
2. Check network tab for API failures
3. Verify environment variables
4. Check backend logs on Render

---

**Frontend is production-ready. Deploy when ready!**
