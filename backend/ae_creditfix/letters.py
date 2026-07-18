"""
Letter engine — generates dispute letter text fully in memory.

Nothing is written to disk here: plaintext letters contain PII and are stored
only in the encrypted `letters` column of the case record (ADR-0002).
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from .case import Case, Item, Letter, new_id
from .templates import BUREAU_ADDRESSES, BUREAU_BODY, COVER_SHEET, CREDITOR_BODY, FCRA, HEADER


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def make_items_block(items: List[Item]) -> str:
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


def _header(case: Case) -> str:
    c = case.client
    return HEADER.format(
        name=c.name, address=c.address, phone=c.phone, email=c.email,
        dob=c.dob, ssn_last4=c.ssn_last4, today=today_str(),
    )


def gen_bureau_letters(case: Case) -> List[Tuple[str, str, str]]:
    """Returns [(letter_id, bureau, letter_text)] — one letter per bureau."""
    groups: dict[str, List[Item]] = {}
    for it in case.items:
        if it.type == "bureau" and it.status == "open":
            groups.setdefault(it.target, []).append(it)

    created = []
    for bureau, items in groups.items():
        ltr_id = new_id("LTR")
        body = _header(case) + "\n" + BUREAU_BODY.format(
            name=case.client.name, target=bureau,
            items_block=make_items_block(items),
            cit_609=FCRA["609"], cit_611=FCRA["611"],
        )
        body += f"\n\nMail to: {bureau} — {BUREAU_ADDRESSES.get(bureau, '(address TBD)')}"
        case.letters.append(Letter(
            id=ltr_id, type="bureau", target=bureau, path="",
            date=today_str(), item_ids=[i.id for i in items],
        ))
        for it in items:
            it.letters.append(ltr_id)
        created.append((ltr_id, bureau, body))
    return created


def gen_creditor_letters(case: Case) -> List[Tuple[str, str, str]]:
    """Returns [(letter_id, creditor, letter_text)] — one letter per creditor item."""
    created = []
    for it in case.items:
        if it.type == "creditor" and it.status == "open":
            ltr_id = new_id("LTR")
            body = _header(case) + "\n" + CREDITOR_BODY.format(
                name=case.client.name, target=it.target,
                account=it.account or "N/A", reason=it.reason or "N/A",
                cit_623=FCRA["623"],
            )
            case.letters.append(Letter(
                id=ltr_id, type="creditor", target=it.target, path="",
                date=today_str(), item_ids=[it.id],
            ))
            it.letters.append(ltr_id)
            created.append((ltr_id, it.target, body))
    return created


def gen_cover_sheet(case: Case) -> str:
    """Returns the cover sheet text."""
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
