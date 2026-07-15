"""
Parsing Engine v3 — Faithful extraction of credit bureau reports.

Rules:
- Capture every reported field, even if redundant or inconsistent
- Flag data quality issues but do not correct them
- Cross-bureau reconciliation happens at the analyst layer, not here
- Parser's job is faithful capture of what the bureau reported
"""

import re
import hashlib
from datetime import datetime, date
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODEL — normalized output structures
# ═══════════════════════════════════════════════════════════════════════════════

def empty_consumer_profile():
    return {
        'primary_name': '',
        'name_variants': [],
        'primary_address': '',
        'address_history': [],
        'phone_numbers': [],
        'employers': [],
        'spouse_or_co_applicant': '',
        'year_of_birth': '',
    }


def empty_file_metadata():
    return {
        'report_date': '',
        'report_number': '',
        'bureau': '',
        'raw_text_length': 0,
    }


def empty_account():
    return {
        'item_id': '',
        'bureau': '',
        'account_name': '',
        'account_number': '',
        'account_type': '',
        'responsibility': '',
        'interest_type': '',
        'date_opened': '',
        'status': '',
        'status_updated_date': '',
        'current_balance': '',
        'balance_updated_date': '',
        'recent_payment': '',
        'monthly_payment': '',
        'credit_limit_or_original_balance': '',
        'highest_balance': '',
        'terms': '',
        'on_record_until_date': '',
        'date_of_first_delinquency': '',
        'payment_history': [],
        'balance_history': [],
        'furnisher_address': '',
        'furnisher_phone': '',
        'comments': [],
        'reinvestigation_history': [],
        'original_creditor': '',
        'company_sold_to': '',
        'dispute_status_indicators': [],
        'data_quality_flags': [],
    }


def empty_inquiry():
    return {
        'inquiry_type': '',
        'inquiring_entity': '',
        'inquiry_date': '',
        'on_record_until_date': '',
        'inquiry_address': '',
        'on_behalf_of': '',
    }


