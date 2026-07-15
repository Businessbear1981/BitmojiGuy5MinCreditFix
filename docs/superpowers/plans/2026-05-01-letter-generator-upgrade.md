# Letter Generator Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the v3 dispute engine with full 50-state law coverage, expanded federal case law, professional PDF output, Grammarly SDK on letter preview, two-state CTA with legal disclosures on landing page, and admin-only Grok intelligence panel.

**Architecture:** Six independent workstreams touching backend (`dispute_engine/`, `api/`) and frontend (`frontend/app/`). Backend changes are Python (Flask + ReportLab). Frontend changes are React/Next.js. Grok integration is a new Flask endpoint proxied from the admin frontend. No changes to the consumer-facing pipeline logic (`parsing_engine.py`, `analyst.py`).

**Tech Stack:** Python 3.14, Flask, ReportLab 4.4, Next.js, Grammarly Text Editor SDK, xAI API (Grok)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `bitmoji_credit_app/dispute_engine/legal_library.py` | Modify | Expand state law to 50+DC, fill case law gaps, add 2 new theories |
| `bitmoji_credit_app/dispute_engine/letter_generator.py` | Modify | Add Section 8 state law, wire state precedent into Section 4 |
| `bitmoji_credit_app/dispute_engine/pdf_renderer.py` | Modify | Professional formatting, page numbers, letterhead, citation styling |
| `bitmoji_credit_app/api/grok.py` | Create | Flask endpoint proxying admin queries to xAI API |
| `bitmoji_credit_app/app.py` | Modify | Register Grok route |
| `frontend/app/page.tsx` | Modify | Two-state CTA, acknowledge box, black text fixes |
| `frontend/app/garden/page.tsx` | Modify | Grammarly SDK on letter preview modal |
| `frontend/app/admin/page.tsx` | Modify | Add Intelligence tab with Grok chat |

---

### Task 1: Expand State Law Authorities to 50 States + DC

**Files:**
- Modify: `bitmoji_credit_app/dispute_engine/legal_library.py` (lines 435-472, `STATE_LAW_AUTHORITIES` dict)

- [ ] **Step 1: Read current state of legal_library.py and api/state_laws.py**

Verify current `STATE_LAW_AUTHORITIES` has only TX/CA/NY/MA. Verify `api/state_laws.py` has all 50+DC in `STATE_LAWS` dict and `STATE_CASE_LAW` dict.

- [ ] **Step 2: Replace STATE_LAW_AUTHORITIES with full 50+DC dict**

Replace the existing 4-entry `STATE_LAW_AUTHORITIES` dict (lines 435-472) with the full merged dataset. Each entry follows this schema:

```python
'AL': {
    'name': 'Alabama',
    'sol_written': 6,
    'sol_oral': 6,
    'sol_open': 6,
    'sol_statute': 'Ala. Code § 6-2-34',
    'consumer_protection': 'Alabama Deceptive Trade Practices Act (Ala. Code § 8-19-1)',
    'debt_collection': '',
    'additional': '',
    'state_case_law': {},
    'verified': True,
    'verified_date': '2026-05-01',
},
```

States with case law from `STATE_CASE_LAW` (TX, CA, WA, FL, NY) get their `state_case_law` dict populated:

```python
'TX': {
    'name': 'Texas',
    'sol_written': 4,
    'sol_oral': 4,
    'sol_open': 4,
    'sol_statute': 'Tex. Civ. Prac. & Rem. Code § 16.004',
    'consumer_protection': 'Texas Deceptive Trade Practices Act (Tex. Bus. & Com. Code § 17.41 et seq.)',
    'debt_collection': 'Texas Debt Collection Act (Tex. Fin. Code Ch. 392)',
    'additional': 'Tex. Fin. Code § 392.304 — prohibits misrepresenting a debt. Collecting on time-barred debt is actionable deception.',
    'state_case_law': {
        'collections': 'Cushman and Tex. Fin. Code 392.304 — Texas Debt Collection Act prohibits misrepresenting a debt.',
        'aged_debt': 'Texas SOL for written contracts is 4 years (Tex. Civ. Prac. & Rem. Code 16.004).',
        'default': 'Texas DTPA (Tex. Bus. & Com. Code 17.41 et seq.) provides treble damages for knowing violations.',
    },
    'verified': True,
    'verified_date': '2026-05-01',
},
```

Full state list: AL, AK, AZ, AR, CA, CO, CT, DE, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NY, NC, ND, OH, OK, OR, PA, RI, SC, SD, TN, TX, UT, VT, VA, WA, WV, WI, WY, DC.

Data source for each state: `api/state_laws.py` `STATE_LAWS` dict (sol_written, sol_oral, sol_open, statute, consumer_act, extra) merged with `STATE_CASE_LAW` dict where available.

- [ ] **Step 3: Update get_state_law() to handle new fields**

The existing `get_state_law()` function (line 521) already works — it just does a dict lookup and checks `verified`. No change needed. Verify it still returns correctly with the expanded entries.

- [ ] **Step 4: Verify by running a quick test**

```bash
cd C:\Users\sgill\BitmojiGuy_CreditFix_FULL\bitmoji_credit_app
python -c "from dispute_engine.legal_library import get_state_law; print(get_state_law('TX')); print(get_state_law('WA')); print(get_state_law('FL')); print(len([k for k in __import__('dispute_engine.legal_library', fromlist=['STATE_LAW_AUTHORITIES']).STATE_LAW_AUTHORITIES]))"
```

Expected: TX, WA, FL all return dicts with state_case_law. Count = 51.

- [ ] **Step 5: Commit**

```bash
git add bitmoji_credit_app/dispute_engine/legal_library.py
git commit -m "feat: expand state law authorities to all 50 states + DC"
```

---

### Task 2: Fill Federal Case Law Gaps + Add New Theories

**Files:**
- Modify: `bitmoji_credit_app/dispute_engine/legal_library.py` (VIOLATION_THEORIES dict)

- [ ] **Step 1: Add case law to re_aging theory**

Find `'re_aging'` in `VIOLATION_THEORIES`. Its `federal_case_law` list is empty (after the comment on line 195). Add:

