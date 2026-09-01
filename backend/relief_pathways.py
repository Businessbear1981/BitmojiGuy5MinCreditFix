"""
Relief pathways — the routes that make a debt smaller instead of arguing it.

The dispute engine's question is "should this tradeline be on the report?"
That is the right question for a debt buyer that cannot show an assignment
chain. It is the wrong first question for two categories:

  **Student loans.** A federal loan is almost always accurately reported. The
  consumer's leverage is not the credit report — it is forgiveness,
  discharge, consolidation and rehabilitation, all of which are free to
  apply for and none of which this platform can determine eligibility for.

  **Medical bills.** The balance itself is often reducible or void: charity
  care, a billing error visible only on an itemised statement, No Surprises
  Act protections, backdated Medicaid. Retiring the bill at the source moots
  the tradeline instead of contesting it.

A consumer sent through the letter generator without ever being told those
routes exist has been under-served, even if every letter is perfect. This
module is the single place the app asks "is there another road here?", so
that answer arrives on the review screen next to the items themselves.

── The line this module does not cross ────────────────────────────────────

Nothing here determines eligibility for anything. Every route names the
authoritative source and the documents worth gathering, and stops. The two
underlying modules (`student_loans`, `medical_relief`) enforce that in their
own payloads; this one only merges them and must not add a claim neither of
them makes.

Two things it says without hedging, because both protect the consumer:

  1. Federal student loan consolidation and rehabilitation are **free** at
     studentaid.gov. Companies charge for both. Nobody has to.
  2. There is **no federal grant** that pays an individual's personal debt.
     `medical_relief.GRANT_REALITY` carries the detail and ships in every
     payload that mentions the word.
"""
from __future__ import annotations

from typing import Optional

import medical_relief
import student_loans

# ── Student-loan routes that are not forgiveness ───────────────────────────
# `student_loans.FORGIVENESS_PROGRAMS` is a forgiveness/discharge directory.
# Consolidation and rehabilitation are neither — they are ways to change a
# loan's status — and they belong in the same panel because a consumer asking
# "what can I do about this?" does not draw that distinction.
#
# Kept here rather than pushed into `student_loans` so that module stays what
# its docstring says it is.

STUDENT_OTHER_ROUTES: dict[str, dict] = {
    "consolidation": {
        "name": "Direct Consolidation Loan",
        "generally_for":
            "Borrowers with more than one federal loan, or with an older "
            "loan type that is not eligible for the newer repayment plans. "
            "Consolidation combines federal loans into one and can change "
            "which plans and forgiveness programmes the loan can reach.",
        "documents_to_gather": [
            "Your full loan list from studentaid.gov, showing each loan's type",
            "Your current servicer and payment history",
        ],
        "verify_at": "https://studentaid.gov",
        "cost":
            "Free. Consolidation is applied for directly at studentaid.gov "
            "and there is no fee. Any company charging to consolidate "
            "federal student loans is charging for a free government form.",
        "note":
            "Consolidation is not automatically the right move — it can "
            "reset progress toward some forgiveness programmes and it can "
            "preserve it in others, depending on the loan types and the "
            "programme. Ask your servicer what it would do to your "
            "qualifying-payment count *before* you apply, in writing.",
    },
    "rehabilitation": {
        "name": "Rehabilitation or repayment of a defaulted federal loan",
        "generally_for":
            "Borrowers whose federal loans are in default. Rehabilitation is "
            "a defined process run by the loan holder; the terms, and what "
            "happens to the default notation on the credit report, are set "
            "by the Department of Education.",
        "documents_to_gather": [
            "Written confirmation from the holder that the loan is in "
            "default, and who currently holds it",
            "Your income documentation, since a rehabilitation payment is "
            "usually set against it",
        ],
        "verify_at": "https://studentaid.gov",
        "cost":
            "Free to arrange with the holder. Companies advertising "
            "'student loan default relief' for a fee are selling access to "
            "a free process.",
        "note":
            "Ask the holder in writing what happens to the credit report "
            "when rehabilitation completes, and get the answer before you "
            "start. Rehabilitation is generally available a limited number "
            "of times, so it is worth doing once, properly.",
    },
    "servicer_dispute": {
        "name": "Federal Student Aid Ombudsman",
        "generally_for":
            "Borrowers who cannot get a straight answer from their servicer "
            "— a payment count that does not add up, an application that "
            "goes unanswered, a forbearance applied without request.",
        "documents_to_gather": [
            "Every written exchange with the servicer, with dates",
            "The servicer's stated payment history, and your own records "
            "where they disagree",
        ],
        "verify_at": "https://studentaid.gov/feedback-center",
        "cost": "Free.",
        "note":
            "This is separate from a credit dispute and does not replace "
            "one. Both can run at the same time.",
    },
}


