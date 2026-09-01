"""
Adapter — FastAPI case model in, dispute-engine model out.

The engine was written against a richer parsed-report structure than the
FastAPI backend carries. Rather than reshape the engine (which is the part
worth protecting), this module translates in one place.

Two directions:
    to_parsed_data()   case items         -> engine `parsed_data`
    to_affirmations()  case items         -> engine `consumer_affirmations`
    from_letters()     engine letter dict -> the app's letter dict
"""
from __future__ import annotations

import re
from typing import Any

from .categories import DISPUTE_CATEGORIES, affirmations_for, guess_category

# Which bureau a target string refers to, when it refers to one at all.
_BUREAU_ALIASES = {
    "experian": "Experian",
    "equifax": "Equifax",
    "transunion": "TransUnion",
    "trans union": "TransUnion",
    "tu": "TransUnion",
    "exp": "Experian",
    "eqf": "Equifax",
}

BUREAUS = ("Experian", "Equifax", "TransUnion")

# The letter generator keys its address book in lowercase; the rest of the app
# (mail_service, the frontend, the PDF) uses the display name. Translate here
# so neither side has to know about the other.
BUREAU_KEYS = {"Experian": "experian", "Equifax": "equifax", "TransUnion": "transunion"}


def bureau_key(display_name: str) -> str:
    """Display bureau name -> letter_generator's address-book key."""
    return BUREAU_KEYS.get(display_name, (display_name or "").strip().lower())


def normalize_bureau(target: str) -> str | None:
    """Map a free-text target onto a canonical bureau name, or None."""
    key = (target or "").strip().lower()
    if not key:
        return None
    if key in _BUREAU_ALIASES:
        return _BUREAU_ALIASES[key]
    for alias, canonical in _BUREAU_ALIASES.items():
        if alias in key:
            return canonical
    return None


def _status_for(item: dict) -> str:
    """
    Synthesise the status string the matchers read.

    `_is_negative()` and `_is_debt_buyer()` both key off status text, so the
    category has to be reflected there or nothing fires.
    """
    category = item.get("bucket") or item.get("category") or ""
    label = DISPUTE_CATEGORIES.get(category, {}).get("label", "")
    reason = item.get("reason", "")
    return f"{label} {reason}".strip()


def _account_type_for(item: dict) -> str:
    category = item.get("bucket") or item.get("category") or ""
    if category in ("collection", "debt_buyer", "medical_debt", "rental_eviction"):
        return "COLLECTION"
    if category in ("bankruptcy", "judgment_lien", "child_support"):
        return "PUBLIC RECORD"
    if category == "inquiry":
        return "INQUIRY"
    return DISPUTE_CATEGORIES.get(category, {}).get("label", "").upper()


_MONEY = re.compile(r"[^0-9.\-]")


def _money(value: Any) -> str:
    """Engine expects balances as strings; keep them parseable."""
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    cleaned = _MONEY.sub("", str(value))
    return cleaned or ""