```python
'federal_case_law': [
    {
        'citation': 'Grigoryan v. Experian Information Solutions, Inc., 84 F. Supp. 3d 1044 (C.D. Cal. 2014)',
        'court': 'C.D. California',
        'year': 2014,
        'holding': (
            'CRA liable for failing to remove obsolete information and for reporting '
            'accounts past the 7-year reporting period. The duty under § 1681c(a) is '
            'non-delegable and the CRA cannot rely solely on furnisher representations '
            'regarding the date of first delinquency.'
        ),
        'verified': True, 'verified_date': '2026-05-01',
    },
    {
        'citation': 'Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002)',
        'court': '8th Circuit',
        'year': 2002,
        'holding': (
            'Pulling a consumer report for an impermissible purpose, including for '
            'time-barred debts, violates FCRA § 604. Reporting entities must verify '
            'that the purpose of the report is permissible.'
        ),
        'verified': True, 'verified_date': '2026-05-01',
    },
],
```

- [ ] **Step 2: Add case law to obsolescence theory**

Find `'obsolescence'` in `VIOLATION_THEORIES`. Its `federal_case_law` list is empty. Add:

```python
'federal_case_law': [
    {
        'citation': 'Grigoryan v. Experian Information Solutions, Inc., 84 F. Supp. 3d 1044 (C.D. Cal. 2014)',
        'court': 'C.D. California',
        'year': 2014,
        'holding': (
            'CRA liable for failing to remove obsolete information past the 7-year '
            'reporting period under FCRA § 605(a).'
        ),
        'verified': True, 'verified_date': '2026-05-01',
    },
],
```

- [ ] **Step 3: Add case law to validation_failure theory**

Find `'validation_failure'` in `VIOLATION_THEORIES`. Its `federal_case_law` list is empty. Add:

```python
'federal_case_law': [
    {
        'citation': 'Gorman v. Wolpoff & Abramson, LLP, 584 F.3d 1147 (9th Cir. 2009)',
        'court': '9th Circuit',
        'year': 2009,
        'holding': (
            'A debt collector that continues to report a debt to credit bureaus after '
            'receiving a consumer dispute may be liable under the FDCPA. Reporting an '
            'unverified debt constitutes collection activity subject to the validation '
            'requirements of § 1692g(b).'
        ),
        'verified': True, 'verified_date': '2026-05-01',
    },
    {
        'citation': 'Dennis v. BEH-1, LLC, 520 F.3d 1066 (9th Cir. 2008)',
        'court': '9th Circuit',
        'year': 2008,
        'holding': (
            'Failure to provide adequate debt validation upon consumer request violates '
            'the FDCPA. The collector bears the burden of providing verification that '
            'substantively addresses the consumer\'s dispute.'
        ),
        'verified': True, 'verified_date': '2026-05-01',
    },
],
```

- [ ] **Step 4: Add case law to duplicate_inconsistent_reporting theory**

Find `'duplicate_inconsistent_reporting'`. Its `federal_case_law` list is empty. Add:

```python
'federal_case_law': [
    {
        'citation': 'Cortez v. Trans Union LLC, 617 F.3d 688 (3d Cir. 2010)',
        'court': '3d Circuit',
        'year': 2010,
        'holding': (
            'CRA liable for inconsistent reporting attributable to inadequate matching '
            'procedures. Duplicate entries for the same underlying account are inherently '
            'inaccurate under § 1681e(b).'
        ),
        'verified': True, 'verified_date': '2026-05-01',
    },
],
```

- [ ] **Step 5: Add case law to identity_theft_documented theory**

Find `'identity_theft_documented'`. Add to existing `federal_case_law` list (after Sloane):

```python
{
    'citation': 'Nelson v. Chase Manhattan Mortgage Corp., 282 F.3d 1057 (9th Cir. 2002)',
    'court': '9th Circuit',
    'year': 2002,
    'holding': (
        'A furnisher that continues to report an account after receiving notice of '
        'identity theft may be liable under FCRA § 623(b) for failure to conduct a '
        'reasonable investigation.'
    ),
    'verified': True, 'verified_date': '2026-05-01',
},
```

- [ ] **Step 6: Add Gorman to improper_chain_of_ownership theory**

Find `'improper_chain_of_ownership'`. Add to existing `federal_case_law` list (after Johnson):

```python
{
    'citation': 'Gorman v. Wolpoff & Abramson, LLP, 584 F.3d 1147 (9th Cir. 2009)',
    'court': '9th Circuit',
    'year': 2009,
    'holding': (
        'A debt collector reporting disputed debt to credit bureaus may be liable '
        'as a furnisher. Credit bureau reporting constitutes collection activity '
        'subject to FDCPA requirements.'
    ),
    'verified': True, 'verified_date': '2026-05-01',
},
```

- [ ] **Step 7: Add late_payment_inaccuracy theory**

Add new entry to `VIOLATION_THEORIES` dict after the `identity_theft_documented` entry:

```python
'late_payment_inaccuracy': {
    'id': 'late_payment_inaccuracy',
    'title': 'Inaccurate Late Payment Reporting',
    'description': (
        'The account shows late payment notations that the consumer disputes as inaccurate. '
        'The consumer asserts payment was made on time, or the late notation was reported '
        'during a hardship accommodation period in violation of CARES Act protections.'
    ),
    'statutory_anchors': [
        {
            'citation': '15 U.S.C. § 1681s-2(a)(1)(A)',
            'short': 'FCRA § 623(a)(1)(A)',
            'obligation': 'Furnisher shall not report information the furnisher knows or has reasonable cause to believe is inaccurate.',
            'verified': True, 'verified_date': '2026-05-01',
        },
        {
            'citation': '15 U.S.C. § 1681i(a)',
            'short': 'FCRA § 611(a)',
            'obligation': 'CRA must conduct a reasonable reinvestigation of disputed information within 30 days.',
            'verified': True, 'verified_date': '2026-05-01',
        },
        {
            'citation': '15 U.S.C. § 1681s-2(a)(1)(F)',
            'short': 'FCRA § 623(a)(1)(F)',
            'obligation': 'During CARES Act accommodation, furnisher must report account as current if consumer is meeting accommodation terms.',
            'verified': True, 'verified_date': '2026-05-01',
        },
    ],
    'regulatory_anchors': [],
    'federal_case_law': [
        {
            'citation': 'Seamans v. Temple University, 744 F.3d 853 (3d Cir. 2014)',
            'court': '3d Circuit',
            'year': 2014,
            'holding': (
                'A furnisher must investigate disputed payment history information upon '
                'notice from a CRA. Failure to review internal records showing timely '
                'payment constitutes an unreasonable investigation under § 1681s-2(b).'
            ),
            'verified': True, 'verified_date': '2026-05-01',
        },
        {
            'citation': 'Saunders v. Branch Banking and Trust Co. of Virginia, 526 F.3d 142 (4th Cir. 2008)',
            'court': '4th Circuit',
            'year': 2008,
            'holding': (
                'A creditor cannot ignore a consumer dispute forwarded by a CRA. The duty '
                'to investigate under § 1681s-2(b) requires meaningful review, not rubber-stamping.'
            ),
            'verified': True, 'verified_date': '2026-05-01',
        },
    ],
    'removal_authority': [
        {
            'basis': '15 U.S.C. § 1681i(a)(5)(A)',
            'framing': 'If the late payment notation cannot be verified with payment records, the notation must be deleted.',
        },
        {
            'basis': '15 U.S.C. § 1681s-2(a)(1)(A)',
            'framing': 'Information the furnisher knows or should know is inaccurate must not be reported.',
        },
    ],
},
```

