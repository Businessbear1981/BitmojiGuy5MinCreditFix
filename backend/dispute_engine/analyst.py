"""
Analyst Layer v4 — maps parsed items to violation theories.

Rules:
- Items without consumer-affirmed grounds receive no treatment
- Items fit multiple theories only when each genuinely applies
- Analyst does not invent theory applicability
- Items within 90 days of natural fall-off are flagged for exclusion

── Why v4 stopped re-deriving what the parser already knows ────────────────

The parser reads the file. It returns every dispute category one tradeline
supports, each with a strength and the evidence it rests on — a delinquency
date that precedes the account's own opening date, a reporting window that
has already closed, an account the bureau itself labels as purchased debt.

This module used to derive the same conclusions a second time, from the same
fields, with a second set of rules. Two derivations of one set of facts do
not check each other; they disagree. A file where the parser found three
grounds produced a letter arguing one, because the matchers only fired where
a consumer affirmation happened to line up. The parser's reading was thrown
away.

So the split is now by *who is in a position to know the fact*:

  file-derived theories — improper chain, re-aging, obsolescence
      These turn on fields the report states outright. Where the parser has
      already read them (`item['categories']` is present) its verdict stands
      and the matchers are skipped, because a second derivation can only
      duplicate it or contradict it. The matchers remain the whole story for
      items the parser never touched: anything from Claude or the keyword
      scanner, which carry no `categories`.

  consumer-derived theories — address, mixed file, identity theft,
                              validation failure, duplicate
      These turn on assertions only the consumer can make, or on structure
      only visible across items. The parser sees none of it, so the matchers
      always run and merge into the same per-item theory map.

identity_theft_documented is never inferred from a category. It carries a
§ 605B blocking claim the consumer has to actually make, and stays gated on
an explicit affirmation no matter what the file looks like.
"""

from datetime import datetime, timedelta

from .legal_library import VIOLATION_THEORIES, get_state_law

try:
    import scoring
except ImportError:  # letters must still build if the scorer is unavailable
    scoring = None

# Known debt buyer / collection entity list
DEBT_BUYER_ENTITIES = {
    'PORTFOLIO RECOVERY', 'MIDLAND CREDIT', 'LVNV FUNDING', 'ENCORE CAPITAL',
    'CAVALRY', 'IC SYSTEM', 'CONVERGENT', 'TRANSWORLD', 'ERC', 'ENHANCED RECOVERY',
    'UNIFIN', 'AFNI', 'CREDIT ACCEPTANCE',
}


# ── Parser category → violation theory ──────────────────────────────────────
# Only the categories where the theory says what the evidence says. A category
# with no entry here is not argued as a theory at all — it is still disputed,
# as an accuracy claim in Section 4B and again in the multiple-grounds close,
# which is the honest place for it.
#
# Deliberately absent, and why:
#   charge_off / late_payment  a charge-off that is reported accurately is
#       lawful to report. The dispute is with the marker's verifiability, not
#       with the furnisher's authority or the clock — no theory covers that.
#   balance_inaccuracy  a missing credit limit is a data-quality failure, not
#       duplicate or inconsistent *reporting* in the sense the theory means.
#   student_loan / repossession / foreclosure / bankruptcy  these name what
#       the account is, not what is wrong with it.
#   identity_theft  never inferred; see _match_identity_theft.
PARSER_CATEGORY_THEORIES = {
    # The bureau's own label says the reporting entity bought the debt rather
    # than extending the credit, which is the premise the chain theory argues.
    'debt_buyer': 'improper_chain_of_ownership',
    'collection': 'improper_chain_of_ownership',

    # Dates that contradict each other, and windows that have run.
    're_aging': 're_aging',
    'obsolete': 'obsolescence',

    # Identity and file-integrity findings.
    'duplicate': 'duplicate_inconsistent_reporting',
    'mixed_file': 'mixed_file_indicators',
    'identity_error': 'mixed_file_indicators',
    'deceased_indicator': 'mixed_file_indicators',
    'personal_info': 'address_inaccuracy',
}

# What a matcher-derived theory is worth when there is no parser category to
# price. `scoring` keys its priors by (category, strength), so a theory that
# came from an affirmation rather than from the file still needs a pair to
# look up. These mirror the trigger conditions of the matchers below: the
# obsolescence matcher only fires once the window has actually closed, so it
# scores as `strong`; validation failure rests on the consumer's word alone,
# so it scores as an ordinary collection.
THEORY_DEFAULT_GROUND = {
    'improper_chain_of_ownership': ('improper_chain_of_ownership', 'strong'),
    'address_inaccuracy': ('personal_info', 'moderate'),
    're_aging': ('re_aging', 'moderate'),
    'obsolescence': ('obsolete', 'strong'),
    'validation_failure': ('collection', 'moderate'),
    'duplicate_inconsistent_reporting': ('duplicate', 'moderate'),
    'mixed_file_indicators': ('mixed_file_indicators', 'strong'),
    'identity_theft_documented': ('identity_error', 'strong'),
}

