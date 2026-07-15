# Letter Generator Upgrade — Design Spec

**Date:** 2026-05-01
**Author:** Sean Gilmore / Claude
**Project:** BitmojiGuy 5 Min Credit Tool (AE.CC.001)

---

## Overview

Six workstreams to upgrade the v3 dispute engine letter generator:

1. **State Law Integration** — Wire all 50 states + DC into the v3 letter generator
2. **Full Legal Precedent** — Fill federal case law gaps across all 7 violation theories
3. **PDF Output Upgrade** — Professional formatting in `pdf_renderer.py`
4. **Grammarly SDK** — Frontend grammar checking on `/garden` letter preview
5. **Landing Page CTA Overhaul** — Two-state acknowledge button + black text fixes
6. **Grok Intelligence Panel** — Admin-only xAI/Grok chat for research and maintenance

---

## Workstream 1: State Law Integration

### Problem

The v3 `legal_library.py` only has 4 states (TX/CA/NY/MA). The v1 `api/state_laws.py` has all 50 + DC with SOL, consumer protection acts, and state case law. The v3 `letter_generator.py` does not produce any state law section in letters.

### Solution

**File: `dispute_engine/legal_library.py`**

Expand `STATE_LAW_AUTHORITIES` from 4 entries to 51 (50 states + DC). Each entry:

```python
'TX': {
    'name': 'Texas',
    'sol_written': 4,
    'sol_oral': 4,
    'sol_open': 4,
    'sol_statute': 'Tex. Civ. Prac. & Rem. Code § 16.004',
    'consumer_protection': 'Texas Deceptive Trade Practices Act (Tex. Bus. & Com. Code § 17.41 et seq.)',
    'debt_collection': 'Texas Debt Collection Act (Tex. Fin. Code Ch. 392)',
    'additional': 'Tex. Fin. Code § 392.304 — prohibits misrepresenting a debt.',
    'state_case_law': {
        'collections': 'Cushman and Tex. Fin. Code 392.304 — Texas Debt Collection Act prohibits misrepresenting a debt.',
        'aged_debt': 'Texas SOL for written contracts is 4 years (Tex. Civ. Prac. & Rem. Code 16.004).',
        'default': 'Texas DTPA (Tex. Bus. & Com. Code 17.41 et seq.) provides treble damages for knowing violations.',
    },
    'verified': True,
    'verified_date': '2026-05-01',
}
```

Data source: merge from `api/state_laws.py` `STATE_LAWS` + `STATE_CASE_LAW` dicts.

**File: `dispute_engine/letter_generator.py`**

Add `_build_section_8_state_law(analyst_report, state_code)`:

- Only appears when `state_code` is provided and found in library
- Outputs: state name, SOL (written/oral/open), SOL statute, consumer protection act, debt collection act, additional notes, state-specific case precedent
- Wire into `generate_bureau_letter()` between Section 7 (Disclaimers) and closing

Also update `_build_section_4_theory_blocks()`:
- When state law has theory-specific case law (e.g., TX collections), append it to that theory's "Judicial Interpretation" sub-section under a "State Precedent:" label

---

## Workstream 2: Full Legal Precedent Coverage

### Problem

Several violation theories in `legal_library.py` have empty `federal_case_law` lists. The v1 `api/state_laws.py` has cases that should be in v3.

### Changes to `legal_library.py`

| Theory | Adding |
|--------|--------|
| `re_aging` | Grigoryan v. Experian, 84 F. Supp. 3d 1044 (C.D. Cal. 2014); Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002) |
| `obsolescence` | Grigoryan v. Experian, 84 F. Supp. 3d 1044 (C.D. Cal. 2014) |
| `validation_failure` | Gorman v. Wolpoff & Abramson, 584 F.3d 1147 (9th Cir. 2009); Dennis v. BEH-1, LLC, 520 F.3d 1066 (9th Cir. 2008) |
| `duplicate_inconsistent` | Cortez v. Trans Union LLC, 617 F.3d 688 (3d Cir. 2010) |
| `identity_theft` | Nelson v. Chase Manhattan Mortgage, 282 F.3d 1057 (9th Cir. 2002) |
| `improper_chain` | Gorman v. Wolpoff & Abramson, 584 F.3d 1147 (9th Cir. 2009) |

All entries follow existing format with `citation`, `court`, `year`, `holding`, `verified: True`, `verified_date`.

Also add missing regulatory anchors:
- `validation_failure`: Add 12 C.F.R. § 1006.34 (already present, verify)
- `re_aging`: Add 12 C.F.R. § 1022.41(a) (Regulation V definition of DOFD)

Also add late payment theory (from v1 templates but missing from v3):

```python
'late_payment_inaccuracy': {
    'id': 'late_payment_inaccuracy',
    'title': 'Inaccurate Late Payment Reporting',
    'description': '...',
    'statutory_anchors': [FCRA 623(a)(1)(A), FCRA 611(a), FCRA 623(a)(1)(F) CARES Act],
    'federal_case_law': [
        Seamans v. Temple Univ. (3d Cir. 2014),
        Saunders v. Branch Banking & Trust (4th Cir. 2008),
    ],
}
```