def to_parsed_data(
    items: list[dict],
    client: dict,
    bureau: str = "",
    data_quality_flags: list[str] | None = None,
) -> dict:
    """
    Build the engine's `parsed_data` from case items.

    `items` are the dicts the report parser produces: bucket, type, target,
    account, amount, opened, reason, confidence.
    """
    accounts = []
    for idx, item in enumerate(items):
        item_id = item.get("id") or f"ITEM{idx + 1:03d}"
        category = item.get("bucket") or item.get("category") or guess_category(item.get("reason", ""))

        accounts.append({
            "item_id": item_id,
            # Prefer the furnisher when the parser distinguished it — the
            # letter must name who reports the debt, not who we mail.
            "account_name": item.get("furnisher") or item.get("target") or "Unknown",
            "account_number": item.get("account") or "",
            "account_type": _account_type_for({**item, "bucket": category}),
            "original_creditor": item.get("original_creditor") or "",
            "reported_to": item.get("target") or "",
            "current_balance": _money(item.get("amount")),
            "highest_balance": _money(item.get("highest_balance")),
            "status": _status_for({**item, "bucket": category}),
            "date_opened": item.get("opened") or "",
            "date_of_first_delinquency": item.get("dofd") or item.get("opened") or "",
            "date_reported": item.get("reported") or "",
            "category": category,
            # Every ground the parser found on this tradeline, not just the
            # strongest. The analyst argues one theory per ground, so dropping
            # this field here silently collapsed a three-ground item into a
            # one-theory letter — the field is the whole reason the analyst can
            # stop re-deriving what the parser already read off the file.
            "categories": [dict(c) for c in (item.get("categories") or [])],
            "category_count": item.get("category_count")
                              or len(item.get("categories") or []),
            # The parser's own falloff verdict, carried so the analyst does not
            # have to recompute the seven-year window from a re-parsed date.
            "falloff_status": item.get("falloff_status") or "",
            "severity": DISPUTE_CATEGORIES.get(category, {}).get("severity", 3),
            "description": item.get("reason") or "",
        })

    return {
        "file_metadata": {
            "bureau": bureau or "unknown",
            "item_count": len(accounts),
        },
        "consumer_profile": {
            "primary_name": client.get("name", ""),
            "current_address": client.get("address", ""),
            "data_quality_flags": list(data_quality_flags or []),
        },
        "accounts": accounts,
        "data_quality_flags": list(data_quality_flags or []),
    }


def to_affirmations(
    items: list[dict],
    consumer_input: dict[str, dict] | None = None,
) -> dict[str, dict]:
    """
    Build `consumer_affirmations` keyed by item_id.

    Where the consumer answered the review questions, use their answers. Where
    they did not, fall back to the affirmations the item's category implies —
    an item the consumer selected as "not my account" already carries its own
    assertion, and re-asking would be theatre.

    Nothing here invents a fraud claim: `confirmed_fraud` is only ever set from
    explicit consumer input, because it carries legal weight the consumer has
    to actually make.
    """
    consumer_input = consumer_input or {}
    out: dict[str, dict] = {}

    for idx, item in enumerate(items):
        item_id = item.get("id") or f"ITEM{idx + 1:03d}"
        category = item.get("bucket") or item.get("category") or ""
        given = dict(consumer_input.get(item_id, {}))

        aff: dict[str, Any] = {
            "not_recognized": False,
            "confirmed_fraud": False,
            "uncertain_chain": False,
            "address_mismatch": False,
            "dofd_uncertain": False,
            "dates_inconsistent": False,
            "name_not_mine": False,
            "no_validation_received": False,
            "ftc_report_number": "",
            "exclude": False,
        }

        # Category-implied defaults, minus anything that must be asserted.
        for key in affirmations_for(category):
            if key in aff and key not in ("confirmed_fraud", "ftc_report_number"):
                aff[key] = True

        # Explicit consumer input always wins.
        aff.update({k: v for k, v in given.items() if k in aff})
        out[item_id] = aff

    return out


def from_letter(engine_letter: dict, target: str, letter_type: str = "bureau") -> dict:
    """
    Convert an engine letter into the shape the rest of the app already speaks
    (`target` / `text` / `tier`), so mail_service, pdf_gen and the frontend
    need no changes.
    """
    return {
        "target": target,
        "type": letter_type,
        "text": engine_letter.get("body", ""),
        "subject": engine_letter.get("subject", ""),
        "tier": engine_letter.get("tier", 1),
        "tier_name": engine_letter.get("tier_name", ""),
        "postage": engine_letter.get("postage", {}),
        "item_count": engine_letter.get("item_count", 0),
        "theory_count": engine_letter.get("theory_count", 0),
        "recipient_address": engine_letter.get("recipient_address", ""),
        "date": engine_letter.get("date", ""),
    }