# Theories the parser derives from the file itself. When an item arrives with
# parser categories, these matchers are skipped for that item — see the module
# docstring.
FILE_DERIVED_THEORIES = frozenset({
    'improper_chain_of_ownership', 're_aging', 'obsolescence',
})

# ── Categories that only *sometimes* carry a theory ─────────────────────────
# These name a marker on the account — a charge-off, a late, a balance, a
# status, a student loan. The marker itself is lawful to report if it is
# true, so there is no theory in the marker's existence. There is a theory
# when the evidence says the file contradicts itself about it: a balance that
# equals the past-due amount with no payment history that would produce that,
# a status that disagrees between one place and another. That is inconsistent
# reporting, and the duplicate/inconsistent theory is where it belongs.
#
# Where the evidence is merely "this is reported and should be verified", the
# item is left uncovered on purpose. compose.py's Section 4B disputes it as a
# plain accuracy claim, which is the honest framing — dressing a routine
# verification request up as a violation theory would overstate the letter.
CONDITIONAL_CATEGORY_THEORY = {
    'status_inaccuracy': 'duplicate_inconsistent_reporting',
    'balance_inaccuracy': 'duplicate_inconsistent_reporting',
    'late_payment': 'duplicate_inconsistent_reporting',
    'charge_off': 'duplicate_inconsistent_reporting',
    'student_loan': 'duplicate_inconsistent_reporting',
}

# Phrases the parser uses when its evidence is about two facts in the file
# disagreeing, rather than about one fact simply being present. Matched
# against the evidence string the parser wrote, because the parser is the
# only thing that knows which of the two it found.
_INCONSISTENCY_MARKERS = (
    'inconsist', 'contradict', 'conflict', 'discrepan', 'disagree',
    'cannot both', 'both reported as', 'does not match', 'differs from',
    'no payment history explaining', 'precedes',
)


def _reads_as_inconsistency(evidence: str) -> bool:
    """
    Does this evidence string describe two facts that disagree?

    The distinction decides whether a marker category becomes a violation
    theory or stays an ordinary accuracy dispute, so it is deliberately
    conservative: absent an explicit contradiction in the parser's own words,
    the answer is no and the item goes to Section 4B.
    """
    ev = (evidence or '').lower()
    return any(marker in ev for marker in _INCONSISTENCY_MARKERS)


def _theory_for_category(cat: dict):
    """The violation theory one parser category supports, or None."""
    name = cat.get('category', '')
    if name in PARSER_CATEGORY_THEORIES:
        return PARSER_CATEGORY_THEORIES[name]
    if (name in CONDITIONAL_CATEGORY_THEORY
            and _reads_as_inconsistency(cat.get('evidence', ''))):
        return CONDITIONAL_CATEGORY_THEORY[name]
    return None


def _theories_from_categories(account: dict) -> list:
    """
    Turn the parser's reading of one tradeline into violation theories.

    One account commonly supports several: a purchased debt whose delinquency
    date precedes its own opening date is both a chain-of-ownership problem
    and a re-aging problem, and they are independent — the furnisher can
    answer one and still lose the other. Several categories may also land on
    the same theory, in which case they merge into one theory carrying both
    pieces of evidence rather than arguing the same point twice.

    Each returned entry keeps the `grounds` that produced it so the block can
    later be priced by `scoring` against the same categories the parser used.
    """
    by_theory = {}
    for cat in account.get('categories') or []:
        tid = _theory_for_category(cat)
        if not tid:
            continue  # no theory fits; Section 4B disputes it as accuracy
        entry = by_theory.setdefault(
            tid, {'theory_id': tid, 'item_id': account['item_id'],
                  'factual_notes': [], 'grounds': []})
        entry['grounds'].append({
            'category': cat.get('category', ''),
            'strength': cat.get('strength', 'moderate'),
            'evidence': cat.get('evidence', ''),
        })
        evidence = (cat.get('evidence') or '').strip()
        if evidence:
            label = cat.get('category', '').replace('_', ' ').title()
            entry['factual_notes'].append(f'{label} ({cat.get("strength", "")}): {evidence}')
    return list(by_theory.values())


def _default_grounds(theory_id: str) -> list:
    """
    A scoreable ground for a theory that came from a matcher, not the file.

    `scoring` prices a (category, strength) pair, so a theory raised on a
    consumer affirmation still needs one to be comparable with a theory the
    parser found. THEORY_DEFAULT_GROUND mirrors each matcher's own trigger
    condition; anything unmapped is priced as a moderate ground of its own
    name so it sorts somewhere sane instead of vanishing.
    """
    category, strength = THEORY_DEFAULT_GROUND.get(theory_id, (theory_id, 'moderate'))
    return [{'category': category, 'strength': strength, 'evidence': ''}]