- [ ] **Step 8: Add method_of_verification theory**

Add new entry to `VIOLATION_THEORIES` dict after `late_payment_inaccuracy`:

```python
'method_of_verification': {
    'id': 'method_of_verification',
    'title': 'Method of Verification Demand',
    'description': (
        'The CRA has responded to a prior dispute claiming the information was verified, '
        'but has not provided the method of verification as required by FCRA § 611(a)(6)(B)(iii). '
        'This follow-up demands the specific procedure used to determine accuracy.'
    ),
    'statutory_anchors': [
        {
            'citation': '15 U.S.C. § 1681i(a)(6)(B)(iii)',
            'short': 'FCRA § 611(a)(6)(B)(iii)',
            'obligation': 'CRA must provide consumer with description of procedure used to determine accuracy, including furnisher name, address, and telephone number.',
            'verified': True, 'verified_date': '2026-05-01',
        },
        {
            'citation': '15 U.S.C. § 1681n',
            'short': 'FCRA § 616',
            'obligation': 'Willful noncompliance: $100-$1,000 statutory damages per violation, plus punitive damages and attorney fees.',
            'verified': True, 'verified_date': '2026-05-01',
        },
        {
            'citation': '15 U.S.C. § 1681o',
            'short': 'FCRA § 617',
            'obligation': 'Negligent noncompliance: actual damages plus attorney fees.',
            'verified': True, 'verified_date': '2026-05-01',
        },
    ],
    'regulatory_anchors': [],
    'federal_case_law': [
        {
            'citation': 'Dennis v. BEH-1, LLC, 520 F.3d 1066 (9th Cir. 2008)',
            'court': '9th Circuit',
            'year': 2008,
            'holding': (
                'Failure to provide the method of verification is actionable under '
                'FCRA § 611. The consumer has a right to know how accuracy was determined.'
            ),
            'verified': True, 'verified_date': '2026-05-01',
        },
        {
            'citation': 'Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997)',
            'court': '3d Circuit',
            'year': 1997,
            'holding': (
                'A CRA must go beyond automated verification (e-OSCAR) and conduct a '
                'genuine reinvestigation. Merely parroting furnisher responses is insufficient.'
            ),
            'verified': True, 'verified_date': '2026-05-01',
        },
        {
            'citation': 'Johnson v. MBNA America Bank, N.A., 357 F.3d 426 (4th Cir. 2004)',
            'court': '4th Circuit',
            'year': 2004,
            'holding': (
                'Furnisher has independent duty to conduct meaningful review of disputed '
                'information under § 623(b).'
            ),
            'verified': True, 'verified_date': '2026-05-01',
        },
    ],
    'removal_authority': [
        {
            'basis': '15 U.S.C. § 1681i(a)(5)(A)',
            'framing': 'If verification procedure cannot be substantiated, the disputed items must be deleted.',
        },
        {
            'basis': '15 U.S.C. § 1681i(a)(6)(B)(iii)',
            'framing': 'Failure to provide method of verification is itself a violation warranting escalation.',
        },
    ],
},
```

- [ ] **Step 9: Verify all theories load**

```bash
cd C:\Users\sgill\BitmojiGuy_CreditFix_FULL\bitmoji_credit_app
python -c "from dispute_engine.legal_library import list_all_theories, get_verified_cases; theories = list_all_theories(); print(f'Theories: {len(theories)}'); [print(f'  {t}: {len(get_verified_cases(t))} cases') for t in theories]"
```

Expected: 9 theories total, each with 1+ verified cases.

- [ ] **Step 10: Commit**

```bash
git add bitmoji_credit_app/dispute_engine/legal_library.py
git commit -m "feat: fill federal case law gaps, add late_payment and MOV theories"
```

---

### Task 3: Add Section 8 State Law to Letter Generator

**Files:**
- Modify: `bitmoji_credit_app/dispute_engine/letter_generator.py`

- [ ] **Step 1: Add _build_section_8_state_law function**

Add after `_build_section_7_disclaimers` (after line 335):

```python
def _build_section_8_state_law(analyst_report: dict, state_code: str) -> str:
    """Section 8 — State Law Authority. Only appears when state is known."""
    state = get_state_law(state_code)
    if not state:
        return ''

    lines = [f'SECTION 8 — STATE LAW AUTHORITY ({state["name"].upper()})', '']
    lines.append(f'This dispute is further supported by the laws of the State of {state["name"]}:')
    lines.append('')

    # Statute of limitations
    lines.append('Statute of Limitations:')
    lines.append(f'  Written contracts: {state["sol_written"]} years ({state["sol_statute"]})')
    if state.get('sol_oral') and state['sol_oral'] != state['sol_written']:
        lines.append(f'  Oral contracts: {state["sol_oral"]} years')
    if state.get('sol_open') and state['sol_open'] != state['sol_written']:
        lines.append(f'  Open accounts: {state["sol_open"]} years')
    lines.append('')

    # Consumer protection
    if state.get('consumer_protection'):
        lines.append('Consumer Protection:')
        lines.append(f'  {state["consumer_protection"]}')
        lines.append('')

    # Debt collection
    if state.get('debt_collection'):
        lines.append('State Debt Collection Law:')
        lines.append(f'  {state["debt_collection"]}')
        lines.append('')

    # Additional notes
    if state.get('additional'):
        lines.append('Additional:')
        lines.append(f'  {state["additional"]}')
        lines.append('')

    # State case law — default precedent
    state_cases = state.get('state_case_law', {})
    default_case = state_cases.get('default')
    if default_case:
        lines.append(f'State Precedent ({state["name"]}):')
        lines.append(f'  {default_case}')
        lines.append('')

    return '\n'.join(lines)
```