def _student_extra_signals(items: list[dict]) -> list[dict]:
    """Consolidation, rehabilitation and the ombudsman, in signal shape."""
    loans = [it for it in (items or []) if student_loans.is_student_loan(it)]
    federal = [it for it in loans if student_loans.looks_federal(it)]
    if not federal:
        return []

    out: list[dict] = []

    def add(key: str, observed: str, action: str):
        r = STUDENT_OTHER_ROUTES[key]
        out.append({
            "program_key": key,
            "program": r["name"],
            "observed_in_report": observed,
            "worth_checking_because": r["generally_for"],
            "what_to_do": action,
            "documents_to_gather": r["documents_to_gather"],
            "verify_at": r["verify_at"],
            "cost": r["cost"],
            "note": r["note"],
            "is_eligibility_determination": False,
            "disclaimer": student_loans.FORGIVENESS_DISCLAIMER,
        })

    count = len(federal)
    if count > 1:
        add("consolidation",
            f"{count} separate federal student loan tradelines appear on this "
            f"report.",
            "Log in at studentaid.gov to see your actual loan list — the "
            "credit report is not the authoritative record of what you owe or "
            "of which loans are federal. Ask your servicer, in writing, what "
            "consolidating would do to any forgiveness progress before you "
            "apply. It is free to apply.")

    if any(student_loans._has_delinquency(it) for it in federal):
        add("rehabilitation",
            "At least one federal loan on this report carries delinquency or "
            "default markers.",
            "Contact the current holder — which may not be the servicer named "
            "on the report — and ask what rehabilitation would require and "
            "what it would do to the credit reporting. Get that in writing "
            "before agreeing. It is free to arrange.")

    add("servicer_dispute",
        f"{count} federal student loan tradeline"
        f"{'s' if count != 1 else ''} on this report.",
        "If your servicer's payment history disagrees with your own records, "
        "or they will not answer a written question, the Federal Student Aid "
        "feedback centre and Ombudsman take that complaint. Free.")

    return out


def find_relief(items: list[dict],
                profile: Optional[dict] = None,
                consumer_marked_medical: Optional[list] = None) -> dict:
    """
    Everything worth raising with someone other than a credit bureau.

    Returns a payload shaped for one UI panel: two sections, each present
    only when the file actually shows that kind of debt, plus the anti-scam
    content whenever the word "grant" would appear anywhere on screen.

    `available` is the single field the frontend needs to decide whether to
    render the entry point at all.
    """
    items = items or []

    student_analysis = student_loans.analyze_student_loans(items)
    student_signals = list(student_loans.forgiveness_signals(items, profile))
    student_signals.extend(_student_extra_signals(items))

    medical = medical_relief.analyze_medical(items, consumer_marked_medical)

    has_student = bool(student_signals)
    has_medical = bool(medical.get("has_medical"))

    sections = []
    if has_student:
        sections.append({
            "key": "student_loans",
            "title": "Student loans",
            "subtitle": (
                f"{student_analysis.get('federal_count', 0)} federal "
                f"tradeline"
                f"{'s' if student_analysis.get('federal_count', 0) != 1 else ''} "
                f"on this report"),
            "lead":
                "Federal student loans are usually reported accurately, which "
                "means a dispute letter is rarely where the leverage is. "
                "Forgiveness, discharge, consolidation and rehabilitation are "
                "where it is — and all of them are free to apply for.",
            "routes": student_signals,
            "verify_at": student_loans.VERIFY_AT,
            "disclaimer": student_loans.FORGIVENESS_DISCLAIMER,
            "free_warning":
                "Every programme listed here is free to apply for at "
                "studentaid.gov. Any company charging a fee to enrol you in "
                "forgiveness, consolidation or default relief is charging for "
                "a free government form.",
        })

    if has_medical:
        sections.append({
            "key": "medical",
            "title": "Medical bills",
            "subtitle": (
                f"{medical['item_count']} medical account"
                f"{'s' if medical['item_count'] != 1 else ''} identified"
                + (f", ${medical['total_balance']:,.0f}"
                   if medical.get("total_balance") else "")),
            "lead":
                "A medical balance can often be reduced or erased at the "
                "source. Doing that moots the tradeline instead of arguing "
                "about it — and you can pursue both at once.",
            "routes": medical["routes"],
            "items": medical["items"],
            "sequence_note": medical.get("sequence_note", ""),
            "disclaimer": medical["disclaimer"],
        })

    return {
        "available": bool(sections),
        "sections": sections,
        # Shown whenever this panel is open at all. The panel is the place a
        # consumer is most primed to be sold a "debt relief grant", so the
        # correction sits alongside the real routes rather than in a footer.
        "grant_reality": medical_relief.GRANT_REALITY,
        "headline":
            "Some of these debts have a route that is not a dispute letter."
            if sections else "",
        "is_eligibility_determination": False,
        "student_analysis": student_analysis if has_student else None,
    }


def entry_point(items: list[dict],
                profile: Optional[dict] = None,
                consumer_marked_medical: Optional[list] = None) -> dict:
    """
    The cheap check the review screen calls to decide whether to show the card.

    Same inputs as `find_relief`, but returns only what a button needs, so a
    page that is not opening the panel does not carry the whole directory.
    """
    payload = find_relief(items, profile, consumer_marked_medical)
    kinds = [s["key"] for s in payload["sections"]]

    if not kinds:
        label = ""
    elif kinds == ["student_loans"]:
        label = "Look for student loan forgiveness, consolidation & relief"
    elif kinds == ["medical"]:
        label = "Look for medical bill assistance & charity care"
    else:
        label = "Look for forgiveness, assistance & consolidation"

    return {
        "available": payload["available"],
        "label": label,
        "kinds": kinds,
        "route_count": sum(len(s["routes"]) for s in payload["sections"]),
        "sublabel": " · ".join(s["subtitle"] for s in payload["sections"]),
    }
