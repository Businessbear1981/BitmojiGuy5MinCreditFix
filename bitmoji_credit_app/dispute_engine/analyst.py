"""
Analyst Layer v3 — maps parsed items to violation theories.

Rules:
- Items without consumer-affirmed grounds receive no treatment
- Items fit multiple theories only when each genuinely applies
- Analyst does not invent theory applicability
- Items within 90 days of natural fall-off are flagged for exclusion
"""

from datetime import datetime, timedelta
from .legal_library import VIOLATION_THEORIES, get_state_law

# Known debt buyer / collection entity list
DEBT_BUYER_ENTITIES = {
    'PORTFOLIO RECOVERY', 'MIDLAND CREDIT', 'LVNV FUNDING', 'ENCORE CAPITAL',
    'CAVALRY', 'IC SYSTEM', 'CONVERGENT', 'TRANSWORLD', 'ERC', 'ENHANCED RECOVERY',
    'UNIFIN', 'AFNI', 'CREDIT ACCEPTANCE',
}


def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ('%m/%d/%Y', '%m/%d/%y', '%m/%Y', '%m/%y', '%Y-%m-%d', '%B %Y', '%b %Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def _is_debt_buyer(account):
    name = (account.get('account_name') or '').upper()
    atype = (account.get('account_type') or '').upper()
    return any(db in name for db in DEBT_BUYER_ENTITIES) or 'DEBT BUYER' in atype or 'COLLECTION' in atype


def _is_negative(account):
    status = (account.get('status') or '').lower()
    negative_keywords = ['collection', 'charge off', 'charge_off', 'late', 'delinqu',
                         'repossess', 'foreclos', 'bankrupt', 'judgment', 'settled']
    return any(kw in status for kw in negative_keywords)


def _days_until_falloff(account):
    dofd = _parse_date(account.get('date_of_first_delinquency'))
    if not dofd:
        return None
    falloff = dofd + timedelta(days=7 * 365.25)
    remaining = (falloff - datetime.now()).days
    return remaining


# ═══════════════════════════════════════════════════════════════════════════════
# VIOLATION THEORY MATCHERS
# ═══════════════════════════════════════════════════════════════════════════════

def _match_improper_chain(account, consumer_affirmations):
    """Triggers: debt buyer/collection AND original creditor != account name."""
    if not _is_debt_buyer(account):
        return None
    aff = consumer_affirmations.get(account['item_id'], {})
    if not aff.get('not_recognized') and not aff.get('uncertain_chain'):
        return None
    notes = []
    if account.get('original_creditor'):
        notes.append(f'Original creditor: {account["original_creditor"]}; reporting entity: {account["account_name"]}')
    if account.get('current_balance') and account.get('highest_balance') and account['current_balance'] == account['highest_balance']:
        notes.append('Balance has not decreased from highest — static reporting pattern')
    return {
        'theory_id': 'improper_chain_of_ownership',
        'item_id': account['item_id'],
        'factual_notes': notes,
    }


def _match_address_inaccuracy(account, consumer_profile, consumer_affirmations):
    """Triggers: data quality flags on addresses OR consumer-affirmed mismatch."""
    aff = consumer_affirmations.get(account['item_id'], {})
    profile_flags = [f for f in consumer_profile.get('data_quality_flags', []) if 'address' in f.lower() or 'name' in f.lower()]

    if not aff.get('address_mismatch') and not profile_flags:
        return None

    notes = []
    if aff.get('address_mismatch'):
        notes.append('Consumer affirms address attached to account does not match verifiable address history')
    for flag in profile_flags:
        notes.append(f'File-level flag: {flag}')
    return {
        'theory_id': 'address_inaccuracy',
        'item_id': account['item_id'],
        'factual_notes': notes,
    }


def _match_re_aging(account, consumer_affirmations):
    """Triggers: DOFD inconsistency or consumer uncertainty about reported dates."""
    aff = consumer_affirmations.get(account['item_id'], {})
    flags = account.get('data_quality_flags', [])

    has_date_flag = any('date' in f.lower() for f in flags)
    has_dofd_concern = aff.get('dofd_uncertain') or aff.get('dates_inconsistent')

    if not has_date_flag and not has_dofd_concern:
        return None

    notes = []
    if has_date_flag:
        notes.append(f'Data quality flags: {[f for f in flags if "date" in f.lower()]}')
    if _is_debt_buyer(account):
        notes.append('Account has been transferred to debt buyer — potential re-aging at transfer')
    if aff.get('dofd_uncertain'):
        notes.append('Consumer expresses uncertainty about the reported date of first delinquency')
    return {
        'theory_id': 're_aging',
        'item_id': account['item_id'],
        'factual_notes': notes,
    }


def _match_obsolescence(account):
    """Triggers: DOFD + 7 years has passed."""
    days = _days_until_falloff(account)
    if days is None:
        return None
    if days <= 0:
        return {
            'theory_id': 'obsolescence',
            'item_id': account['item_id'],
            'factual_notes': [f'Item is {abs(days)} days past the 7-year reporting window'],
        }
    return None


def _match_duplicate(account, all_accounts):
    """Triggers: same underlying account appears multiple times."""
    dupes = [a for a in all_accounts
             if a['item_id'] != account['item_id']
             and a['account_name'].upper() == account['account_name'].upper()
             and a.get('account_number') and a['account_number'] == account.get('account_number')]
    if not dupes:
        return None
    return {
        'theory_id': 'duplicate_inconsistent_reporting',
        'item_id': account['item_id'],
        'factual_notes': [f'Duplicate entry found: same account name and number reported {len(dupes) + 1} times'],
    }


def _match_mixed_file(account, consumer_profile, consumer_affirmations):
    """Triggers: name variants or addresses consumer says aren't theirs."""
    aff = consumer_affirmations.get(account['item_id'], {})
    profile_flags = [f for f in consumer_profile.get('data_quality_flags', []) if 'name_variant' in f.lower()]

    if not aff.get('name_not_mine') and not profile_flags:
        return None

    notes = []
    if aff.get('name_not_mine'):
        notes.append('Consumer affirms a name variant on this account does not belong to them')
    for flag in profile_flags:
        notes.append(f'File-level flag: {flag}')
    return {
        'theory_id': 'mixed_file_indicators',
        'item_id': account['item_id'],
        'factual_notes': notes,
    }


def _match_identity_theft(account, consumer_affirmations):
    """Triggers: consumer has affirmed certainty of identity theft."""
    aff = consumer_affirmations.get(account['item_id'], {})
    if not aff.get('confirmed_fraud'):
        return None
    notes = ['Consumer has affirmed certainty of identity theft for this account']
    if aff.get('ftc_report_number'):
        notes.append(f'FTC report number: {aff["ftc_report_number"]}')
    return {
        'theory_id': 'identity_theft_documented',
        'item_id': account['item_id'],
        'factual_notes': notes,
    }


def _match_validation_failure(account, consumer_affirmations):
    """Triggers: collection/debt buyer AND consumer never received validation."""
    if not _is_debt_buyer(account):
        return None
    aff = consumer_affirmations.get(account['item_id'], {})
    if not aff.get('no_validation_received'):
        return None
    return {
        'theory_id': 'validation_failure',
        'item_id': account['item_id'],
        'factual_notes': ['Consumer affirms no validation was ever received from current collector'],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYST FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def analyze(
    parsed_data: dict,
    consumer_affirmations: dict,
    state_code: str = '',
) -> dict:
    """
    Produce analyst report from parsed data + consumer affirmations.

    consumer_affirmations: dict mapping item_id → {
        'not_recognized': bool,
        'confirmed_fraud': bool,
        'uncertain_chain': bool,
        'address_mismatch': bool,
        'dofd_uncertain': bool,
        'dates_inconsistent': bool,
        'name_not_mine': bool,
        'no_validation_received': bool,
        'ftc_report_number': str,
        'exclude': bool,  # consumer explicitly wants to skip
    }

    Returns analyst report dict.
    """
    accounts = parsed_data.get('accounts', [])
    profile = parsed_data.get('consumer_profile', {})

    # ── Run all matchers against all affirmed accounts ────────────────────────
    theory_groups = {}  # theory_id → list of {item_id, factual_notes}
    item_theories = {}  # item_id → list of theory_ids

    matchers = [
        lambda a, aff: _match_improper_chain(a, aff),
        lambda a, aff: _match_address_inaccuracy(a, profile, aff),
        lambda a, aff: _match_re_aging(a, aff),
        lambda a, aff: _match_obsolescence(a),
        lambda a, aff: _match_duplicate(a, accounts),
        lambda a, aff: _match_mixed_file(a, profile, aff),
        lambda a, aff: _match_identity_theft(a, aff),
        lambda a, aff: _match_validation_failure(a, aff),
    ]

    excluded_items = []
    included_items = []

    for acct in accounts:
        item_id = acct['item_id']
        aff = consumer_affirmations.get(item_id, {})

        # ── Exclusion logic ──────────────────────────────────────────────────
        # No affirmation at all → exclude
        if not aff:
            excluded_items.append({
                'item_id': item_id,
                'account_name': acct['account_name'],
                'reason': 'no_consumer_affirmation',
            })
            continue

        # Consumer explicitly wants to skip
        if aff.get('exclude'):
            excluded_items.append({
                'item_id': item_id,
                'account_name': acct['account_name'],
                'reason': 'consumer_excluded',
            })
            continue

        # Falls off naturally within 90 days
        days = _days_until_falloff(acct)
        if days is not None and 0 < days <= 90:
            excluded_items.append({
                'item_id': item_id,
                'account_name': acct['account_name'],
                'reason': f'natural_falloff_in_{days}_days',
            })
            continue

        # ── Match theories ───────────────────────────────────────────────────
        item_matched_theories = []
        for matcher in matchers:
            result = matcher(acct, consumer_affirmations)
            if result:
                tid = result['theory_id']
                if tid not in theory_groups:
                    theory_groups[tid] = []
                theory_groups[tid].append({
                    'item_id': item_id,
                    'account': acct,
                    'factual_notes': result['factual_notes'],
                })
                item_matched_theories.append(tid)

        if item_matched_theories:
            item_theories[item_id] = item_matched_theories
            included_items.append(acct)
        else:
            # Has affirmation but no theory matched
            excluded_items.append({
                'item_id': item_id,
                'account_name': acct['account_name'],
                'reason': 'no_matching_violation_theory',
            })

    # ── Multi-theory items ───────────────────────────────────────────────────
    multi_theory_items = {
        item_id: theories
        for item_id, theories in item_theories.items()
        if len(theories) >= 2
    }

    # ── Furnisher pattern indicators ─────────────────────────────────────────
    furnisher_counts = {}
    for acct in included_items:
        name = acct['account_name']
        furnisher_counts[name] = furnisher_counts.get(name, 0) + 1
    furnisher_patterns = {
        name: count for name, count in furnisher_counts.items() if count >= 2
    }

    # ── Recommended ordering ─────────────────────────────────────────────────
    # Strongest cumulative-weight theories first
    theory_order = sorted(
        theory_groups.keys(),
        key=lambda tid: len(theory_groups[tid]),
        reverse=True,
    )

    # ── Build violation theory blocks for the report ─────────────────────────
    violation_theory_blocks = []
    for tid in theory_order:
        theory_def = VIOLATION_THEORIES.get(tid, {})
        items_in_theory = theory_groups[tid]

        # Common factual pattern across items
        all_notes = [n for item in items_in_theory for n in item['factual_notes']]
        common = _find_common_pattern(all_notes)

        block = {
            'theory_id': tid,
            'title': theory_def.get('title', tid),
            'description': theory_def.get('description', ''),
            'items_affected': [
                {
                    'item_id': item['item_id'],
                    'account_name': item['account'].get('account_name', ''),
                    'account_number': item['account'].get('account_number', ''),
                    'current_balance': item['account'].get('current_balance', ''),
                    'status': item['account'].get('status', ''),
                    'per_item_notes': item['factual_notes'],
                }
                for item in items_in_theory
            ],
            'common_factual_pattern': common,
            'supporting_data_quality': [
                f for f in parsed_data.get('data_quality_flags', [])
                if any(keyword in f.lower() for keyword in ('address', 'name', 'date', 'truncat'))
            ],
        }
        violation_theory_blocks.append(block)

    # ── State law ────────────────────────────────────────────────────────────
    state_law = get_state_law(state_code)

    return {
        'bureau': parsed_data.get('file_metadata', {}).get('bureau', 'unknown'),
        'consumer_name': profile.get('primary_name', ''),
        'violation_theory_blocks': violation_theory_blocks,
        'multi_theory_items': multi_theory_items,
        'furnisher_patterns': furnisher_patterns,
        'excluded_items': excluded_items,
        'included_item_count': len(included_items),
        'total_account_count': len(accounts),
        'theory_order': theory_order,
        'state_code': state_code,
        'state_law': state_law,
    }


def _find_common_pattern(notes: list) -> str:
    """Find the most common factual pattern across notes."""
    if not notes:
        return ''
    # Simple: return the most frequent note
    from collections import Counter
    counter = Counter(notes)
    most_common = counter.most_common(1)
    if most_common:
        return most_common[0][0]
    return ''


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from .parsing_engine import parse_report
    import json

    filepath = r'C:\Users\sgill\Downloads\Annual Credit Report - Experian.html'
    filename = 'Annual Credit Report - Experian.html'

    parsed = parse_report(filepath, filename, consumer_name='Sean Gilmore')

    # Mock consumer affirmations — affirm non-recognition on all negative items
    affirmations = {}
    for acct in parsed['accounts']:
        if acct['status'] and any(kw in acct['status'].lower() for kw in ['collection', 'charge off', 'charge_off']):
            affirmations[acct['item_id']] = {
                'not_recognized': True,
                'uncertain_chain': True,
                'no_validation_received': True,
            }

    report = analyze(parsed, affirmations, state_code='TX')

    print(f'Bureau: {report["bureau"]}')
    print(f'Included: {report["included_item_count"]} / {report["total_account_count"]} accounts')
    print(f'Excluded: {len(report["excluded_items"])}')
    print(f'Theories matched: {len(report["violation_theory_blocks"])}')
    print(f'Multi-theory items: {len(report["multi_theory_items"])}')
    print(f'Furnisher patterns: {report["furnisher_patterns"]}')
    print()

    for block in report['violation_theory_blocks']:
        print(f'  THEORY: {block["title"]}')
        print(f'  Items: {len(block["items_affected"])}')
        for item in block['items_affected']:
            print(f'    - {item["account_name"]} | {item["account_number"]} | {item["status"]} | {item["current_balance"]}')
            for note in item['per_item_notes']:
                print(f'      > {note}')
        print()