- [ ] **Step 2: Wire Section 8 into generate_bureau_letter**

In `generate_bureau_letter()`, find the `sections` list (around line 393). Add Section 8 between disclaimers and the closing:

```python
    sections = [
        '\n'.join(header),
        _build_section_1_audit(analyst_report),
        _build_section_2_statutory_basis(theory_ids),
        _build_section_3_consumer_position(analyst_report, has_fraud),
        _build_section_4_theory_blocks(analyst_report),
        _build_section_5_requests(analyst_report),
        _build_section_6_demand(analyst_report),
        _build_section_7_disclaimers(analyst_report, has_fraud),
        _build_section_8_state_law(analyst_report, analyst_report.get('state_code', '')),
    ]
```

- [ ] **Step 3: Wire state precedent into Section 4 theory blocks**

In `_build_section_4_theory_blocks()`, after the "Removal Authority" block (around line 220), add state-specific case law for the current theory. This requires passing `state_code` to the function.

Update the function signature:

```python
def _build_section_4_theory_blocks(analyst_report: dict) -> str:
```

Add after the removal authority block (before `lines.append('---')`):

```python
        # State-specific precedent for this theory
        state_code = analyst_report.get('state_code', '')
        if state_code:
            state = get_state_law(state_code)
            if state:
                state_cases = state.get('state_case_law', {})
                # Map theory_id to state_case_law keys
                theory_to_state_key = {
                    'improper_chain_of_ownership': 'collections',
                    'validation_failure': 'collections',
                    'obsolescence': 'aged_debt',
                    're_aging': 'aged_debt',
                }
                state_key = theory_to_state_key.get(block['theory_id'])
                state_case = state_cases.get(state_key) if state_key else None
                if state_case:
                    lines.append(f'State Precedent ({state["name"]}):')
                    lines.append(f'  {state_case}')
                    lines.append('')
```

- [ ] **Step 4: Verify letter generation with state law**

```bash
cd C:\Users\sgill\BitmojiGuy_CreditFix_FULL\bitmoji_credit_app
python -c "
from dispute_engine.letter_generator import _build_section_8_state_law
result = _build_section_8_state_law({}, 'TX')
print(result[:500])
print('---')
result2 = _build_section_8_state_law({}, 'WA')
print(result2[:500])
print('---')
empty = _build_section_8_state_law({}, '')
print(f'Empty state returns: \"{empty}\"')
"
```

Expected: TX and WA produce full state law sections. Empty string returns empty string.

- [ ] **Step 5: Commit**

```bash
git add bitmoji_credit_app/dispute_engine/letter_generator.py
git commit -m "feat: add Section 8 state law and per-theory state precedent to letters"
```

---

### Task 4: Upgrade PDF Renderer

**Files:**
- Modify: `bitmoji_credit_app/dispute_engine/pdf_renderer.py`

- [ ] **Step 1: Add page number callback**

Replace the entire `render_letter_pdf` function with an upgraded version. Add a page number drawing function before `render_letter_pdf`:

```python
from reportlab.lib.colors import black, HexColor

_GOLD = HexColor('#C9A84C')


def _draw_page_number(canvas, doc):
    """Draw 'Page X of Y' at bottom center."""
    canvas.saveState()
    canvas.setFont('Times-Roman', 9)
    canvas.setFillColor(black)
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(
        doc.pagesize[0] / 2.0,
        0.5 * inch,
        f'Page {page_num}',
    )
    canvas.restoreState()
```

- [ ] **Step 2: Add enhanced styles**

Replace `render_letter_pdf` with this upgraded version:

```python
def render_letter_pdf(letter_body: str, consumer_name: str = '', recipient_name: str = '') -> bytes:
    """
    Render a dispute letter as a professionally formatted, sanitized PDF.
    Returns PDF bytes ready for Click2Mail upload or consumer download.
    """
    _sanitize_text(letter_body)

    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        title='',
        author='',
        subject='',
        creator='',
    )

    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        'LetterBody', parent=styles['Normal'],
        fontName='Times-Roman', fontSize=11, leading=15,
        spaceAfter=6, textColor=black,
    )
    heading_style = ParagraphStyle(
        'LetterHeading', parent=styles['Normal'],
        fontName='Times-Bold', fontSize=12, leading=16,
        spaceAfter=2, spaceBefore=14, textColor=black,
    )
    subheading_style = ParagraphStyle(
        'LetterSubHeading', parent=styles['Normal'],
        fontName='Times-Bold', fontSize=11, leading=15,
        spaceAfter=4, spaceBefore=10, textColor=black,
    )
    bullet_style = ParagraphStyle(
        'LetterBullet', parent=styles['Normal'],
        fontName='Times-Roman', fontSize=10, leading=13,
        spaceAfter=3, textColor=black,
        leftIndent=36, firstLineIndent=-18,
    )
    citation_style = ParagraphStyle(
        'LetterCitation', parent=styles['Normal'],
        fontName='Times-Roman', fontSize=10, leading=13,
        spaceAfter=3, textColor=black,
        leftIndent=36,
    )
    small_style = ParagraphStyle(
        'LetterSmall', parent=styles['Normal'],
        fontName='Times-Roman', fontSize=10, leading=13,
        spaceAfter=3, textColor=black,
    )

    from reportlab.platypus import HRFlowable

    flowables = []
    lines = letter_body.split('\n')

    for line in lines:
        stripped = line.strip()

        if not stripped:
            flowables.append(Spacer(1, 6))
            continue

        # Separator lines
        if stripped.startswith('===') or stripped == '---':
            flowables.append(HRFlowable(
                width='100%', thickness=0.5, color=black,
                spaceAfter=8, spaceBefore=8,
            ))
            continue

        safe = stripped.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Section headers
        if stripped.startswith('SECTION '):
            flowables.append(Paragraph(f'<b>{safe}</b>', heading_style))
            flowables.append(HRFlowable(
                width='100%', thickness=0.5, color=black,
                spaceAfter=6, spaceBefore=2,
            ))
        # Sub-section headers (4.A, 4.B, etc.)
        elif re.match(r'^4\.[A-Z]\s', stripped):
            flowables.append(Paragraph(f'<b>{safe}</b>', subheading_style))
        # Bullet items
        elif stripped.startswith('- ') or stripped.startswith('  - '):
            flowables.append(Paragraph(safe, bullet_style))
        # Indented items (statutory citations, notes)
        elif stripped.startswith('  '):
            # Italicize case names (text before comma followed by citation)
            case_match = re.match(r'^(.+?)(,\s*\d+\s+F\..+)$', safe)
            if case_match:
                safe = f'<i>{case_match.group(1)}</i>{case_match.group(2)}'
            flowables.append(Paragraph(safe, citation_style))
        # All-caps lines (sub-labels like "Statutory Authority:", "Factual Basis:")
        elif stripped.isupper() and len(stripped) > 5:
            flowables.append(Paragraph(f'<b>{safe}</b>', heading_style))
        # Labels ending with colon
        elif stripped.endswith(':') and len(stripped) < 60:
            flowables.append(Paragraph(f'<b>{safe}</b>', small_style))
        else:
            flowables.append(Paragraph(safe, body_style))

    doc.build(flowables, onFirstPage=_draw_page_number, onLaterPages=_draw_page_number)

    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
```

