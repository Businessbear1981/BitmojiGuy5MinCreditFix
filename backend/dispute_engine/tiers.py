"""
The tiered escalation ladder.

A dispute is not one letter, it is a sequence. Each tier does something the
previous tier earned the right to do: you cannot demand a method of
verification until you have been told the item was "verified", and you cannot
credibly reference § 1681n damages until the bureau has had its statutory
thirty days and used them badly.

    Tier 1  day 0    Reinvestigation demand        First Class
    Tier 2  day 30   Method of verification        Certified
    Tier 3  day 60   Pre-litigation notice         Certified + return receipt
    Tier 4  day 90   Regulatory escalation         Certified + return receipt

The postage ladder mirrors the legal ladder on purpose: by tier 3 the mailing
receipt is evidence, so it has to be signed for.

`generate_bureau_letter()` in letter_generator.py builds the tier 1 body.
This module escalates that body — it adds the sections a later round needs and
rewrites the framing, without rebuilding the underlying analysis.
"""
from __future__ import annotations

from datetime import datetime

from .legal_library import get_escalation_paths, get_state_law, get_theory

# ── Ladder definition ───────────────────────────────────────────────────────
# extra_service maps directly onto Lob's field of the same name.
TIER_LADDER = {
    1: {
        "tier": 1,
        "key": "reinvestigation",
        "name": "Reinvestigation Demand",
        "day": 0,
        "mail_class": "usps_first_class",
        "extra_service": None,
        "return_envelope": True,
        "anchor": "15 U.S.C. § 1681i(a)(1)",
        "summary": "Opens the dispute and starts the 30-day clock.",
    },
    2: {
        "tier": 2,
        "key": "method_of_verification",
        "name": "Method of Verification Demand",
        "day": 30,
        "mail_class": "usps_first_class",
        "extra_service": "certified",
        "return_envelope": True,
        "anchor": "15 U.S.C. § 1681i(a)(6)(B)(iii)",
        "summary": "Asks how the item was verified, by name, and with what documents.",
    },
    3: {
        "tier": 3,
        "key": "pre_litigation",
        "name": "Pre-Litigation Notice",
        "day": 60,
        "mail_class": "usps_first_class",
        "extra_service": "certified_return_receipt",
        "return_envelope": True,
        "anchor": "15 U.S.C. §§ 1681n, 1681o",
        "summary": "Puts the bureau on notice of willful and negligent noncompliance.",
    },
    4: {
        "tier": 4,
        "key": "regulatory_escalation",
        "name": "Regulatory Escalation",
        "day": 90,
        "mail_class": "usps_first_class",
        "extra_service": "certified_return_receipt",
        "return_envelope": True,
        "anchor": "12 U.S.C. § 5493(b)(3)",
        "summary": "Copies the CFPB, the FTC and the state Attorney General.",
    },
}

MAX_TIER = max(TIER_LADDER)


def tier_for_day(days_since_dispatch: int) -> int:
    """Which tier is due at this point in the case. Never exceeds MAX_TIER."""
    due = 1
    for tier, spec in sorted(TIER_LADDER.items()):
        if days_since_dispatch >= spec["day"]:
            due = tier
    return min(due, MAX_TIER)


def postage_for_tier(tier: int) -> dict:
    """Mail-class settings for this tier, ready to merge into a Lob payload."""
    spec = TIER_LADDER.get(tier, TIER_LADDER[MAX_TIER])
    payload = {
        "mail_type": spec["mail_class"],
        "return_envelope": spec["return_envelope"],
    }
    if spec["extra_service"]:
        payload["extra_service"] = spec["extra_service"]
    return payload


def ladder_summary() -> list[dict]:
    """The whole ladder, for the Watcher timeline and the admin panel."""
    return [
        {
            "tier": s["tier"],
            "name": s["name"],
            "day": s["day"],
            "postage": (
                "Certified + return receipt" if s["extra_service"] == "certified_return_receipt"
                else "Certified" if s["extra_service"] == "certified"
                else "First Class"
            ),
            "anchor": s["anchor"],
            "summary": s["summary"],
        }
        for s in sorted(TIER_LADDER.values(), key=lambda x: x["tier"])
    ]


# ── Escalation sections ─────────────────────────────────────────────────────