def empty_public_record():
    return {
        'type': '',
        'date': '',
        'amount': '',
        'status': '',
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_text_from_file(filepath: str, filename: str) -> str:
    """Extract text from a file. Supports PDF, HTML, TXT, CSV, DOCX."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if ext == 'pdf':
        return _extract_pdf(filepath)
    elif ext in ('html', 'htm'):
        return _extract_html(filepath)
    elif ext in ('txt', 'csv'):
        return _extract_text(filepath)
    elif ext == 'docx':
        return _extract_docx(filepath)
    else:
        # Try as text
        return _extract_text(filepath)


def _extract_pdf(filepath: str) -> str:
    try:
        import pdfplumber
        text = ''
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages[:50]:
                t = page.extract_text()
                if t:
                    text += t + '\n'
        return text
    except Exception as e:
        print(f'[PARSE] PDF extraction error: {e}')
        return ''


def _extract_html(filepath: str) -> str:
    try:
        from bs4 import BeautifulSoup
        with open(filepath, 'r', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        print(f'[PARSE] HTML extraction error: {e}')
        return ''


def _extract_text(filepath: str) -> str:
    try:
        with open(filepath, 'r', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f'[PARSE] Text extraction error: {e}')
        return ''


def _extract_docx(filepath: str) -> str:
    try:
        from docx import Document
        doc = Document(filepath)
        return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        print(f'[PARSE] DOCX extraction error: {e}')
        return ''


# ═══════════════════════════════════════════════════════════════════════════════
# BUREAU DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def detect_bureau(text: str) -> str:
    """Detect which bureau issued the report."""
    text_lower = text[:5000].lower()
    if 'experian' in text_lower:
        return 'experian'
    if 'equifax' in text_lower:
        return 'equifax'
    if 'transunion' in text_lower or 'trans union' in text_lower:
        return 'transunion'
    return 'unknown'


# ═══════════════════════════════════════════════════════════════════════════════
# CONSUMER PROFILE EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_consumer_profile(text: str, consumer_name: str = '') -> dict:
    """Extract consumer profile information from report text."""
    profile = empty_consumer_profile()

    # Names — look for "Names" section or reported name variants
    name_section = re.search(
        r'(?:Names?|Also Known As|AKA|Name Variations?)[\s:]*\n?((?:[A-Z][A-Z\s,.\'-]+\n?){1,10})',
        text, re.IGNORECASE
    )
    if name_section:
        names = [n.strip() for n in name_section.group(1).strip().split('\n') if n.strip() and len(n.strip()) > 2]
        if names:
            profile['primary_name'] = names[0]
            profile['name_variants'] = names

    if not profile['primary_name'] and consumer_name:
        profile['primary_name'] = consumer_name

    # Addresses
    addr_blocks = re.findall(
        r'(\d+\s+[A-Z][A-Za-z\s]+(?:ST|AVE|BLVD|DR|RD|CT|LN|WAY|PL|CIR|PKWY)[.,]?\s*(?:#\s*\w+\s*)?[A-Z]{2}\s+\d{5}(?:-\d{4})?)',
        text
    )
    if addr_blocks:
        profile['primary_address'] = addr_blocks[0]
        for addr in addr_blocks:
            entry = {'address': addr, 'data_quality_flags': []}
            # Flag potential typos — very short street names, unusual patterns
            if len(addr.split()[1]) <= 2:
                entry['data_quality_flags'].append('possible_truncation')
            profile['address_history'].append(entry)

    # Phone numbers
    phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text[:3000])
    profile['phone_numbers'] = list(set(phones))

    # Employers
    emp_section = re.search(r'(?:Employers?|Employment)[\s:]*\n?((?:[A-Z][A-Za-z\s&.,]+\n?){1,5})', text, re.IGNORECASE)
    if emp_section:
        profile['employers'] = [e.strip() for e in emp_section.group(1).strip().split('\n') if e.strip()]

    # Year of birth
    yob = re.search(r'(?:Year of Birth|DOB|Born|Date of Birth)[\s:]*(\d{4})', text, re.IGNORECASE)
    if yob:
        profile['year_of_birth'] = yob.group(1)

    # Data quality: flag name variants that look like misspellings
    if profile['primary_name']:
        primary_upper = profile['primary_name'].upper()
        for variant in profile['name_variants'][1:]:
            if _is_likely_misspelling(primary_upper, variant.upper()):
                profile.setdefault('data_quality_flags', []).append(
                    f'name_variant_possible_misspelling: "{variant}" vs primary "{profile["primary_name"]}"'
                )

    return profile


def _is_likely_misspelling(name1: str, name2: str) -> bool:
    """Check if two names differ by 1-2 characters (likely misspelling vs. alias)."""
    if name1 == name2:
        return False
    # Simple edit distance check
    if abs(len(name1) - len(name2)) > 2:
        return False
    diffs = sum(1 for a, b in zip(name1, name2) if a != b)
    diffs += abs(len(name1) - len(name2))
    return 1 <= diffs <= 2


# ═══════════════════════════════════════════════════════════════════════════════
# ACCOUNT EXTRACTION — the core parser
# ═══════════════════════════════════════════════════════════════════════════════

# Known creditors / furnishers for entity recognition
KNOWN_ENTITIES = [
    'CAPITAL ONE', 'CHASE', 'JPMORGAN', 'BANK OF AMERICA', 'WELLS FARGO',
    'CITIBANK', 'CITI', 'DISCOVER', 'AMERICAN EXPRESS', 'AMEX', 'SYNCHRONY',
    'BARCLAYS', 'US BANK', 'PNC', 'TD BANK', 'ALLY', 'NAVIENT', 'SALLIE MAE',
    'PORTFOLIO RECOVERY', 'MIDLAND CREDIT', 'LVNV FUNDING', 'ENCORE CAPITAL',
    'CAVALRY', 'IC SYSTEM', 'CONVERGENT', 'TRANSWORLD', 'ERC', 'ENHANCED RECOVERY',
    'UNIFIN', 'AFNI', 'CREDIT ACCEPTANCE', 'WESTLAKE', 'SANTANDER',
    'REGIONAL ACCEPTANCE', 'SPRINGLEAF', 'ONEMAIN', 'LENDING CLUB', 'PROSPER',
    'UPSTART', 'SOFI', 'AVANT', 'BEST BUY', 'TARGET', 'WALMART', 'AMAZON',
    'PAYPAL', 'KLARNA', 'AFFIRM', 'AFTERPAY', 'CARE CREDIT',
]

# Known debt buyers / collection agencies
KNOWN_DEBT_BUYERS = [
    'PORTFOLIO RECOVERY', 'MIDLAND CREDIT', 'LVNV FUNDING', 'ENCORE CAPITAL',
    'CAVALRY', 'IC SYSTEM', 'CONVERGENT', 'TRANSWORLD', 'ERC', 'ENHANCED RECOVERY',
    'UNIFIN', 'AFNI', 'CREDIT ACCEPTANCE',
]

# Field extraction patterns
FIELD_PATTERNS = {
    'account_number': re.compile(r'(?:Account\s*(?:Number|#|No))[:\s]*([A-Z0-9*xX]{4,20})', re.IGNORECASE),
    'account_type': re.compile(r'(?:Account\s*Type|Type)[:\s]*([\w\s]{3,40}?)(?:\n|$)', re.IGNORECASE),
    'responsibility': re.compile(r'(?:Responsibility|Owner)[:\s]*([\w\s]{3,30}?)(?:\n|$)', re.IGNORECASE),
    'date_opened': re.compile(r'(?:Date\s*Opened|Opened)[:\s]*(\d{1,2}/\d{2,4})', re.IGNORECASE),
    'status': re.compile(r'(?:(?:Account\s*)?Status|Condition)[:\s]*([\w\s,.]{3,60}?)(?:\n|$)', re.IGNORECASE),
    'status_updated_date': re.compile(r'(?:Status\s*Updated|Updated)[:\s]*(\w+\s+\d{4}|\d{1,2}/\d{2,4})', re.IGNORECASE),
    'current_balance': re.compile(r'(?:Balance|Current\s*Balance)[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
    'balance_updated_date': re.compile(r'(?:Balance\s*Updated)[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})', re.IGNORECASE),
    'credit_limit': re.compile(r'(?:Credit\s*Limit|Original\s*(?:Balance|Amount)|Limit)[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
    'highest_balance': re.compile(r'(?:Highest\s*Balance|High\s*Balance)[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
    'monthly_payment': re.compile(r'(?:Monthly\s*Payment|Payment\s*Amount)[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
    'recent_payment': re.compile(r'(?:Recent\s*Payment|Last\s*Payment)[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
    'terms': re.compile(r'(?:Terms)[:\s]*([\w\s]{3,30}?)(?:\n|$)', re.IGNORECASE),
    'past_due': re.compile(r'(?:Past\s*Due|Amount\s*Past\s*Due)[:\s]*\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
    'original_creditor': re.compile(r'(?:Original\s*Creditor|Orig\.?\s*Creditor)[:\s]*([\w\s&.,\'-]{3,50}?)(?:\n|$)', re.IGNORECASE),
    'on_record_until': re.compile(r'(?:On\s*Record\s*Until|Estimated\s*removal|Remove\s*date)[:\s]*(\w+\s+\d{4}|\d{1,2}/\d{2,4})', re.IGNORECASE),
    'dofd': re.compile(r'(?:Date\s*of\s*First\s*Delinquency|First\s*Delinq|DOFD)[:\s]*(\d{1,2}/\d{2,4})', re.IGNORECASE),
}

# Status keywords for classification
STATUS_KEYWORDS = {
    'collection': re.compile(r'collect(?:ion|ed|ions)', re.IGNORECASE),
    'charge_off': re.compile(r'charge[\s-]*off', re.IGNORECASE),
    'late_payment': re.compile(r'(?:30|60|90|120)\s*days?\s*(?:late|past\s*due)|late\s+payment|delinquen', re.IGNORECASE),
    'repossession': re.compile(r'repos(?:s)?ess', re.IGNORECASE),
    'foreclosure': re.compile(r'foreclos', re.IGNORECASE),
    'bankruptcy': re.compile(r'bankrupt', re.IGNORECASE),
    'judgment': re.compile(r'judg(?:e)?ment', re.IGNORECASE),
    'settled': re.compile(r'settled?\s+(?:for\s+)?less', re.IGNORECASE),
    'paid': re.compile(r'paid\s*(?:in\s*full|as\s*agreed|closed)', re.IGNORECASE),
    'open': re.compile(r'(?:^|\s)open(?:\s|$)', re.IGNORECASE),
    'closed': re.compile(r'(?:^|\s)closed(?:\s|$)', re.IGNORECASE),
}

# Payment history status codes
PAYMENT_CODES = {
    'OK': 'Current', 'C': 'Current', '1': 'Current',
    '30': '30 days late', '2': '30 days late',
    '60': '60 days late', '3': '60 days late',
    '90': '90 days late', '4': '90 days late',
    '120': '120 days late', '5': '120+ days late',
    'CO': 'Charge-off', '9': 'Charge-off',
    'FC': 'Foreclosure', 'RP': 'Repossession',
    'CL': 'Collection',
}


def extract_accounts(text: str, bureau: str) -> list:
    """
    Extract all accounts from report text.
    Uses a block-splitting approach: split on known entity names,
    then extract fields from each block.
    """
    accounts = []

    # Build entity regex
    entity_pattern = '|'.join(re.escape(e) for e in KNOWN_ENTITIES)
    entity_re = re.compile(f'({entity_pattern})', re.IGNORECASE)

    # Split text into blocks per entity mention
    parts = entity_re.split(text)

    # parts = [preamble, entity1, block1, entity2, block2, ...]
    i = 1
    seen_keys = set()
    while i < len(parts) - 1:
        entity_name = parts[i].strip().title()
        block = parts[i + 1][:2000]  # limit context per account

        acct = empty_account()
        acct['bureau'] = bureau
        acct['account_name'] = entity_name

        # Extract each field
        for field_name, pattern in FIELD_PATTERNS.items():
            m = pattern.search(block)
            if m:
                value = m.group(1).strip()
                if field_name == 'account_number':
                    acct['account_number'] = value
                elif field_name == 'account_type':
                    acct['account_type'] = value
                elif field_name == 'responsibility':
                    acct['responsibility'] = value
                elif field_name == 'date_opened':
                    acct['date_opened'] = value
                elif field_name == 'status':
                    acct['status'] = value
                elif field_name == 'status_updated_date':
                    acct['status_updated_date'] = value
                elif field_name == 'current_balance':
                    acct['current_balance'] = f'${value}'
                elif field_name == 'balance_updated_date':
                    acct['balance_updated_date'] = value
                elif field_name == 'credit_limit':
                    acct['credit_limit_or_original_balance'] = f'${value}'
                elif field_name == 'highest_balance':
                    acct['highest_balance'] = f'${value}'
                elif field_name == 'monthly_payment':
                    acct['monthly_payment'] = f'${value}'
                elif field_name == 'recent_payment':
                    acct['recent_payment'] = f'${value}'
                elif field_name == 'terms':
                    acct['terms'] = value
                elif field_name == 'past_due':
                    if not acct['current_balance']:
                        acct['current_balance'] = f'${value}'
                elif field_name == 'original_creditor':
                    acct['original_creditor'] = value
                elif field_name == 'on_record_until':
                    acct['on_record_until_date'] = value
                elif field_name == 'dofd':
                    acct['date_of_first_delinquency'] = value

        # Classify status from keywords in block
        for status_key, status_re in STATUS_KEYWORDS.items():
            if status_re.search(block):
                if not acct['status'] or status_key in ('collection', 'charge_off', 'repossession', 'foreclosure'):
                    acct['status'] = status_key.replace('_', ' ').title()
                break

        # Check if this is a debt buyer
        entity_upper = entity_name.upper()
        if any(db in entity_upper for db in KNOWN_DEBT_BUYERS):
            if not acct['account_type'] or acct['account_type'].lower() in ('', 'unsecured'):
                acct['account_type'] = 'Debt Buyer / Collection'

        # Comments — look for dispute indicators, reinvestigation notes
        dispute_indicators = re.findall(
            r'((?:dispute|disputed|consumer\s+(?:states|disputes)|meets\s+requirement|updated\s+from).{0,100})',
            block, re.IGNORECASE
        )
        acct['dispute_status_indicators'] = [d.strip()[:120] for d in dispute_indicators]

        reinvestigation = re.findall(
            r'((?:reinvestigat|processing\s+of\s+your\s+dispute|updated\s+from\s+our).{0,100})',
            block, re.IGNORECASE
        )
        acct['reinvestigation_history'] = [r.strip()[:120] for r in reinvestigation]

        comments = re.findall(
            r'(?:Comment|Remark|Note)[:\s]*(.*?)(?:\n|$)',
            block, re.IGNORECASE
        )
        acct['comments'] = [c.strip()[:200] for c in comments if c.strip()]

        # Payment history — look for month-by-month grid
        pay_hist = re.findall(
            r'(?:OK|30|60|90|120|CO|CL|FC|RP|C|--|\*)',
            block[:500]
        )
        if len(pay_hist) >= 6:
            acct['payment_history'] = pay_hist[:48]  # up to 4 years

        # Generate stable item_id
        id_source = f"{entity_name}|{acct['account_number']}|{bureau}"
        acct['item_id'] = hashlib.md5(id_source.encode()).hexdigest()[:12]

        # Data quality flags
        if acct['date_opened'] and acct['date_of_first_delinquency']:
            opened = _parse_date(acct['date_opened'])
            dofd = _parse_date(acct['date_of_first_delinquency'])
            if opened and dofd and opened > dofd:
                acct['data_quality_flags'].append('date_opened_after_dofd')

        if acct['current_balance'] and acct['current_balance'] == acct.get('highest_balance'):
            acct['data_quality_flags'].append('balance_equals_highest_no_reduction')

        # Deduplicate by entity + account number
        dedup_key = f"{entity_name}|{acct['account_number']}"
        if dedup_key not in seen_keys:
            seen_keys.add(dedup_key)
            accounts.append(acct)

        i += 2

    return accounts


# ═══════════════════════════════════════════════════════════════════════════════
# INQUIRY EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_inquiries(text: str) -> list:
    """Extract hard and soft inquiries from report text."""
    inquiries = []

    # Look for inquiry section
    inq_section = re.search(
        r'(?:Hard\s*Inquiries|Inquiries\s*that\s*may\s*affect|Regular\s*Inquiries)([\s\S]{0,5000})(?:Soft|Promotional|End\s*of)',
        text, re.IGNORECASE
    )
    if not inq_section:
        return inquiries

    section_text = inq_section.group(1)

    # Extract individual inquiries
    inq_matches = re.findall(
        r'([A-Z][A-Za-z\s&.,\'-]{3,40})\s+(\d{1,2}/\d{1,2}/\d{2,4})',
        section_text
    )
    for entity, date_str in inq_matches:
        inq = empty_inquiry()
        inq['inquiry_type'] = 'hard'
        inq['inquiring_entity'] = entity.strip()
        inq['inquiry_date'] = date_str
        inquiries.append(inq)

    return inquiries


# ═══════════════════════════════════════════════════════════════════════════════
# DATE PARSING UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_date(date_str: str) -> Optional[datetime]:
    """Try to parse a date string in common credit report formats."""
    for fmt in ('%m/%d/%Y', '%m/%d/%y', '%m/%Y', '%m/%y', '%Y-%m-%d', '%B %Y', '%b %Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PARSE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def parse_report(filepath: str, filename: str, consumer_name: str = '') -> dict:
    """
    Parse a credit bureau report file into the normalized data model.

    Returns:
    {
        'consumer_profile': {...},
        'file_metadata': {...},
        'accounts': [...],
        'inquiries': [...],
        'public_records': [...],
        'data_quality_flags': [...],
    }
    """
    text = extract_text_from_file(filepath, filename)
    if not text:
        return {
            'consumer_profile': empty_consumer_profile(),
            'file_metadata': empty_file_metadata(),
            'accounts': [],
            'inquiries': [],
            'public_records': [],
            'data_quality_flags': ['extraction_failed'],
        }

    bureau = detect_bureau(text)
    profile = extract_consumer_profile(text, consumer_name)
    accounts = extract_accounts(text, bureau)
    inquiries = extract_inquiries(text)

    metadata = empty_file_metadata()
    metadata['bureau'] = bureau
    metadata['raw_text_length'] = len(text)

    # Report date
    rd = re.search(r'(?:Report\s*(?:Date|Generated)|Date\s*of\s*Report)[:\s]*(\d{1,2}/\d{1,2}/\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})', text, re.IGNORECASE)
    if rd:
        metadata['report_date'] = rd.group(1)

    # Report number
    rn = re.search(r'(?:Report\s*(?:Number|#|No))[:\s]*(\d[\w-]+)', text, re.IGNORECASE)
    if rn:
        metadata['report_number'] = rn.group(1)

    # File-level data quality flags
    file_flags = []
    if len(accounts) == 0 and len(text) > 1000:
        file_flags.append('no_accounts_extracted_from_substantial_text')
    if bureau == 'unknown':
        file_flags.append('bureau_not_detected')
    if not profile['primary_name'] and not consumer_name:
        file_flags.append('no_consumer_name_detected')

    # Profile-level flags
    file_flags.extend(profile.get('data_quality_flags', []))

    return {
        'consumer_profile': profile,
        'file_metadata': metadata,
        'accounts': accounts,
        'inquiries': inquiries,
        'public_records': [],  # TODO: public record extraction
        'data_quality_flags': file_flags,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    import json

    filepath = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\sgill\Downloads\Annual Credit Report - Experian.html'
    filename = filepath.rsplit('\\', 1)[-1] if '\\' in filepath else filepath.rsplit('/', 1)[-1]

    result = parse_report(filepath, filename, consumer_name='Sean Gilmore')

    print(f'Bureau: {result["file_metadata"]["bureau"]}')
    print(f'Report date: {result["file_metadata"]["report_date"]}')
    print(f'Text length: {result["file_metadata"]["raw_text_length"]}')
    print(f'Consumer: {result["consumer_profile"]["primary_name"]}')
    print(f'Name variants: {result["consumer_profile"]["name_variants"]}')
    print(f'Addresses: {len(result["consumer_profile"]["address_history"])}')
    print(f'Accounts: {len(result["accounts"])}')
    print(f'Inquiries: {len(result["inquiries"])}')
    print(f'File flags: {result["data_quality_flags"]}')
    print()

    for acct in result['accounts'][:10]:
        print(f'  [{acct["item_id"]}] {acct["account_name"]} | {acct["account_number"]} | {acct["status"]} | {acct["current_balance"]} | type={acct["account_type"]} | opened={acct["date_opened"]} | dofd={acct["date_of_first_delinquency"]} | orig={acct["original_creditor"]}')
        if acct['data_quality_flags']:
            print(f'    FLAGS: {acct["data_quality_flags"]}')
        if acct['dispute_status_indicators']:
            print(f'    DISPUTE: {acct["dispute_status_indicators"][:2]}')

    if len(result['accounts']) > 10:
        print(f'  ... and {len(result["accounts"]) - 10} more')