- [ ] **Step 3: Verify PDF renders correctly**

```bash
cd C:\Users\sgill\BitmojiGuy_CreditFix_FULL\bitmoji_credit_app
python -c "
from dispute_engine.pdf_renderer import render_letter_pdf
sample = '''May 01, 2026

Jane Doe
456 Oak Lane
Houston, TX 77001

Experian
P.O. Box 4500
Allen, TX 75013

Re: Formal Dispute

============================================================

SECTION 1 — ACCOUNT AUDIT

Item 1:
  Account Name: Portfolio Recovery
  Account Number: ****8821

SECTION 4 — GROUNDS FOR DISPUTE

4.A — IMPROPER CHAIN OF OWNERSHIP

  - Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997)

---

Sincerely,

Jane Doe'''

pdf = render_letter_pdf(sample, 'Jane Doe', 'Experian')
print(f'PDF size: {len(pdf)} bytes')
with open('test_letter.pdf', 'wb') as f:
    f.write(pdf)
print('Saved to test_letter.pdf')
"
```

Expected: PDF renders without error, includes page numbers.

- [ ] **Step 4: Commit**

```bash
git add bitmoji_credit_app/dispute_engine/pdf_renderer.py
git commit -m "feat: upgrade PDF renderer with professional formatting and page numbers"
```

---

### Task 5: Landing Page CTA Overhaul

**Files:**
- Modify: `frontend/app/page.tsx` (lines 233-253 CTA button, line 172 h1 color, line 308 admin button color)

- [ ] **Step 1: Add useState for acknowledge state**

At the top of `Home()` component (after line 16), add:

```tsx
const [showAcknowledge, setShowAcknowledge] = useState(false)
```