def _score_theory_block(entries: list, bureau: str) -> dict:
    """
    Price one violation theory using only the grounds that produced it.

    Scored per item and reduced by taking the strongest, because a theory
    block is an argument, and an argument is as good as its best instance —
    combining across items would answer "will at least one of these come
    off", which is a different question and would let a theory look strong
    purely for appearing on many accounts.

    Returns an empty dict when the scorer is unavailable, so a missing
    optional module degrades the ordering rather than the letter.
    """
    if scoring is None:
        return {}

    best_p, best_band, best_grounds = 0.0, '', []
    for entry in entries:
        grounds = entry.get('grounds') or _default_grounds(entry['theory_id'])
        scored = scoring.score_item({'categories': grounds}, bureau)
        entry['p_removed'] = scored['p_removed']
        entry['band'] = scored['band']
        entry['grounds_scored'] = scored['grounds']
        if scored['p_removed'] >= best_p:
            best_p = scored['p_removed']
            best_band = scored['band']
            best_grounds = scored['grounds']

    return {
        'p_removed': best_p,
        'band': best_band,
        'grounds': best_grounds,
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

        # ── Theories for this item ───────────────────────────────────────────
        # The parser's reading comes first, then the matchers cover what the
        # parser cannot see. Both merge into one map keyed by theory, so an
        # item the parser read as re-aged and the consumer also flagged as a
        # mixed file argues both, instead of whichever ran last.
        has_parser_view = bool(acct.get('categories'))
        per_theory = {e['theory_id']: e for e in _theories_from_categories(acct)}

        for matcher in matchers:
            result = matcher(acct, consumer_affirmations)
            if not result:
                continue
            tid = result['theory_id']
            # The parser already read these three straight off the file. A
            # second derivation from the same fields can only repeat its
            # verdict or disagree with it, and disagreeing is how a file with
            # three grounds ended up arguing one.
            if has_parser_view and tid in FILE_DERIVED_THEORIES:
                continue
            entry = per_theory.setdefault(
                tid, {'theory_id': tid, 'item_id': item_id,
                      'factual_notes': [], 'grounds': []})
            entry['factual_notes'].extend(result['factual_notes'])
            # A matcher hit is a ground in its own right and has to be priced,
            # whether it opened the theory or joined one the parser opened.
            # Deduped by category so a matcher agreeing with the parser about
            # the same fact does not get counted as a second independent
            # ground — that is precisely the inflation the dampener exists to
            # prevent, and it is cheaper to not create it here.
            for ground in _default_grounds(tid):
                if not any(g['category'] == ground['category']
                           for g in entry['grounds']):
                    entry['grounds'].append(ground)

        for tid, entry in per_theory.items():
            entry['account'] = acct
            theory_groups.setdefault(tid, []).append(entry)

        item_matched_theories = list(per_theory.keys())

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

    # ── Build violation theory blocks for the report ─────────────────────────
    # Scored first, ordered afterwards: the letter should lead with the
    # argument most likely to remove something, not with the one that happens
    # to touch the most accounts. Count only breaks ties.
    bureau = parsed_data.get('file_metadata', {}).get('bureau', 'unknown')

    violation_theory_blocks = []
    for tid, items_in_theory in theory_groups.items():
        theory_def = VIOLATION_THEORIES.get(tid, {})

        # Common factual pattern across items
        all_notes = [n for item in items_in_theory for n in item['factual_notes']]
        common = _find_common_pattern(all_notes)

        # Prices every item in the block and stamps p_removed/band onto each
        # entry as a side effect, so the per-item numbers below are populated.
        block_score = _score_theory_block(items_in_theory, bureau)

        block = {
            'theory_id': tid,
            'title': theory_def.get('title', tid),
            'description': theory_def.get('description', ''),
            # What this argument is worth, from the same priors the review
            # screen ranks items with — one number, one basis, everywhere.
            'p_removed': block_score.get('p_removed', 0.0),
            'band': block_score.get('band', ''),
            'grounds': block_score.get('grounds', []),
            'items_affected': [
                {
                    'item_id': item['item_id'],
                    'account_name': item['account'].get('account_name', ''),
                    'account_number': item['account'].get('account_number', ''),
                    'current_balance': item['account'].get('current_balance', ''),
                    'status': item['account'].get('status', ''),
                    'per_item_notes': item['factual_notes'],
                    'p_removed': item.get('p_removed', 0.0),
                    'band': item.get('band', ''),
                    'grounds': item.get('grounds_scored', []),
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

    # Descending removal likelihood; item count breaks ties so a theory that
    # covers four accounts outranks an equally-priced one covering a single
    # account. theory_order is derived from the blocks rather than sorted
    # separately, so the two can never disagree about the running order.
    violation_theory_blocks.sort(
        key=lambda b: (b.get('p_removed', 0.0), len(b['items_affected'])),
        reverse=True,
    )
    theory_order = [b['theory_id'] for b in violation_theory_blocks]

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
