# BitmojiGuy 5-Min Credit Tool — AE.CC.001
## Sean Gilmore | Arden Edge Capital

---

## Product Philosophy (Inviolable)

The tool helps consumers exercise rights they actually have, on items where they actually have specific grounds, in language that honestly reflects their situation. Every feature must serve this principle. Features that pull away from this principle are wrong features regardless of how they perform on other metrics.

The tool does NOT operate as a traditional credit repair organization. It does not dispute negative items as a category. It does not generate letters for items the consumer has not affirmed specific grounds for. It does not produce template boilerplate that overstates what the consumer knows.

## Architectural Commitments (Locked)

The intake → assertion → letter pipeline is the spine of this product:
- Consumer affirms specific grounds for specific items in intake
- Tool generates letters only for items with affirmed grounds
- Letter content cites only what the consumer has affirmed
- No letter contains assertions the consumer did not enter

**Selective disputing rule:** Items without consumer-affirmed grounds receive no letters. There is no "dispute all" path, no bulk dispute shortcut, and no bypass mechanism. This is a constraint, not a feature.

**Recipient routing rule:** Bureau-appropriate grounds go to bureau letters under FCRA framework. Collector-appropriate grounds (validation, chain of title, license to collect) go to separate collector letters under FDCPA framework. These do not get mixed into single letters.

**Letter structure rule:** Letters follow math-first composition. Audit data and specific factual claims lead. Statutory grounding closes. The order is the strategy and is not interchangeable.

**Honest position rule:** Every claim in a letter must be sourceable to a fact the consumer affirmed in intake. The tool never asserts fraud unless the consumer affirmed certainty of fraud. The tool never asserts a balance is wrong unless the consumer provided basis. The tool says "I cannot verify" rather than "this is inaccurate" when the consumer's epistemic state is uncertainty.

## Forbidden Patterns

Do not implement features that:
- Generate letters for items without consumer-affirmed grounds
- Bulk-dispute or shortcut the per-item intake
- Add statute citations not tied to specific affirmed grounds
- Produce letter language asserting facts the consumer did not enter
- Mix bureau-recipient and collector-recipient grounds in single letters
- Stack multiple statutory framings of the same factual claim against the same recipient
- Brand letters with internal tool identifiers, customer numbers, or generator strings
- Embed metadata that identifies the tool in delivered documents

Do not modify the data model that flows through the intake → assertion → letter pipeline without explicit approval surfaced to the project owner.

## Escalation Rule

If a feature request would require changing locked architecture or violating the philosophical commitments, stop and surface the conflict. State plainly: "This request conflicts with locked architecture in section X. Here is why. Here is what we could do that does not conflict." Do not work around the conflict silently. Do not partially implement features that compromise the spine.

## Session Discipline

Each work session focuses on one feature or one issue. Do not let session scope expand into "while we're here let me also..." territory. Architectural questions are not re-litigated in feature sessions; they are surfaced and deferred to architecture sessions.

---

## Tech Stack

| Layer    | Tech        | Port | Entry Point                   |
|----------|-------------|------|-------------------------------|
| Backend  | Flask       | 5000 | `bitmoji_credit_app/app.py`   |
| Frontend | Next.js     | 3000 | `frontend/app/` directory     |

### Backend — `bitmoji_credit_app/app.py`
- Flask REST API serving JSON to the Next.js frontend
- Handles: intake, document uploads, credit report parsing, dispute letter generation, payment processing, certified mail dispatch, follow-up scheduling
- Credit report parsing: pdfplumber (PDF), BeautifulSoup (HTML), python-docx (DOCX), pytesseract (OCR)
- Encryption: Fernet (AES-128-CBC + HMAC-SHA256) with SHA-256 key derivation
- Payment: Stripe Checkout (card) + Cash App + Chime manual pay
- Database: SQLite (encrypted fields)

### Frontend — Next.js (Port 3000)
- 8 screens with Shoji door transitions
- Zustand state management
- Gold `#C9A84C`, fonts Cinzel Decorative + Rajdhani
- `seascape.jpg` landing background

## 8 Screens / Routes

1. `/` — Landing (Lone Cypress Seascape)
2. `/map` — Intake Form (Map Room)
3. `/dojo` — Upload Documents (Samurai Armor Ceremony)
4. `/koi-pond` — Authorize Disputes (Koi Pond)
5. `/garden` — Generate Letters (Sand Garden)
6. `/stairway` — Payment ($24.99)
7. `/gate` — Certified Mail Dispatch (Dragon's Gate)
8. `/watcher` — 30/60/90 Day Tracker ($10.99 subscription)

## Design System

| Role          | Value       |
|---------------|-------------|
| Primary Gold  | `#C9A84C`   |
| Neon Glow     | `text-shadow: 0 0 8px currentColor, 0 0 20px currentColor` |
| Font Display  | Cinzel Decorative |
| Font Body     | Rajdhani |
| Navigation    | ShojiDoors.tsx sliding panel transitions |

## Key Components

- `ArmorWarrior.tsx` — Samurai armor ceremony on /dojo
- `ShojiDoors.tsx` — Global route transition animations
- `TopNav.tsx` — Step navigation (future steps disabled)
- `WizardSidebar.tsx` — Mr Beeks mascot + step nav
- `SceneLayout.tsx` — Cinematic background system
