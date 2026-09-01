"""
Letter Generator v3 — comprehensive per-bureau letters.

Rules:
- One comprehensive letter per bureau (not per-item)
- Organized by violation theory blocks, not by item
- Items appearing in multiple theories appear in multiple sections
- No AE branding, no customer numbers, no generator strings
- All citations from legal_library only — never generated on the fly
- Honest position framing throughout
"""

from datetime import datetime
from .legal_library import (
    get_theory, get_verified_cases, get_verified_statutes,
    get_removal_authority, get_escalation_paths, get_state_law,
    VIOLATION_THEORIES,
)


# ═══════════════════════════════════════════════════════════════════════════════
# BUREAU ADDRESSES
# ═══════════════════════════════════════════════════════════════════════════════

BUREAU_ADDRESSES = {
    'equifax': {
        'name': 'Equifax Information Services LLC',
        'address': 'P.O. Box 740256\nAtlanta, GA 30374-0256',
    },
    'experian': {
        'name': 'Experian',
        'address': 'P.O. Box 4500\nAllen, TX 75013',
    },
    'transunion': {
        'name': 'TransUnion LLC',
        'address': 'P.O. Box 2000\nChester, PA 19016',
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_section_1_audit(analyst_report: dict) -> str:
    """Section 1 — Account Audit: all disputed items with reported data."""
    lines = ['SECTION 1 — ACCOUNT AUDIT', '']
    lines.append('I am disputing the following items on my credit report. Each item is identified '
                 'below with its reported data as it appears in my file.')
    lines.append('')

    item_num = 0
    seen_items = set()
    for block in analyst_report['violation_theory_blocks']:
        for item in block['items_affected']:
            if item['item_id'] in seen_items:
                continue
            seen_items.add(item['item_id'])
            item_num += 1
            lines.append(f'Item {item_num}:')
            if item.get('account_name'):
                lines.append(f'  Account Name: {item["account_name"]}')
            if item.get('account_number'):
                lines.append(f'  Account Number: {item["account_number"]}')
            if item.get('current_balance'):
                lines.append(f'  Reported Balance: {item["current_balance"]}')
            if item.get('status'):
                lines.append(f'  Status: {item["status"]}')
            # Pull additional fields from the full account data
            acct = item.get('_full_account', {})
            if acct.get('date_opened'):
                lines.append(f'  Date Opened: {acct["date_opened"]}')
            if acct.get('original_creditor'):
                lines.append(f'  Original Creditor: {acct["original_creditor"]}')
            if acct.get('date_of_first_delinquency'):
                lines.append(f'  Date of First Delinquency: {acct["date_of_first_delinquency"]}')
            if acct.get('account_type'):
                lines.append(f'  Account Type: {acct["account_type"]}')
            if acct.get('credit_limit_or_original_balance'):
                lines.append(f'  Credit Limit / Original Balance: {acct["credit_limit_or_original_balance"]}')
            lines.append('')

    return '\n'.join(lines)


def _build_section_2_statutory_basis(theory_ids: list) -> str:
    """Section 2 — Statutory Basis: all statutes invoked across all theories."""
    lines = ['SECTION 2 — STATUTORY BASIS FOR THIS DISPUTE', '']
    lines.append('This dispute is brought under the following provisions of federal law:')
    lines.append('')

    seen_citations = set()
    for tid in theory_ids:
        for statute in get_verified_statutes(tid):
            cite = statute['citation']
            if cite in seen_citations:
                continue
            seen_citations.add(cite)
            lines.append(f'- {statute["short"]}: {statute["obligation"]}')
            lines.append(f'  ({cite})')
            lines.append('')

    return '\n'.join(lines)


def _build_section_3_consumer_position(analyst_report: dict, has_fraud: bool) -> str:
    """Section 3 — Consumer's Factual Position."""
    lines = ['SECTION 3 — CONSUMER\'S FACTUAL POSITION', '']

    # Build honest-position narrative based on what theories are present
    theory_ids = [b['theory_id'] for b in analyst_report['violation_theory_blocks']]

    if 'identity_theft_documented' in theory_ids:
        lines.append('I am a victim of identity theft. The items identified in this letter as '
                     'subject to identity theft claims are accounts I did not open, authorize, '
                     'or benefit from. I have filed or am prepared to file an FTC Identity Theft Report.')
        lines.append('')

    if 'improper_chain_of_ownership' in theory_ids:
        lines.append('I have reviewed my credit report and identified accounts being reported by '
                     'entities I do not recognize as my original creditors. I am not affirming that '
                     'the underlying debts do not exist — I am stating that the current reporting '
                     'entities have not established their authority to report on these accounts, and '
                     'I cannot verify the chain of ownership from original creditor to current furnisher.')
        lines.append('')

    if 'validation_failure' in theory_ids:
        lines.append('For accounts reported by collection agencies and debt buyers, I have not '
                     'received validation of the debts as required under federal law. I am exercising '
                     'my right to request verification before these items continue to appear on my report.')
        lines.append('')

    if 're_aging' in theory_ids:
        lines.append('I have identified items where the reported dates appear inconsistent with '
                     'what I would expect based on the account history. I am requesting verification '
                     'of the date of first delinquency for these items.')
        lines.append('')

    if 'address_inaccuracy' in theory_ids or 'mixed_file_indicators' in theory_ids:
        lines.append('My consumer file contains personal information — including addresses and/or '
                     'name variants — that do not belong to me. This raises concerns about the '
                     'accuracy of my file and the procedures used to match information to my identity.')
        lines.append('')

    if not has_fraud:
        lines.append('Note: I am not claiming identity theft for the items in this letter unless '
                     'explicitly stated above. My dispute is based on the specific grounds identified '
                     'in Section 4 below.')
        lines.append('')

    return '\n'.join(lines)


def _build_section_4_theory_blocks(analyst_report: dict) -> str:
    """Section 4 — Violation Theory Blocks: the substantive heart."""
    lines = ['SECTION 4 — GROUNDS FOR DISPUTE', '']

    for idx, block in enumerate(analyst_report['violation_theory_blocks']):
        theory = get_theory(block['theory_id'])
        if not theory:
            continue

        letter_label = chr(65 + idx)  # A, B, C, ...
        lines.append(f'4.{letter_label} — {theory["title"].upper()}')
        lines.append('')

        # Items affected
        lines.append('Items Affected:')
        for item in block['items_affected']:
            item_desc = item.get('account_name', 'Unknown')
            if item.get('account_number'):
                item_desc += f' (Acct: {item["account_number"]})'
            if item.get('current_balance'):
                item_desc += f' — {item["current_balance"]}'
            if item.get('status'):
                item_desc += f' [{item["status"]}]'
            lines.append(f'  - {item_desc}')
        lines.append('')

        # Statutory anchors
        lines.append('Statutory Authority:')
        for statute in get_verified_statutes(block['theory_id']):
            lines.append(f'  - {statute["short"]}: {statute["obligation"]}')
        lines.append('')

        # Factual instances
        if block.get('common_factual_pattern'):
            lines.append('Factual Basis:')
            lines.append(f'  {block["common_factual_pattern"]}')
            lines.append('')

        # Per-item notes
        has_item_notes = any(item.get('per_item_notes') for item in block['items_affected'])
        if has_item_notes:
            lines.append('Item-Specific Notes:')
            for item in block['items_affected']:
                if item.get('per_item_notes'):
                    lines.append(f'  {item.get("account_name", "Item")}:')
                    for note in item['per_item_notes']:
                        lines.append(f'    - {note}')
            lines.append('')

        # Enforcement — case law
        cases = get_verified_cases(block['theory_id'])
        if cases:
            lines.append('Judicial Interpretation:')
            for case in cases:
                lines.append(f'  - {case["citation"]}')
                lines.append(f'    Holding: {case["holding"]}')
            lines.append('')

        # Removal authority
        removal = get_removal_authority(block['theory_id'])
        if removal:
            lines.append('Removal Authority:')
            for r in removal:
                lines.append(f'  - Under {r["basis"]}: {r["framing"]}')
            if len(removal) > 1:
                lines.append('  Any one of the above bases is independently sufficient for removal.')
            lines.append('')

        lines.append('---')
        lines.append('')

    return '\n'.join(lines)


def _build_section_5_requests(analyst_report: dict) -> str:
    """Section 5 — Specific Requests tied to each theory block."""
    lines = ['SECTION 5 — SPECIFIC REQUESTS', '']

    for idx, block in enumerate(analyst_report['violation_theory_blocks']):
        theory = get_theory(block['theory_id'])
        if not theory:
            continue

        letter_label = chr(65 + idx)
        req_num = idx + 1

        lines.append(f'Request {req_num} (re: Section 4.{letter_label} — {theory["title"]}):')
        lines.append(f'  (a) Conduct a reinvestigation of all items identified in Section 4.{letter_label}, '
                     f'contacting each furnisher to verify the disputed information with documentation.')
        lines.append(f'  (b) If the furnisher cannot verify the information with documentation, '
                     f'delete the item(s) from my file per 15 U.S.C. § 1681i(a)(5)(A).')
        lines.append(f'  (c) Provide me with a description of the procedure used to determine accuracy '
                     f'and completeness, including the name, address, and telephone number of each '
                     f'furnisher contacted, per 15 U.S.C. § 1681i(a)(6)(B)(iii).')
        lines.append('')

    # General procedural request
    lines.append(f'General Procedural Request:')
    lines.append(f'  Complete all reinvestigations within 30 days of receipt of this letter as '
                 f'required by 15 U.S.C. § 1681i(a)(1). Provide me with written results including '
                 f'a notice of any changes made to my file.')
    lines.append('')

    return '\n'.join(lines)


def _build_section_6_demand(analyst_report: dict) -> str:
    """Section 6 — Cascading Demand for Removal."""
    lines = ['SECTION 6 — DEMAND FOR REMOVAL', '']

    # List all disputed items
    lines.append('I demand the removal of the following items from my consumer file:')
    lines.append('')

    seen_items = set()
    for block in analyst_report['violation_theory_blocks']:
        for item in block['items_affected']:
            if item['item_id'] in seen_items:
                continue
            seen_items.add(item['item_id'])
            item_desc = item.get('account_name', 'Unknown')
            if item.get('account_number'):
                item_desc += f' (Acct: {item["account_number"]})'
            lines.append(f'  - {item_desc}')
    lines.append('')

    # Cascading grounds
    lines.append('Grounds for removal (each independently sufficient):')

    all_removal = []
    seen_bases = set()
    for block in analyst_report['violation_theory_blocks']:
        for r in get_removal_authority(block['theory_id']):
            if r['basis'] not in seen_bases:
                seen_bases.add(r['basis'])
                all_removal.append(r)

    for i, r in enumerate(all_removal, 1):
        prefix = 'Primary' if i == 1 else f'Alternative {i - 1}'
        lines.append(f'  {prefix}: Under {r["basis"]} — {r["framing"]}')
    lines.append('')

    # Escalation paths
    escalation = get_escalation_paths('bureau')
    if escalation:
        lines.append('If the disputed items are not removed within 30 days, I intend to pursue '
                     'the following remedies:')
        for path in escalation:
            lines.append(f'  - {path}')
        lines.append('')

    lines.append('I am retaining copies of this letter and all supporting documentation for '
                 'my records.')
    lines.append('')

    return '\n'.join(lines)


def _build_section_7_disclaimers(analyst_report: dict, has_fraud: bool) -> str:
    """Section 7 — Disclaimers."""
    lines = ['SECTION 7 — DISCLAIMERS', '']

    theory_ids = [b['theory_id'] for b in analyst_report['violation_theory_blocks']]

    if not has_fraud:
        lines.append('- I am not claiming identity theft for the items disputed in this letter '
                     'unless explicitly stated in Section 3.')

    if 'improper_chain_of_ownership' in theory_ids:
        lines.append('- I am not asserting that the underlying debts referenced by the disputed '
                     'accounts do not exist. I am asserting that the current reporting entities '
                     'have not demonstrated their authority to report on my file.')

    if 're_aging' in theory_ids:
        lines.append('- I am not asserting that all reported dates are inaccurate. I am requesting '
                     'verification of specific dates where my records raise questions.')

    lines.append('- This letter is my personal correspondence exercising rights under federal '
                 'and state law. It does not constitute legal advice and was not prepared by an attorney.')
    lines.append('')

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE LETTER COMPOSER
# ═══════════════════════════════════════════════════════════════════════════════

def generate_bureau_letter(
    analyst_report: dict,
    consumer_name: str,
    consumer_address: str,
    bureau_key: str,
    parsed_data: dict = None,
) -> dict:
    """
    Generate one comprehensive letter for one bureau from the analyst report.

    Returns dict with 'recipient', 'subject', 'body', 'metadata'.
    """
    bureau = BUREAU_ADDRESSES.get(bureau_key)
    if not bureau:
        raise ValueError(f'Unknown bureau: {bureau_key}')

    date_str = datetime.now().strftime('%B %d, %Y')

    # Enrich items with full account data from parsed_data
    if parsed_data:
        acct_lookup = {a['item_id']: a for a in parsed_data.get('accounts', [])}
        for block in analyst_report['violation_theory_blocks']:
            for item in block['items_affected']:
                item['_full_account'] = acct_lookup.get(item['item_id'], {})

    has_fraud = any(b['theory_id'] == 'identity_theft_documented'
                    for b in analyst_report['violation_theory_blocks'])
    theory_ids = [b['theory_id'] for b in analyst_report['violation_theory_blocks']]

    # Build all sections
    header = [
        date_str,
        '',
        consumer_name,
        consumer_address,
        '',
        bureau['name'],
        bureau['address'],
        '',
        'Re: Formal Dispute of Information — Request for Reinvestigation',
        '',
        f'Dear {bureau["name"]},',
        '',
        'I am writing to formally dispute information on my credit report under the Fair Credit '
        'Reporting Act. I have reviewed my report and identified specific items that I believe are '
        'inaccurate, unverifiable, or otherwise do not meet the standards required by federal law.',
        '',
        '=' * 60,
        '',
    ]

    sections = [
        '\n'.join(header),
        _build_section_1_audit(analyst_report),
        _build_section_2_statutory_basis(theory_ids),
        _build_section_3_consumer_position(analyst_report, has_fraud),
        _build_section_4_theory_blocks(analyst_report),
        _build_section_5_requests(analyst_report),
        _build_section_6_demand(analyst_report),
        _build_section_7_disclaimers(analyst_report, has_fraud),
    ]

    # Closing
    closing = [
        'Sincerely,',
        '',
        consumer_name,
    ]

    body = '\n'.join(sections) + '\n'.join(closing)

    # Item count for metadata
    seen = set()
    for block in analyst_report['violation_theory_blocks']:
        for item in block['items_affected']:
            seen.add(item['item_id'])

    return {
        'recipient_name': bureau['name'],
        'recipient_address': bureau['address'],
        'bureau_key': bureau_key,
        'subject': f'Formal Dispute — {len(seen)} Items — {consumer_name}',
        'body': body,
        'item_count': len(seen),
        'theory_count': len(analyst_report['violation_theory_blocks']),
        'framework': 'fcra',
        'date': date_str,
    }


def generate_collector_letter(
    analyst_report: dict,
    consumer_name: str,
    consumer_address: str,
    collector_name: str,
    collector_address: str,
) -> dict:
    """Generate a collector letter (FDCPA track) — parallel structure."""
    date_str = datetime.now().strftime('%B %d, %Y')

    # Filter to validation_failure theory only
    val_blocks = [b for b in analyst_report['violation_theory_blocks']
                  if b['theory_id'] == 'validation_failure']
    if not val_blocks:
        return None

    items = val_blocks[0]['items_affected']

    header = f"""{date_str}

{consumer_name}
{consumer_address}

{collector_name}
{collector_address}

Re: Dispute and Request for Debt Validation

Dear {collector_name},

I am writing to dispute the following account(s) and request validation of the debt(s) under the Fair Debt Collection Practices Act.

"""

    # Section 1 — items
    audit = 'ACCOUNT(S) IN DISPUTE:\n\n'
    for item in items:
        audit += f'  Account Name: {item.get("account_name", "")}\n'
        if item.get('account_number'):
            audit += f'  Account Number: {item["account_number"]}\n'
        if item.get('current_balance'):
            audit += f'  Reported Balance: {item["current_balance"]}\n'
        audit += '\n'

    # Section 2 — statutory basis
    statutory = 'STATUTORY BASIS:\n\n'
    for statute in get_verified_statutes('validation_failure'):
        statutory += f'  - {statute["short"]}: {statute["obligation"]}\n'
    statutory += '\n'

    # Section 3 — position
    position = """CONSUMER STATEMENT:

I do not acknowledge this debt. I am exercising my right under 15 U.S.C. § 1692g(b) to request validation. Please cease all collection activity until you have provided the validation requested below.

"""

    # Section 4 — requests
    requests = """VALIDATION REQUESTS:

1. Provide the name and address of the original creditor
2. Provide the original account number with the original creditor
3. Provide a copy of the original signed agreement bearing my signature
4. Provide a complete payment history from the original creditor through to your acquisition
5. Provide documentation of the complete chain of title from original creditor to your company
6. Provide proof of your license to collect debts in my state
7. Cease all collection activity and credit bureau reporting until validation is provided per 15 U.S.C. § 1692g(b)

"""

    # Section 5 — demand
    escalation = get_escalation_paths('collector')
    demand = 'DEMAND:\n\n'
    demand += 'If you cannot provide the above validation within 30 days, I demand that you:\n'
    demand += '  - Cease all collection activity on this account\n'
    demand += '  - Request deletion of this account from all credit bureau reports\n'
    demand += '  - Confirm in writing that collection has ceased\n\n'
    if escalation:
        demand += 'If these demands are not met, I intend to pursue:\n'
        for path in escalation:
            demand += f'  - {path}\n'
        demand += '\n'

    # Section 6 — disclaimers
    disclaimers = """DISCLAIMERS:

- This letter is not an acknowledgment of the debt
- This letter is my personal correspondence exercising rights under federal and state law
- I am retaining copies of this letter for my records

"""

    closing = f'Sincerely,\n\n{consumer_name}'

    body = header + audit + statutory + position + requests + demand + disclaimers + closing

    return {
        'recipient_name': collector_name,
        'recipient_address': collector_address,
        'subject': f'Debt Validation Request — {consumer_name}',
        'body': body,
        'item_count': len(items),
        'theory_count': 1,
        'framework': 'fdcpa',
        'date': date_str,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SANITIZATION
# ═══════════════════════════════════════════════════════════════════════════════

import re as _re

_BRANDING_PATTERNS = [
    _re.compile(r'AE[\s.-]*CC[\s.-]*\d+', _re.IGNORECASE),
    _re.compile(r'AE[\s.-]*Labs', _re.IGNORECASE),
    _re.compile(r'Arden\s*Edge', _re.IGNORECASE),
    _re.compile(r'BitmojiGuy', _re.IGNORECASE),
    _re.compile(r'CreditFix', _re.IGNORECASE),
    _re.compile(r'Credit\s*Tool', _re.IGNORECASE),
    _re.compile(r'AE-\d{8}-\w+'),  # confirmation codes
]


def sanitize_letter(letter: dict) -> dict:
    """Scan letter body for internal branding and block if found."""
    body = letter.get('body', '')
    violations = []
    for pattern in _BRANDING_PATTERNS:
        matches = pattern.findall(body)
        if matches:
            violations.extend(matches)

    if violations:
        raise ValueError(
            f'SANITIZATION FAILURE: Letter contains internal branding: {violations}. '
            f'Letter blocked from output.'
        )

    return letter


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from .parsing_engine import parse_report
    from .analyst import analyze

    filepath = r'C:\Users\sgill\Downloads\Annual Credit Report - Experian.html'
    filename = 'Annual Credit Report - Experian.html'

    # Parse
    parsed = parse_report(filepath, filename, consumer_name='Sean Gilmore')

    # Mock affirmations
    affirmations = {}
    for acct in parsed['accounts']:
        s = (acct.get('status') or '').lower()
        if any(kw in s for kw in ['collection', 'charge off']):
            affirmations[acct['item_id']] = {
                'not_recognized': True,
                'uncertain_chain': True,
                'no_validation_received': True,
            }

    # Analyze
    report = analyze(parsed, affirmations, state_code='TX')

    # Generate
    letter = generate_bureau_letter(
        analyst_report=report,
        consumer_name='Sean Gilmore',
        consumer_address='123 Main St\nDallas, TX 75201',
        bureau_key='experian',
        parsed_data=parsed,
    )

    # Sanitize
    letter = sanitize_letter(letter)

    print(f'Subject: {letter["subject"]}')
    print(f'To: {letter["recipient_name"]}')
    print(f'Items: {letter["item_count"]}, Theories: {letter["theory_count"]}')
    print(f'Framework: {letter["framework"]}')
    print(f'Length: {len(letter["body"])} chars')
    print()
    print('=' * 70)
    print(letter['body'])
    print('=' * 70)
