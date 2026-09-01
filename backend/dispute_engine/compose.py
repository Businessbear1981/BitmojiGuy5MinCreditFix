"""
The merged letter generator — one entry point for the whole platform.

Two letter systems existed. This merges them rather than picking a winner:

  * The **theory engine** (analyst + legal_library + letter_generator) builds a
    seven-section argument around whichever violation theories the facts
    actually support. It is the strong path and it runs first.

  * The **category templates** (categories.py) cover every dispute type in the
    taxonomy, including the ones no theory matched — a wrong balance, a stray
    inquiry, a personal-information error. These become Section 4B of the same
    letter rather than a second mailing.

An item can therefore never fall through: it is argued by theory, or it is
argued by category, but it is always in the letter. Then `tiers.apply_tier()`
escalates the whole thing to whichever round the case is on.

    generate_case_letters(client, items, ...) -> list[letter dict]

is the only function the application layer needs.
"""
from __future__ import annotations

from datetime import datetime

from . import adapter, tiers
from .analyst import analyze
from .categories import DISPUTE_CATEGORIES, citations_for, get_category
from .letter_generator import (
    BUREAU_ADDRESSES,
    generate_bureau_letter,
    generate_collector_letter,
    sanitize_letter,
)

# ── Category fallback section ───────────────────────────────────────────────

def _category_section(items: list[dict], start_index: int = 0) -> str:
    """
    Build the argument for items no violation theory picked up.

    These are real disputes — an unauthorised inquiry or a missing credit limit
    is worth removing — they just do not need a case-law scaffold. Each gets
    its statutory anchor, the facts, and what is being asked for.
    """
    if not items:
        return ""

    lines = [
        "SECTION 4B — ADDITIONAL DISPUTED ITEMS",
        "",
        ("The following items are disputed on the accuracy grounds stated for each. "
        "Each is independent of the theories set out above."),
        "",
    ]

    for offset, item in enumerate(items):
        category_id = item.get("bucket") or item.get("category") or ""
        category = get_category(category_id)
        label = category.get("label", "Disputed Item")
        marker = f"4B.{start_index + offset + 1}"

        lines.append(f"{marker} — {label}")
        lines.append("")

        target = item.get("target") or "Unknown"
        account = item.get("account") or ""
        # When the target is the bureau itself (inquiries, personal info), the
        # item has no furnisher — saying "furnisher: TransUnion" would be wrong.
        if adapter.normalize_bureau(target):
            lines.append(f"  Appears on: {target}")
        else:
            lines.append(f"  Furnisher / entity: {target}")
        if account:
            lines.append(f"  Account reference: {account}")
        if item.get("amount") not in (None, ""):
            lines.append(f"  Amount reported: {item['amount']}")
        if item.get("opened"):
            lines.append(f"  Date shown: {item['opened']}")
        lines.append("")

        reason = item.get("reason") or "The information reported is inaccurate or incomplete."
        lines.append(f"  Basis of dispute: {reason}")
        lines.append("")

        citations = citations_for(category_id)
        if citations:
            lines.append("  Authority:")
            for citation in citations:
                lines.append(f"    - {citation}")
            lines.append("")

        note = category.get("note")
        if note:
            lines.append(f"  {note}")
            lines.append("")

        lines.append(
            "  Requested action: verify this information with the furnisher against "
            "documentation, and delete it if it cannot be verified as reported, per "
            "15 U.S.C. § 1681i(a)(5)(A)."
        )
        lines.append("")

    return "\n".join(lines)


def _splice_category_section(body: str, section: str) -> str:
    """Insert 4B immediately before Section 5 so the numbering reads correctly."""
    if not section:
        return body
    marker = "SECTION 5 — SPECIFIC REQUESTS"
    if marker in body:
        head, _, tail = body.partition(marker)
        return f"{head}{section}\n{marker}{tail}"
    return f"{body}\n{section}"