def _prior_round_reference(prior: dict | None) -> list[str]:
    """Cite the previous round so the recipient cannot treat this as a new dispute."""
    if not prior:
        return [
            "This letter follows an earlier dispute sent to you regarding the same items.",
            "",
        ]

    lines = ["PRIOR CORRESPONDENCE", ""]
    sent = prior.get("sent_at") or prior.get("date") or ""
    if sent:
        lines.append(f"  Dispute mailed: {sent}")
    if prior.get("tracking_number"):
        lines.append(f"  USPS tracking: {prior['tracking_number']}")
    if prior.get("delivered_at"):
        lines.append(f"  Delivered: {prior['delivered_at']}")
    if prior.get("tier"):
        spec = TIER_LADDER.get(prior["tier"], {})
        lines.append(f"  Round: Tier {prior['tier']} — {spec.get('name', '')}")
    lines.append("")
    lines.append(
        "The statutory period for reinvestigation under 15 U.S.C. § 1681i(a)(1) has "
        "run from the date of delivery shown above."
    )
    lines.append("")
    return lines


def _section_mov(analyst_report: dict) -> str:
    """Tier 2 — method of verification demand."""
    lines = [
        "SECTION 8 — DEMAND FOR METHOD OF VERIFICATION",
        "",
        ("You have reported that the disputed items were verified. Under 15 U.S.C. "
        "§ 1681i(a)(6)(B)(iii), I am entitled to a description of the procedure used "
        "to determine the accuracy and completeness of the disputed information, "
        "including the business name, address, and telephone number of each furnisher "
        "contacted. I am requesting that description now."),
        "",
        "For each item still appearing on my file, provide in writing:",
        "",
        "  (a) The name, address, and telephone number of the furnisher contacted.",
        "  (b) The date the furnisher was contacted and the method of contact.",
        ("  (c) The name and title of the individual at your organization who conducted "
        "the reinvestigation."),
        ("  (d) Every document the furnisher supplied in response, or a statement that "
        "no documents were supplied."),
        ("  (e) The specific steps taken to resolve the discrepancies identified in my "
        "prior letter, beyond transmitting an automated dispute code."),
        "",
        ("A response consisting only of the word 'verified', or of an e-OSCAR response "
        "code, does not describe a procedure and does not satisfy the statute. "
        "Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997), holds that a "
        "reinvestigation must be reasonable, and that merely restating a furnisher's "
        "position is not enough where the consumer has identified specific reasons to "
        "doubt it."),
        "",
    ]

    blocks = analyst_report.get("violation_theory_blocks", [])
    if blocks:
        lines.append("The specific reasons I identified, which remain unaddressed:")
        lines.append("")
        for block in blocks:
            theory = get_theory(block["theory_id"]) or {}
            lines.append(f"  - {theory.get('title', block['theory_id'])}")
            if block.get("common_factual_pattern"):
                lines.append(f"      {block['common_factual_pattern']}")
        lines.append("")

    lines.append(
        "If you cannot produce the description this statute requires, the item was "
        "not reasonably reinvestigated and must be deleted under "
        "15 U.S.C. § 1681i(a)(5)(A)."
    )
    lines.append("")
    return "\n".join(lines)


def _section_pre_litigation(analyst_report: dict, state_code: str = "") -> str:
    """Tier 3 — notice of willful and negligent noncompliance."""
    lines = [
        "SECTION 8 — NOTICE OF NONCOMPLIANCE",
        "",
        ("This is my third written communication regarding these items. I have "
        "identified specific inaccuracies, requested a reinvestigation, and requested "
        "the method of verification. The items remain on my file."),
        "",
        "Two provisions of the Act are now engaged:",
        "",
        ("  15 U.S.C. § 1681o — negligent noncompliance. A consumer reporting agency "
        "that negligently fails to comply with the Act is liable for actual damages "
        "together with costs and reasonable attorney's fees."),
        "",
        ("  15 U.S.C. § 1681n — willful noncompliance. Where the failure is willful, "
        "which includes reckless disregard of the statutory obligation, liability "
        "extends to actual damages or statutory damages of $100 to $1,000 per "
        "violation, together with punitive damages, costs and fees. Safeco Ins. Co. "
        "of America v. Burr, 551 U.S. 47 (2007), holds that recklessness suffices "
        "for willfulness under this section."),
        "",
        ("Continuing to report information after a consumer has twice identified "
        "specific grounds for doubting it, and after failing to describe any "
        "procedure used to verify it, is the pattern those provisions address."),
        "",
    ]

    state_law = get_state_law(state_code) if state_code else None
    if state_law:
        lines.append(f"STATE LAW — {state_law.get('name', state_code)}")
        lines.append("")
        if state_law.get("consumer_protection"):
            lines.append(f"  {state_law['consumer_protection']}")
        if state_law.get("debt_collection"):
            lines.append(f"  {state_law['debt_collection']}")
        if state_law.get("sol_written"):
            lines.append(
                f"  Statute of limitations on written contracts: "
                f"{state_law['sol_written']} years ({state_law.get('sol_statute', '')})".rstrip(" ()")
            )
        if state_law.get("additional"):
            lines.append(f"  {state_law['additional']}")
        lines.append("")
        lines.append(
            "  Reporting a time-barred debt is not itself unlawful, but the "
            "limitations period above is relevant to what documentation the "
            "furnisher can still be expected to produce."
        )
        lines.append("")

    lines.append(
        "I would prefer to resolve this without a complaint or a filing. Delete the "
        "items identified above, or produce the documentation and the description of "
        "procedure that would justify keeping them, within 30 days of receipt."
    )
    lines.append("")
    return "\n".join(lines)