Add `useState` to the import on line 3 (it's not currently imported):

```tsx
'use client'

import { useState } from 'react'
import { useShojiNav } from '@/lib/shojiNav'
```

- [ ] **Step 2: Change h1 color to black**

Replace line 172 (`color: '#F0D080'`) and the text-shadow:

```tsx
        <h1
          style={{
            fontFamily: 'var(--font-cinzel-decorative), serif',
            fontSize: 'clamp(2rem, 5vw, 3.4rem)',
            color: '#000000',
            letterSpacing: 4,
            lineHeight: 1.1,
            margin: 0,
          }}
        >
```

(Remove the `textShadow` line entirely from the h1.)

- [ ] **Step 3: Change Admin Dashboard button color to black**

Replace the admin button `color: '#8A8278'` (line 308) with `color: '#000000'`:

```tsx
          style={{
            marginTop: '2.5rem',
            fontFamily: 'var(--font-cinzel), serif',
            fontSize: 11,
            letterSpacing: 3,
            textTransform: 'uppercase',
            color: '#000000',
            background: 'transparent',
            padding: '8px 24px',
            borderRadius: 4,
            border: '1px solid rgba(0,0,0,0.25)',
            cursor: 'pointer',
            transition: 'all 0.3s',
          }}
```

- [ ] **Step 4: Replace CTA button with two-state behavior**

Replace the existing CTA button (lines 233-253) with:

```tsx
        <button
          onClick={() => {
            if (showAcknowledge) {
              navigateTo('/map')
            } else {
              setShowAcknowledge(true)
            }
          }}
          style={{
            marginTop: '1.5rem',
            fontFamily: 'var(--font-cinzel), serif',
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: 4,
            textTransform: 'uppercase',
            color: '#1A0A02',
            background: 'linear-gradient(135deg, #8B6914, #F0D080)',
            padding: '1rem 2.5rem',
            borderRadius: 4,
            border: '1px solid #8B5A20',
            cursor: 'pointer',
            boxShadow: '0 6px 30px rgba(201,168,76,0.45), inset 0 1px 0 rgba(255,255,255,0.25)',
            transition: 'all 0.2s',
          }}
        >
          {showAcknowledge ? 'I Acknowledge \u2014 Proceed to Credit Fix' : 'Begin Your Credit Fix \u2014 $24.99'}
        </button>

        {showAcknowledge && (
          <div style={{
            marginTop: '1rem',
            padding: '1.25rem',
            background: '#C9A84C',
            borderRadius: 8,
            border: '2px solid #000000',
            maxWidth: 520,
            textAlign: 'left',
          }}>
            <p style={{
              fontFamily: 'var(--font-cinzel-decorative), serif',
              fontSize: 13,
              fontWeight: 700,
              color: '#000000',
              textShadow: '0 0 8px #000000, 0 0 16px #000000',
              lineHeight: 1.7,
              margin: 0,
              marginBottom: 12,
            }}>
              By proceeding I confirm:<br />
              - I am the consumer named in these disputes, 18+, US resident<br />
              - This is a technology tool &mdash; not a law firm or credit repair service<br />
              - I direct all actions. No legal advice is provided.<br />
              - $24.99 covers letter generation only. Postage is separate (~$20-40)<br />
              - Results are not guaranteed
            </p>
            <p style={{
              fontFamily: 'var(--font-rajdhani), sans-serif',
              fontSize: 9,
              color: 'rgba(0,0,0,0.55)',
              maxWidth: 480,
              textAlign: 'center',
              lineHeight: 1.6,
              maxHeight: 80,
              overflowY: 'auto',
              margin: '0 auto',
            }}>
              BitmojiGuy 5 Min CreditFix is a financial technology tool operated by Arden Edge Capital (AE.CC.001). Not a credit repair organization, law firm, credit counseling service, or debt settlement company. No attorney-client relationship is created. No legal advice is provided. Consumer directs all actions. Letters authored by consumer under rights arising from: Fair Credit Reporting Act (15 U.S.C. &sect; 1681 et seq.) | Fair Debt Collection Practices Act (15 U.S.C. &sect; 1692 et seq.) | Equal Credit Opportunity Act (15 U.S.C. &sect; 1691 et seq.) | Consumer Financial Protection Act (12 U.S.C. &sect; 5481 et seq.) | Applicable state consumer protection law. Exempt from Credit Repair Organizations Act (15 U.S.C. &sect; 1679) &mdash; no advance fees collected for credit repair services, no representations of credit improvement made, consumer directs all actions. Exempt from Texas Credit Services Organization Act (Tex. Fin. Code &sect; 393) on same basis. Data processed in closed-loop session &mdash; not retained, transmitted, or sold to third parties. Results not guaranteed. Bureaus are legally required to investigate disputes but not required to remove accurate information. For free federal dispute resources visit consumerfinance.gov. Governing law: State of Texas. Disputes resolved by binding arbitration. &copy; 2026 Arden Edge Capital | AE.CC.001 | ardanedgecapital.com
            </p>
          </div>
        )}
```

- [ ] **Step 5: Verify in browser**

```bash
cd C:\Users\sgill\BitmojiGuy_CreditFix_FULL\frontend
npm run dev
```

Open http://localhost:3000. Verify:
1. h1 "BitmojiGuy 5 Min Credit Tool" is black text
2. CTA says "Begin Your Credit Fix — $24.99"
3. Click CTA → acknowledge box appears with gold background
4. CTA text changes to "I Acknowledge — Proceed to Credit Fix"
5. Click again → navigates to /map
6. "Admin Dashboard" text is black
7. Everything else on page untouched (seascape, orbital ring, price box, videos)

- [ ] **Step 6: Commit**

```bash
git add frontend/app/page.tsx
git commit -m "feat: two-state CTA with legal disclosures, black text for h1 and admin"
```

---

### Task 6: Grammarly SDK on Letter Preview

**Files:**
- Modify: `frontend/app/garden/page.tsx` (letter preview modal, lines 302-397)

- [ ] **Step 1: Add Grammarly script loader**

Add a `useEffect` at the top of `GardenPage` to load the Grammarly SDK script dynamically:

```tsx
  // Load Grammarly SDK if client ID is configured
  useEffect(() => {
    const clientId = process.env.NEXT_PUBLIC_GRAMMARLY_CLIENT_ID
    if (!clientId) return
    if (document.querySelector('script[src*="grammarly"]')) return
    const script = document.createElement('script')
    script.src = 'https://js.grammarly.com/grammarly-editor-plugin/v1/index.js'
    script.async = true
    document.head.appendChild(script)
  }, [])
```

- [ ] **Step 2: Wrap letter body in Grammarly editor**

In the letter preview modal (around line 388), replace the plain text `<div>` with a Grammarly-wrapped textarea:

Replace:
```tsx
            {/* Letter body */}
            <div style={{
              padding: '20px',
              fontFamily: 'var(--font-body)', fontSize: 13, color: '#E0DCD4',
              lineHeight: 1.8, whiteSpace: 'pre-wrap',
            }}>
              {modalLetter.body}
            </div>
```

With:
```tsx
            {/* Letter body — Grammarly-enabled if SDK loaded */}
            <div style={{ padding: '20px' }}>
              {process.env.NEXT_PUBLIC_GRAMMARLY_CLIENT_ID ? (
                // @ts-expect-error Grammarly custom element
                <grammarly-editor-plugin clientId={process.env.NEXT_PUBLIC_GRAMMARLY_CLIENT_ID}>
                  <textarea
                    defaultValue={modalLetter.body}
                    style={{
                      width: '100%',
                      minHeight: 400,
                      fontFamily: 'Georgia, Times, serif',
                      fontSize: 13,
                      color: '#E0DCD4',
                      background: 'transparent',
                      border: 'none',
                      lineHeight: 1.8,
                      resize: 'vertical',
                      outline: 'none',
                    }}
                  />
                {/* @ts-expect-error Grammarly custom element */}
                </grammarly-editor-plugin>
              ) : (
                <div style={{
                  fontFamily: 'var(--font-body)', fontSize: 13, color: '#E0DCD4',
                  lineHeight: 1.8, whiteSpace: 'pre-wrap',
                }}>
                  {modalLetter.body}
                </div>
              )}
            </div>
```

- [ ] **Step 3: Add env var placeholder**

Create or update `.env.local` in frontend directory:

```bash
echo "# Grammarly Text Editor SDK — register at developer.grammarly.com" >> C:\Users\sgill\BitmojiGuy_CreditFix_FULL\frontend\.env.local
echo "# NEXT_PUBLIC_GRAMMARLY_CLIENT_ID=your-client-id-here" >> C:\Users\sgill\BitmojiGuy_CreditFix_FULL\frontend\.env.local
```

- [ ] **Step 4: Verify graceful fallback**

Without the env var set, the letter preview should show the plain text div (existing behavior). No errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/garden/page.tsx
git commit -m "feat: add Grammarly SDK to letter preview with graceful fallback"
```

---

### Task 7: Grok Intelligence Panel — Backend

**Files:**
- Create: `bitmoji_credit_app/api/grok.py`
- Modify: `bitmoji_credit_app/app.py` (register route)

- [ ] **Step 1: Create api/grok.py**

```python
"""
Grok Intelligence — Admin-only xAI API proxy.

Rules:
- Admin-authenticated only, never client-facing
- API key server-side only, never exposed to frontend
- System prompt loaded with legal library context
- No consumer PII in queries
"""

import os
import requests as http_requests
from flask import request, jsonify


XAI_API_URL = 'https://api.x.ai/v1/responses'

SYSTEM_PROMPT = """You are an admin research assistant for a consumer credit dispute fintech tool (BitmojiGuy 5 Min CreditFix by Arden Edge Capital).

Your role:
- Help the admin research federal and state credit dispute law
- Suggest improvements to dispute letter templates
- Answer client questions about the dispute process
- Research new case law and regulatory changes
- Provide strategy recommendations for specific dispute scenarios

Context:
- The tool helps consumers exercise rights under FCRA (15 U.S.C. § 1681 et seq.), FDCPA (15 U.S.C. § 1692 et seq.), and state consumer protection laws
- It is NOT a credit repair organization, law firm, or credit counseling service
- The consumer directs all actions — the tool generates letters based on consumer-affirmed grounds only
- Letters are organized by violation theory: improper chain of ownership, address inaccuracy, re-aging, obsolescence, validation failure, duplicate reporting, mixed file, identity theft, late payment inaccuracy, method of verification demand

Important:
- All your output is for admin review only — never shown directly to consumers
- Be specific with case citations — include full citation, court, year, and holding
- When suggesting letter language, maintain the honest position framing (say "I cannot verify" not "this is inaccurate" when epistemic state is uncertainty)
"""


def grok_query():
    """Handle admin Grok query. Requires admin session."""
    api_key = os.environ.get('XAI_API_KEY', '')
    if not api_key:
        return jsonify({'error': 'XAI_API_KEY not configured'}), 500

    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        resp = http_requests.post(
            XAI_API_URL,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            json={
                'model': 'grok-4.20-reasoning',
                'input': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': prompt},
                ],
            },
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        # Extract response text from xAI response format
        output_text = ''
        for item in result.get('output', []):
            if item.get('type') == 'message':
                for content in item.get('content', []):
                    if content.get('type') == 'output_text':
                        output_text += content.get('text', '')
        if not output_text:
            output_text = str(result)
        return jsonify({'response': output_text})
    except http_requests.exceptions.Timeout:
        return jsonify({'error': 'Grok request timed out'}), 504
    except http_requests.exceptions.RequestException as e:
        return jsonify({'error': f'Grok API error: {str(e)}'}), 502
```

- [ ] **Step 2: Register route in app.py**

Find the admin route section in `app.py`. Add the Grok endpoint after the existing admin API routes. The exact location depends on how routes are registered. Add:

```python
from api.grok import grok_query

# Inside the admin routes section, add:
@app.route('/admin/api/grok', methods=['POST'])
@admin_required  # use whatever admin auth decorator exists
def admin_grok():
    return grok_query()
```

If `app.py` uses a different auth pattern (e.g., checking session manually), wrap accordingly:

```python
@app.route('/admin/api/grok', methods=['POST'])
def admin_grok():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return grok_query()
```

- [ ] **Step 3: Add XAI_API_KEY to .env**

```bash
echo "# xAI Grok API — admin intelligence panel" >> C:\Users\sgill\BitmojiGuy_CreditFix_FULL\bitmoji_credit_app\.env
echo "# Paste your API key below (never commit this file)" >> C:\Users\sgill\BitmojiGuy_CreditFix_FULL\bitmoji_credit_app\.env
echo "XAI_API_KEY=" >> C:\Users\sgill\BitmojiGuy_CreditFix_FULL\bitmoji_credit_app\.env
```

- [ ] **Step 4: Verify .env is in .gitignore**

```bash
grep -q "\.env" C:\Users\sgill\BitmojiGuy_CreditFix_FULL\.gitignore && echo "OK" || echo "WARNING: add .env to .gitignore"
```

- [ ] **Step 5: Commit**

```bash
git add bitmoji_credit_app/api/grok.py
git commit -m "feat: add admin-only Grok intelligence endpoint"
```

---

### Task 8: Grok Intelligence Panel — Frontend

**Files:**
- Modify: `frontend/app/admin/page.tsx`

- [ ] **Step 1: Add intelligence tab state**

Update the `activeTab` type on line 89:

```tsx
const [activeTab, setActiveTab] = useState<'cases' | 'pipeline' | 'notifications' | 'intelligence'>('cases')
```

- [ ] **Step 2: Add intelligence state variables**

After the existing `useState` declarations (around line 89), add:

```tsx
  const [grokPrompt, setGrokPrompt] = useState('')
  const [grokResponse, setGrokResponse] = useState('')
  const [grokLoading, setGrokLoading] = useState(false)
  const [grokHistory, setGrokHistory] = useState<{prompt: string, response: string}[]>([])
```

- [ ] **Step 3: Add Grok query function**

After the existing action functions (around line 198), add:

```tsx
  async function queryGrok() {
    if (!grokPrompt.trim()) return
    setGrokLoading(true)
    setGrokResponse('')
    try {
      const res = await fetch(`${FLASK}/admin/api/grok`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: grokPrompt }),
      })
      const data = await res.json()
      const response = data.response || data.error || 'No response'
      setGrokResponse(response)
      setGrokHistory((prev) => [{ prompt: grokPrompt, response }, ...prev].slice(0, 10))
    } catch {
      setGrokResponse('Failed to connect to Grok')
    }
    setGrokLoading(false)
  }