def _summary_close(items: list[dict]) -> str:
    """
    The closing section: which items are contested on several independent
    grounds, and what that means.

    This is the argument a reviewer makes to themselves anyway — "this one
    shows up three different ways, one of them is going to hold." Saying it
    plainly, item by item, does two things: it stops the bureau resolving the
    easiest ground and treating the item as settled, and it makes the letter
    read as a considered audit rather than a scattergun.
    """
    stacked = [i for i in items if len(i.get("categories") or []) >= 2]
    if not stacked:
        return ""

    stacked.sort(key=lambda i: -len(i["categories"]))

    lines = [
        "SECTION 9 — ITEMS CONTESTED ON MULTIPLE INDEPENDENT GROUNDS",
        "",
        ("Several of the items above are disputed for more than one reason. The "
        "grounds are independent of each other: each stands on its own, and any "
        "one of them, if correct, requires deletion or correction of the item."),
        "",
        ("I raise this because resolving the narrowest ground does not dispose of "
        "the others. An item contested on three grounds has not been reinvestigated "
        "until all three have been addressed."),
        "",
    ]

    for item in stacked:
        name = item.get("furnisher") or item.get("target") or "Account"
        acct = item.get("account") or ""
        cats = item["categories"]
        header = f"{name}" + (f" (Acct: {acct})" if acct else "")
        lines.append(f"  {header} — {len(cats)} independent grounds:")

        for n, c in enumerate(cats, 1):
            label = c["category"].replace("_", " ").title()
            lines.append(f"    ({n}) {label} — {c['evidence']}.")
        lines.append("")

    strong = sum(1 for i in stacked for c in i["categories"] if c["strength"] == "strong")
    if strong:
        lines.append(
            f"Of the grounds set out above, {strong} rest on a direct contradiction "
            f"within the file as you have furnished it — dates that cannot both be "
            f"correct, or a reporting period that has already run. Those require no "
            f"investigation beyond reading the record.")
        lines.append("")

    return "\n".join(lines)


# ── Coverage accounting ─────────────────────────────────────────────────────

def _theory_covered_ids(analyst_report: dict) -> set[str]:
    covered: set[str] = set()
    for block in analyst_report.get("violation_theory_blocks", []):
        for item in block.get("items_affected", []):
            covered.add(item["item_id"])
    return covered


# ── Main entry point ────────────────────────────────────────────────────────

def generate_case_letters(
    client: dict,
    items: list[dict],
    state_code: str = "",
    tier: int = 1,
    consumer_affirmations: dict[str, dict] | None = None,
    prior_rounds: dict[str, dict] | None = None,
) -> list[dict]:
    """
    Generate every letter this case needs, at the requested tier.

    client   {name, address, dob, ssn_last4, phone, email}
    items    the case's dispute items (report-parser shape)
    tier     1-4; see tiers.TIER_LADDER
    prior_rounds  {target: {tracking_number, sent_at, delivered_at, tier}}

    Returns a list of letter dicts in the app's own shape. One letter per
    bureau that has items, plus one per furnisher for direct § 623 disputes.
    """
    if not items:
        return []

    client = client or {}
    prior_rounds = prior_rounds or {}
    consumer_name = client.get("name", "")
    consumer_address = client.get("address", "")

    # Assign stable ids up front so affirmations and reports agree.
    for idx, item in enumerate(items):
        item.setdefault("id", f"ITEM{idx + 1:03d}")

    bureau_items = [i for i in items if (i.get("type") or "bureau") != "creditor"]
    creditor_items = [i for i in items if (i.get("type") or "bureau") == "creditor"]

    letters: list[dict] = []

    # ── Bureau letters: one per bureau, carrying every bureau-side item ──────
    # Items are disputed with all three bureaus unless the parser pinned one,
    # because an item is usually reported to more than one.
    for bureau in adapter.BUREAUS:
        targeted = [
            i for i in bureau_items
            if adapter.normalize_bureau(i.get("target", "")) in (None, bureau)
        ]
        if not targeted:
            continue

        parsed = adapter.to_parsed_data(targeted, client, bureau=bureau)
        affirmations = adapter.to_affirmations(targeted, consumer_affirmations)
        report = analyze(parsed, affirmations, state_code)

        covered = _theory_covered_ids(report)
        uncovered = [i for i in targeted if i["id"] not in covered]

        if not report.get("violation_theory_blocks") and not uncovered:
            continue

        if report.get("violation_theory_blocks"):
            engine_letter = generate_bureau_letter(
                report, consumer_name, consumer_address,
                adapter.bureau_key(bureau), parsed,
            )
        else:
            # No theory fired anywhere — build the shell and let 4B carry it.
            engine_letter = _shell_letter(bureau, consumer_name, consumer_address, report)

        engine_letter["body"] = _splice_category_section(
            engine_letter["body"], _category_section(uncovered)
        )
        close = _summary_close(targeted)
        if close:
            body = engine_letter["body"]
            marker = "SECTION 7 — DISCLAIMERS"
            if marker in body:
                head, _, tail = body.partition(marker)
                engine_letter["body"] = f"{head}{close}\n{marker}{tail}"
            else:
                engine_letter["body"] = f"{body}\n{close}"
        engine_letter["item_count"] = len(targeted)

        tiered = tiers.apply_tier(
            engine_letter,
            tier,
            report,
            state_code=state_code,
            prior_round=prior_rounds.get(bureau),
            recipient_type="bureau",
        )
        letters.append(adapter.from_letter(sanitize_letter(tiered), bureau, "bureau"))

    # ── Direct furnisher letters (§ 623) ────────────────────────────────────
    by_furnisher: dict[str, list[dict]] = {}
    for item in creditor_items:
        by_furnisher.setdefault(item.get("target") or "Unknown", []).append(item)

    for furnisher, group in by_furnisher.items():
        parsed = adapter.to_parsed_data(group, client, bureau=furnisher)
        affirmations = adapter.to_affirmations(group, consumer_affirmations)
        report = analyze(parsed, affirmations, state_code)

        covered = _theory_covered_ids(report)
        uncovered = [i for i in group if i["id"] not in covered]

        if report.get("violation_theory_blocks"):
            engine_letter = generate_collector_letter(
                report, consumer_name, consumer_address, furnisher, parsed
            )
        else:
            engine_letter = _shell_letter(furnisher, consumer_name, consumer_address, report,
                                          is_bureau=False)

        engine_letter["body"] = _splice_category_section(
            engine_letter["body"], _category_section(uncovered)
        )
        engine_letter["item_count"] = len(group)

        tiered = tiers.apply_tier(
            engine_letter,
            tier,
            report,
            state_code=state_code,
            prior_round=prior_rounds.get(furnisher),
            recipient_type="collector",
        )
        letters.append(adapter.from_letter(sanitize_letter(tiered), furnisher, "creditor"))

    return letters