def _section_regulatory(analyst_report: dict, recipient_type: str = "bureau") -> str:
    """Tier 4 — regulatory escalation, with copies actually going out."""
    lines = [
        "SECTION 8 — REGULATORY ESCALATION",
        "",
        ("Ninety days have passed since my first dispute. The items remain on my file "
        "and no adequate description of the verification procedure has been provided."),
        "",
        "Copies of this letter and the full correspondence record are being filed with:",
        "",
        "  - The Consumer Financial Protection Bureau",
        "    1700 G Street NW, Washington, DC 20552",
        "  - The Federal Trade Commission",
        "    600 Pennsylvania Avenue NW, Washington, DC 20580",
        "  - The Attorney General of my state of residence",
        "",
        ("The correspondence record accompanying those complaints includes the mailing "
        "dates, USPS certified tracking numbers and return receipts for every round."),
        "",
    ]

    paths = get_escalation_paths(recipient_type)
    if paths:
        lines.append("Remedies remaining available to me:")
        lines.append("")
        for path in paths:
            lines.append(f"  - {path}")
        lines.append("")

    lines.append(
        "This remains resolvable. Deleting the disputed items, or producing the "
        "documentation that supports them, closes the matter."
    )
    lines.append("")
    return "\n".join(lines)


# ── Public entry point ──────────────────────────────────────────────────────

_TIER_SUBJECTS = {
    1: "Formal Dispute — Request for Reinvestigation",
    2: "Second Notice — Demand for Method of Verification",
    3: "Third Notice — Noncompliance with 15 U.S.C. §§ 1681i, 1681n, 1681o",
    4: "Final Notice — Regulatory Complaint Filed",
}


def apply_tier(
    letter: dict,
    tier: int,
    analyst_report: dict,
    state_code: str = "",
    prior_round: dict | None = None,
    recipient_type: str = "bureau",
) -> dict:
    """
    Escalate a tier-1 letter to the requested tier.

    `letter` is what generate_bureau_letter() or generate_collector_letter()
    returned. `prior_round` carries the previous mailing's tracking data, so the
    escalated letter can cite it. Returns a new dict; the input is not mutated.
    """
    tier = max(1, min(int(tier or 1), MAX_TIER))
    spec = TIER_LADDER[tier]
    out = dict(letter)

    if tier == 1:
        out["tier"] = 1
        out["tier_name"] = spec["name"]
        out["postage"] = postage_for_tier(1)
        return out

    body = out.get("body", "")

    # Splice the prior-round reference in just below the salutation block, and
    # append the escalation section before the signature.
    prior_block = "\n".join(_prior_round_reference(prior_round))

    if tier == 2:
        escalation = _section_mov(analyst_report)
    elif tier == 3:
        escalation = _section_pre_litigation(analyst_report, state_code)
    else:
        escalation = _section_regulatory(analyst_report, recipient_type)

    signature_marker = "Sincerely,"
    if signature_marker in body:
        head, _, tail = body.rpartition(signature_marker)
        body = f"{head}{escalation}\n{signature_marker}{tail}"
    else:
        body = f"{body}\n{escalation}"

    # Prior-round reference goes near the top, right after the rule line the
    # header ends with.
    rule = "=" * 60
    if rule in body:
        head, _, tail = body.partition(rule)
        body = f"{head}{rule}\n\n{prior_block}{tail}"
    else:
        body = f"{prior_block}\n{body}"

    out["body"] = body
    out["tier"] = tier
    out["tier_name"] = spec["name"]
    out["postage"] = postage_for_tier(tier)
    out["subject"] = f"{_TIER_SUBJECTS[tier]} — {out.get('recipient_name', '')}".strip(" —")
    out["escalated_at"] = datetime.utcnow().isoformat()
    return out