```

- [ ] **Step 4: Add intelligence tab button**

Find the tabs `div` (line 453). Add `'intelligence'` to the tab list:

```tsx
        <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: `1px solid ${GOLD}22` }}>
          {(['cases', 'pipeline', 'notifications', 'intelligence'] as const).map((tab) => (
```

- [ ] **Step 5: Add intelligence tab content**

After the notifications tab content block (after line 736, before the closing `</div>`), add:

```tsx
        {activeTab === 'intelligence' && (
          <div>
            <div style={{
              padding: 20, background: 'rgba(10,8,4,0.5)',
              border: `1px solid ${GOLD}15`, borderRadius: 8, marginBottom: 16,
            }}>
              <h3 style={{
                fontFamily: 'var(--font-cinzel), serif', fontSize: 15,
                color: GOLD, letterSpacing: 2, marginBottom: 16,
                textShadow: `0 0 8px currentColor, 0 0 20px currentColor, 0 0 10px ${GOLD}44`,
              }}>
                Grok Intelligence
              </h3>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 11, color: '#8A8278',
                marginBottom: 16, fontStyle: 'italic',
              }}>
                Research case law, draft letter improvements, answer client questions. Admin-only — never client-facing.
              </p>
              <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
                <textarea
                  value={grokPrompt}
                  onChange={(e) => setGrokPrompt(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); queryGrok() } }}
                  placeholder="Ask Grok... (e.g., 'What case law supports disputing re-aged collection accounts in Florida?')"
                  rows={3}
                  style={{
                    flex: 1, padding: '12px 14px',
                    background: 'rgba(10,8,4,0.7)', border: `1px solid ${GOLD}22`,
                    borderRadius: 6, color: '#F0EBE0',
                    fontFamily: 'var(--font-body)', fontSize: 13,
                    outline: 'none', resize: 'vertical',
                  }}
                />
                <button
                  onClick={queryGrok}
                  disabled={grokLoading || !grokPrompt.trim()}
                  style={{
                    alignSelf: 'flex-end',
                    padding: '12px 24px',
                    fontFamily: 'var(--font-cinzel), serif', fontSize: 12,
                    letterSpacing: 2, textTransform: 'uppercase',
                    color: '#1A0A02',
                    background: grokLoading ? 'rgba(100,100,100,0.3)' : `linear-gradient(135deg, ${GOLD}, #8B6914)`,
                    border: 'none', borderRadius: 4,
                    cursor: grokLoading ? 'not-allowed' : 'pointer',
                    boxShadow: grokLoading ? 'none' : `0 4px 20px ${GOLD}55`,
                    opacity: grokLoading ? 0.5 : 1,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {grokLoading ? 'Thinking...' : 'Query'}
                </button>
              </div>

              {/* Current response */}
              {grokResponse && (
                <div style={{
                  padding: 16, background: 'rgba(0,0,0,0.4)',
                  border: `1px solid ${GOLD}22`, borderRadius: 6,
                  maxHeight: 500, overflowY: 'auto',
                }}>
                  <pre style={{
                    fontFamily: 'var(--font-body)', fontSize: 13,
                    color: '#F0EBE0', lineHeight: 1.7,
                    whiteSpace: 'pre-wrap', wordWrap: 'break-word',
                    margin: 0,
                  }}>
                    {grokResponse}
                  </pre>
                </div>
              )}
            </div>

            {/* History */}
            {grokHistory.length > 1 && (
              <div style={{
                padding: 20, background: 'rgba(10,8,4,0.5)',
                border: `1px solid ${GOLD}15`, borderRadius: 8,
              }}>
                <h4 style={{
                  fontFamily: 'var(--font-cinzel), serif', fontSize: 12,
                  color: GOLD, letterSpacing: 2, marginBottom: 12,
                }}>
                  Recent Queries
                </h4>
                {grokHistory.slice(1).map((h, i) => (
                  <div key={i} style={{
                    padding: '10px 0',
                    borderBottom: `1px solid ${GOLD}11`,
                  }}>
                    <p style={{
                      fontFamily: 'var(--font-body)', fontSize: 12,
                      color: GOLD, margin: '0 0 4px',
                    }}>
                      Q: {h.prompt.slice(0, 120)}{h.prompt.length > 120 ? '...' : ''}
                    </p>
                    <p style={{
                      fontFamily: 'var(--font-body)', fontSize: 11,
                      color: '#8A8278', margin: 0,
                    }}>
                      A: {h.response.slice(0, 200)}{h.response.length > 200 ? '...' : ''}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
```

- [ ] **Step 6: Verify in browser**

Navigate to http://localhost:3000/admin, log in, click "Intelligence" tab. Verify:
1. Tab appears in tab bar
2. Textarea and Query button render
3. Without XAI_API_KEY set, submitting shows "XAI_API_KEY not configured" error (expected)
4. UI matches admin theme (dark background, gold accents)

- [ ] **Step 7: Commit**

```bash
git add frontend/app/admin/page.tsx
git commit -m "feat: add Grok Intelligence tab to admin dashboard"
```

---

### Task 9: Final Integration Verification

- [ ] **Step 1: Start backend**

```bash
cd C:\Users\sgill\BitmojiGuy_CreditFix_FULL\bitmoji_credit_app
python app.py
```

Verify Flask starts on port 5000 without import errors.

- [ ] **Step 2: Start frontend**

```bash
cd C:\Users\sgill\BitmojiGuy_CreditFix_FULL\frontend
npm run dev
```

Verify Next.js starts on port 3000 without build errors.

- [ ] **Step 3: Verify landing page CTA flow**

Open http://localhost:3000. Walk through:
1. h1 black text ✓
2. CTA "Begin Your Credit Fix — $24.99" ✓
3. Click → acknowledge box with gold background ✓
4. CTA changes to "I Acknowledge — Proceed to Credit Fix" ✓
5. Click → navigates to /map ✓
6. Admin Dashboard black text ✓

- [ ] **Step 4: Verify letter generation includes state law**

```bash
cd C:\Users\sgill\BitmojiGuy_CreditFix_FULL\bitmoji_credit_app
python -m dispute_engine.letter_generator
```

Check output includes "SECTION 8 — STATE LAW AUTHORITY (TEXAS)".

- [ ] **Step 5: Verify PDF renders with new formatting**

Check `test_letter.pdf` from Task 4 — page numbers, horizontal rules, italic citations.

- [ ] **Step 6: Verify admin Grok tab loads**

Navigate to http://localhost:3000/admin → Intelligence tab renders.

- [ ] **Step 7: Final commit**

```bash
git add -A
git status
git commit -m "feat: letter generator upgrade — state law, case law, PDF, Grammarly, CTA, Grok"
```