def _shell_letter(
    target: str,
    consumer_name: str,
    consumer_address: str,
    report: dict,
    is_bureau: bool = True,
) -> dict:
    """
    Minimal letter frame for the case where no violation theory matched.

    The category section still has to be delivered on letterhead with a
    salutation and a signature, so build the frame here rather than skipping
    the item entirely.
    """
    date_str = datetime.now().strftime("%B %d, %Y")
    recipient = BUREAU_ADDRESSES.get(adapter.bureau_key(target), {})
    recipient_name = recipient.get("name", target)
    recipient_address = recipient.get("address", "")

    header = [
        date_str,
        "",
        consumer_name,
        consumer_address,
        "",
        recipient_name,
        recipient_address,
        "",
        "Re: Formal Dispute of Information — Request for Reinvestigation",
        "",
        f"Dear {recipient_name},",
        "",
        ("I am writing to formally dispute information appearing on my credit file "
        "under the Fair Credit Reporting Act. The items identified below are "
        "inaccurate, incomplete, or unverifiable as reported."),
        "",
        "=" * 60,
        "",
    ]

    return {
        "recipient_name": recipient_name,
        "recipient_address": recipient_address,
        "bureau_key": target if is_bureau else "",
        "subject": f"Formal Dispute — {consumer_name}",
        "body": "\n".join(header),
        "item_count": 0,
        "theory_count": 0,
        "framework": "fcra",
        "date": date_str,
    }


# ── Introspection for the admin panel ───────────────────────────────────────

def engine_manifest() -> dict:
    """What this engine can currently argue. Used by /api/admin/templates."""
    from .legal_library import VIOLATION_THEORIES

    return {
        "categories": len(DISPUTE_CATEGORIES),
        "theories": len(VIOLATION_THEORIES),
        "tiers": tiers.ladder_summary(),
        "category_list": [
            {"id": cid, "label": c["label"], "type": c["type"],
             "severity": c["severity"], "theories": c["theories"]}
            for cid, c in DISPUTE_CATEGORIES.items()
        ],
        "theory_list": [
            {"id": tid, "title": t.get("title", tid)}
            for tid, t in VIOLATION_THEORIES.items()
        ],
    }
