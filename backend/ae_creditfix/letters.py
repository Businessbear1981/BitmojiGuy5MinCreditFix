"""
Letter engine — the app's entry point into the merged dispute engine.

Everything substantive now lives in `dispute_engine/`: the violation theories,
the fifty-state authorities, the seven-section composer, the category
taxonomy, and the four-tier escalation ladder. This module is the seam
between that engine and the FastAPI case model, and it keeps the cover sheet.

Nothing is written to disk here: plaintext letters contain PII and are stored
only in the encrypted `letters` column of the case record (ADR-0002).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional, Tuple

from dispute_engine import generate_case_letters, tier_for_day

from .case import Case, Item, Letter, new_id
from .templates import BUREAU_ADDRESSES, COVER_SHEET

# "…, Austin, TX 78702" / "… TX 78702" — pull the two-letter state.
_STATE_RE = re.compile(r"\b([A-Z]{2})\b(?=[,\s]+\d{5}(?:-\d{4})?\s*$)")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def state_from_address(address: str) -> str:
    """
    Best-effort state code from a free-text mailing address.

    Used to select state-law authorities for tier 3. A miss is harmless — the
    letter simply omits the state-law section rather than guessing wrong.
    """
    if not address:
        return ""
    match = _STATE_RE.search(address.strip())
    if match:
        return match.group(1)
    # Fall back to a comma-separated component that is exactly two letters.
    for part in reversed([p.strip() for p in address.split(",")]):
        token = part.split()[0] if part else ""
        if len(token) == 2 and token.isalpha():
            return token.upper()
    return ""


def _client_dict(case: Case) -> dict:
    c = case.client
    return {
        "name": c.name, "address": c.address, "dob": c.dob,
        "ssn_last4": c.ssn_last4, "phone": c.phone, "email": c.email,
    }


def _open_items(case: Case) -> List[dict]:
    """Open items in the shape the engine's adapter expects."""
    out = []
    for it in case.items:
        if it.status != "open":
            continue
        out.append({
            "id": it.id,
            "bucket": getattr(it, "bucket", "") or "",
            "affirmations": getattr(it, "affirmations", {}) or {},
            "type": it.type,
            "target": it.target,
            "account": it.account,
            "amount": it.amount,
            "opened": it.opened,
            "reason": it.reason,
        })
    return out


def make_items_block(items: List[Item]) -> str:
    """Human-readable item list, used on the cover sheet."""
    lines = []
    for it in items:
        parts = [f"- {it.target} | {it.account or 'N/A'}"]
        if it.amount is not None:
            parts.append(f"${it.amount:.2f}")
        if it.opened:
            parts.append(f"opened {it.opened}")
        parts.append(f"reason: {it.reason or 'N/A'}")
        lines.append("  " + " | ".join(parts))
    return "\n".join(lines) if lines else "  (none)"


# ── Main generation ─────────────────────────────────────────────────────────

def gen_letters(
    case: Case,
    tier: int = 1,
    consumer_affirmations: Optional[dict] = None,
    prior_rounds: Optional[dict] = None,
) -> List[dict]:
    """
    Generate every letter this case needs at the given tier.

    Returns the app-shaped letter dicts (target / text / tier / postage …) and
    records a Letter stub on the case so item→letter linkage survives.
    """
    items = _open_items(case)
    if not items:
        return []

    state_code = state_from_address(case.client.address)

    # Per-item affirmations recorded at review time, overridden by anything
    # the caller passes explicitly.
    affirmations = {i["id"]: i["affirmations"] for i in items if i.get("affirmations")}
    affirmations.update(consumer_affirmations or {})

    letters = generate_case_letters(
        client=_client_dict(case),
        items=items,
        state_code=state_code,
        tier=tier,
        consumer_affirmations=affirmations,
        prior_rounds=prior_rounds,
    )

    # Link letters back onto the case so the cover sheet and the item log agree.
    by_target: dict[str, list[str]] = {}
    for it in case.items:
        if it.status == "open":
            by_target.setdefault(it.target, []).append(it.id)

    for ltr in letters:
        ltr_id = new_id("LTR")
        ltr["id"] = ltr_id
        item_ids = by_target.get(ltr["target"], [i["id"] for i in items])
        case.letters.append(Letter(
            id=ltr_id, type=ltr.get("type", "bureau"), target=ltr["target"],
            path="", date=today_str(), item_ids=item_ids,
        ))
        for it in case.items:
            if it.id in item_ids:
                it.letters.append(ltr_id)

    return letters


def gen_followup_letters(case: Case, days_since_dispatch: int, prior_rounds: Optional[dict] = None) -> List[dict]:
    """Generate the round that is due at this point in the case."""
    return gen_letters(case, tier=tier_for_day(days_since_dispatch), prior_rounds=prior_rounds)


# ── Backwards-compatible shims ──────────────────────────────────────────────
# main.py and the tests still call these. They now return tier-1 output from
# the merged engine rather than the old two-template stub.

def gen_bureau_letters(case: Case) -> List[Tuple[str, str, str]]:
    """[(letter_id, bureau, letter_text)] — bureau-directed letters only."""
    return [
        (ltr["id"], ltr["target"], ltr["text"])
        for ltr in gen_letters(case, tier=1)
        if ltr.get("type", "bureau") == "bureau"
    ]


def gen_creditor_letters(case: Case) -> List[Tuple[str, str, str]]:
    """[(letter_id, furnisher, letter_text)] — direct § 623 letters only."""
    return [
        (ltr["id"], ltr["target"], ltr["text"])
        for ltr in gen_letters(case, tier=1)
        if ltr.get("type") == "creditor"
    ]


def gen_cover_sheet(case: Case) -> str:
    """The binder front page."""
    c = case.client
    p2 = sum(1 for it in case.items if it.type == "bureau" and it.status == "open")
    p3 = sum(1 for it in case.items if it.type == "creditor" and it.status == "open")
    return COVER_SHEET.format(
        name=c.name, dob=c.dob, ssn_last4=c.ssn_last4, phone=c.phone,
        email=c.email, address=c.address, today=today_str(),
        p1="Yes" if case.phases.get("p1_docs_complete") else "No",
        p2_count=p2, p3_count=p3, p4="Pending",
        attachments=", ".join(case.attachments) or "(none)",
    )


__all__ = [
    "gen_letters", "gen_followup_letters", "gen_bureau_letters",
    "gen_creditor_letters", "gen_cover_sheet", "make_items_block",
    "state_from_address", "today_str", "BUREAU_ADDRESSES",
]