And MOV demand theory:

```python
'method_of_verification': {
    'id': 'method_of_verification',
    'title': 'Method of Verification Demand',
    'description': '...',
    'statutory_anchors': [FCRA 611(a)(6)(B)(iii), FCRA 616, FCRA 617],
    'federal_case_law': [
        Dennis v. BEH-1, LLC (9th Cir. 2008),
        Cushman v. Trans Union Corp. (3d Cir. 1997),
        Johnson v. MBNA (4th Cir. 2004),
    ],
}
```

---

## Workstream 3: PDF Output Upgrade

### Problem

Current `pdf_renderer.py` is functional but basic — no visual hierarchy, no page numbers, no proper letterhead layout.

### Changes to `dispute_engine/pdf_renderer.py`

**Letterhead layout:**
- Consumer name + address: top-left, 11pt Times-Roman
- Date: top-right aligned, 11pt
- Bureau name + address: below consumer block, left-aligned
- Re: line bold, 11pt
- Horizontal rule after header

**Section formatting:**
- Section headers (SECTION 1, SECTION 2...): 12pt Times-Bold, followed by 0.5pt horizontal rule
- Sub-headers (4.A, 4.B...): 11pt Times-Bold, 12pt space before
- Body text: 11pt Times-Roman, 15pt leading
- Bullet items: 10pt, left-indent 36pt, hanging indent
- Case citations: italic for case name portion (e.g., *Cushman v. Trans Union Corp.*, 115 F.3d 220)

**Page numbers:**
- Bottom center: "Page X of Y" in 9pt Times-Roman
- Use `onLaterPages` callback for page numbering

**State law section:**
- Same formatting as other sections
- State name in header: "SECTION 8 — STATE LAW AUTHORITY (TEXAS)"

**Sanitization:**
- Keep existing branding pattern scan
- Ensure no metadata leaks (Author, Producer, Creator fields blank)

---

## Workstream 4: Grammarly Text Editor SDK

### Problem

No grammar/spell checking on generated letters before consumer finalizes.

### Solution

**File: `frontend/app/garden/page.tsx`** (or equivalent letter preview component)

Add Grammarly Text Editor SDK:

```tsx
<script src="https://js.grammarly.com/grammarly-editor-plugin/v1/index.js" />

<grammarly-editor-plugin clientId={process.env.NEXT_PUBLIC_GRAMMARLY_CLIENT_ID}>
  <textarea value={letterBody} readOnly={false} />
</grammarly-editor-plugin>
```

**Environment variable:**
- `NEXT_PUBLIC_GRAMMARLY_CLIENT_ID` — set in `.env.local`
- User registers at developer.grammarly.com to get Client ID

**Graceful fallback:**
- If env var is not set, render plain textarea without Grammarly wrapper
- No errors, no broken UI

---

## Workstream 5: Landing Page CTA Overhaul

### Problem

Current CTA button navigates directly to `/map`. Need two-state acknowledge flow with legal disclosures.

### Changes to `frontend/app/page.tsx`

**Only the CTA button section changes. Everything else on the page is untouched.**

**STATE 1 — Default:**
- Button text: "Begin Your Credit Fix — $24.99"
- Same existing gold gradient styling
- On click: sets `showAcknowledge = true`, does NOT navigate
- Acknowledge box appears below button

**Acknowledge box:**
- Background: `#C9A84C`
- Padding: `1.25rem`
- Border-radius: `8px`
- Border: `2px solid #000000`

**Acknowledgement text** (Cinzel Decorative, bold, #000000, text-shadow: 0 0 8px #000000 0 0 16px #000000, 13px):

> By proceeding I confirm:
> - I am the consumer named in these disputes, 18+, US resident
> - This is a technology tool — not a law firm or credit repair service
> - I direct all actions. No legal advice is provided.
> - $24.99 covers letter generation only. Postage is separate (~$20-40)
> - Results are not guaranteed

**Small print below** (Rajdhani, 9px, rgba(0,0,0,0.55), max-width 480px, centered, line-height 1.6, max-height 80px, overflow-y auto):

> BitmojiGuy 5 Min CreditFix is a financial technology tool operated by Arden Edge Capital (AE.CC.001). Not a credit repair organization, law firm, credit counseling service, or debt settlement company. No attorney-client relationship is created. No legal advice is provided. Consumer directs all actions. Letters authored by consumer under rights arising from: Fair Credit Reporting Act (15 U.S.C. § 1681 et seq.) | Fair Debt Collection Practices Act (15 U.S.C. § 1692 et seq.) | Equal Credit Opportunity Act (15 U.S.C. § 1691 et seq.) | Consumer Financial Protection Act (12 U.S.C. § 5481 et seq.) | Applicable state consumer protection law. Exempt from Credit Repair Organizations Act (15 U.S.C. § 1679) — no advance fees collected for credit repair services, no representations of credit improvement made, consumer directs all actions. Exempt from Texas Credit Services Organization Act (Tex. Fin. Code § 393) on same basis. Data processed in closed-loop session — not retained, transmitted, or sold to third parties. Results not guaranteed. Bureaus are legally required to investigate disputes but not required to remove accurate information. For free federal dispute resources visit consumerfinance.gov. Governing law: State of Texas. Disputes resolved by binding arbitration. (c) 2026 Arden Edge Capital | AE.CC.001 | ardanedgecapital.com

**STATE 2 — After acknowledge box appears:**
- Button text changes to: "I Acknowledge — Proceed to Credit Fix"
- Same gold styling
- THIS click navigates to `/map`

**Additional text color changes:**
- h1 "BitmojiGuy 5 Min Credit Tool": `color: '#000000'` (was `#F0D080`), remove gold text-shadow
- "Admin Dashboard" button: `color: '#000000'` (was `#8A8278`), hover stays gold

---

## Workstream 6: Grok Intelligence Panel (Admin-Only)

### Problem

Admin needs an AI research tool for weekly tasks: answering client questions, updating letter templates, researching new case law, and general credit dispute intelligence. This is admin-only — never client-facing. The client-facing app is a closed-loop system.

### Solution

**Backend: `bitmoji_credit_app/api/grok.py`** (new file)

Flask endpoint `/admin/api/grok` that proxies requests to the xAI API:

```python
@app.route('/admin/api/grok', methods=['POST'])
def grok_query():
    # Requires admin auth
    prompt = request.json.get('prompt', '')
    # Call xAI API with system prompt pre-loaded with legal library context
    response = requests.post('https://api.x.ai/v1/responses', ...)
    return jsonify({'response': response_text})
```

System prompt includes:
- Product philosophy from CLAUDE.md (not a credit repair org, consumer-directed)
- All violation theory definitions from `legal_library.py`
- State law summary data
- Escalation paths
- Instruction: "You are an admin research assistant for a consumer credit dispute tool. Help the admin research case law, draft letter improvements, and answer client questions. Never produce content that would go directly to consumers — all output is for admin review only."

**Environment variable:**
- `XAI_API_KEY` — stored in `.env` (server-side only, never exposed to frontend)
- Model: `grok-4.20-reasoning`

**Frontend: `frontend/app/admin/page.tsx`**

Add a 4th tab `'intelligence'` to the existing tab bar (alongside cases, pipeline, notifications):

```tsx
{activeTab === 'intelligence' && (
  <div>
    <h2>Grok Intelligence</h2>
    <textarea value={grokPrompt} onChange={...} placeholder="Ask Grok..." />
    <button onClick={sendToGrok}>Query</button>
    <div>{grokResponse}</div>
  </div>
)}
```

UI specs:
- Same dark theme as rest of admin (background `#050403`, gold accents)
- Input: multi-line textarea, same styling as other admin inputs
- Send button: gold gradient, same as other admin action buttons
- Response: rendered in a scrollable container with monospace font for code/citations, body font for prose
- Loading state: "Thinking..." with gold pulse animation
- Response history: keep last 10 queries in local state (not persisted — admin's weekly research is ephemeral)

### What Grok does NOT do

- Never appears in consumer-facing pages
- Never generates letters directly (admin reviews and manually updates templates)
- Never accesses consumer PII (queries are about law/strategy, not individual cases)
- API key never exposed to frontend (proxied through Flask)

---

## Files Modified

| File | Workstream | Change |
|------|-----------|--------|
| `dispute_engine/legal_library.py` | 1, 2 | Expand to 50 states + DC, fill case law gaps, add late_payment + MOV theories |
| `dispute_engine/letter_generator.py` | 1 | Add `_build_section_8_state_law()`, wire state precedent into Section 4 |
| `dispute_engine/pdf_renderer.py` | 3 | Professional formatting, page numbers, letterhead, citation styling |
| `frontend/app/garden/page.tsx` | 4 | Grammarly SDK integration |
| `frontend/app/page.tsx` | 5 | Two-state CTA button, acknowledge box, black text fixes |
| `frontend/app/admin/page.tsx` | 6 | Add "Intelligence" tab with Grok chat interface |
| `bitmoji_credit_app/api/grok.py` | 6 | New Flask endpoint proxying to xAI API |
| `bitmoji_credit_app/app.py` | 6 | Register grok blueprint/route |
| `.env.local` | 4 | `NEXT_PUBLIC_GRAMMARLY_CLIENT_ID` |
| `.env` | 6 | `XAI_API_KEY` (server-side only) |

## Files NOT Modified

- `parsing_engine.py` — untouched
- `analyst.py` — untouched (already imports from legal_library)
- `app.py` — untouched
- All other pages — untouched
- ShojiDoors.tsx, ArmorWarrior.tsx — untouched

---

## Constraints

- No CLAUDE.md violations: letters still require consumer affirmation per item
- No branding in letter output (sanitization check stays)
- State law section omitted if consumer state unknown
- Grammarly degrades gracefully if no client ID
- Landing page: ONLY CTA button + text colors change, everything else untouched
- Grok panel: admin-only, never client-facing, API key server-side only
- Grok does not access consumer PII or generate letters directly
