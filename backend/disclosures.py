"""
Consumer disclosures and acknowledgements.

Single source of truth for what the customer is told and what they affirm.
The frontend renders from here, the acknowledgement endpoint validates
against here, and the letter footer quotes from here — so the three can
never drift apart and say different things.

⚠️  NOT LEGAL ADVICE, AND NOT A COMPLIANCE GUARANTEE.

This module is drafted to match the positioning already documented in
docs/compliance/croa-positioning.md: the product is self-help document
preparation software the consumer operates themselves, not a service
performed on their behalf. That positioning is the company's, it has not
been reviewed by counsel, and the memo's own action list still says
"engage a consumer-finance attorney before scaling paid volume."

Several states (Texas and California among them) impose registration and
bonding requirements on credit services organizations that do not depend on
how the product describes itself. Nothing here substitutes for that review.

What this module does do is make sure the consumer is told the true things
that matter most, in plain language, before they pay:

  * nobody can remove accurate, timely information from a credit report
  * they can do all of this themselves, free
  * we are not a credit repair organization, credit counselor, or law firm
  * no outcome is promised
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import config

# Salt so a hashed IP cannot be reversed by hashing the whole IPv4 space.
_IP_SALT = config.TERMS_TOKEN_SECRET

# ── Version the text, so an acknowledgement records what was actually shown ──
DISCLOSURE_VERSION = "2026-08-31.1"


# ── The headline disclosure ─────────────────────────────────────────────────

WHAT_WE_ARE = {
    "id": "what_we_are",
    "heading": "What this is",
    "body": (
        "5-Min Credit Fix is self-help software. It reads the credit report you "
        "upload, identifies items that may be inaccurate or unverifiable, and "
        "prepares dispute letters in your name for you to review, sign and send. "
        "You decide what to dispute. You sign the letters. They are your letters."
    ),
}

WHAT_WE_ARE_NOT = {
    "id": "what_we_are_not",
    "heading": "What this is not",
    "body": (
        "We are not a credit repair organization, a credit counseling agency, a "
        "debt settlement company, a law firm, or a financial advisor. We do not "
        "contact the credit bureaus or your creditors on your behalf. We do not "
        "negotiate, advocate, or represent you. No attorney-client relationship "
        "is created, and nothing we provide is legal advice."
    ),
}

NO_GUARANTEE = {
    "id": "no_guarantee",
    "heading": "No outcome is promised",
    "body": (
        "We cannot and do not promise that any item will be removed, that your "
        "score will rise, or that your report will change at all. Nobody can "
        "lawfully make that promise. Accurate, current, and verifiable negative "
        "information cannot be removed from a credit report by anyone, at any "
        "price. What a dispute does is require the bureau to reinvestigate and "
        "to delete what it cannot verify."
    ),
}

FREE_ALTERNATIVE = {
    "id": "free_alternative",
    "heading": "You can do this yourself for free",
    "body": (
        "Every right this software helps you exercise is yours already and costs "
        "nothing to use. You can get your reports free at annualcreditreport.com, "
        "and you can dispute directly with Experian, Equifax and TransUnion at no "
        "charge, by mail or through their own websites. What you are paying us for "
        "is preparation and convenience — finding the items, drafting the letters, "
        "and putting them in the mail — not for access to your rights."
    ),
}

YOUR_RESPONSIBILITY = {
    "id": "your_responsibility",
    "heading": "Your responsibility",
    "body": (
        "You must have a good-faith basis for every item you dispute. Knowingly "
        "submitting a false statement to a credit bureau can carry legal "
        "consequences. Review each letter before it is sent and remove anything "
        "you do not believe to be inaccurate. Disputing accurate information "
        "wastes the bureau's 30 days and yours."
    ),
}

WHAT_HAPPENS_NEXT = {
    "id": "what_happens_next",
    "heading": "What happens after you pay",
    "body": (
        "Your letters are prepared, mailed on your behalf, and emailed to you as a "
        "PDF. The bureaus have 30 days from receipt to investigate and respond. "
        "Responses go to you directly, not to us. Your personal information is "
        "encrypted while we hold it and permanently deleted within 24 hours."
    ),
}

DISCLOSURE_SECTIONS = [
    WHAT_WE_ARE,
    WHAT_WE_ARE_NOT,
    NO_GUARANTEE,
    FREE_ALTERNATIVE,
    YOUR_RESPONSIBILITY,
    WHAT_HAPPENS_NEXT,
]


# ── Acknowledgements the consumer must affirm ───────────────────────────────
# Each is a separate, specific statement. A single "I agree to everything"
# checkbox is weaker evidence of informed consent than several narrow ones,
# and it is easier for a consumer to skim past.

REQUIRED_ACKNOWLEDGEMENTS = [
    {
        "id": "ack_not_counselor",
        "label": (
            "I understand 5-Min Credit Fix is software, not a credit repair "
            "organization, credit counselor, or law firm, and that no legal "
            "advice is being given."
        ),
    },
    {
        "id": "ack_no_guarantee",
        "label": (
            "I understand no result is promised, and that accurate and verifiable "
            "information cannot be removed from my credit report."
        ),
    },
    {
        "id": "ack_free_alternative",
        "label": (
            "I understand I can dispute items myself, directly with the bureaus, "
            "for free."
        ),
    },
    {
        "id": "ack_good_faith",
        "label": (
            "I affirm that the items I have selected are inaccurate, incomplete, "
            "or unverifiable to the best of my knowledge."
        ),
    },
    {
        "id": "ack_my_letters",
        "label": (
            "I understand these are my letters, sent in my name, and that I am "
            "responsible for their contents."
        ),
    },
]

REQUIRED_IDS = tuple(a["id"] for a in REQUIRED_ACKNOWLEDGEMENTS)


# ── Fine print ──────────────────────────────────────────────────────────────

FINE_PRINT = (
    "5-Min Credit Fix is a product of Arden Edge Labs. It is self-help document "
    "preparation software and is not a credit repair organization, credit "
    "counseling agency, debt settlement company, or law firm. We do not provide "
    "legal, financial, tax, or credit advice, and we do not act on your behalf "
    "with any credit bureau or creditor. No specific result is promised or "
    "implied. Accurate, timely, and verifiable information cannot be removed "
    "from a consumer report. You may obtain your credit reports free of charge "
    "at annualcreditreport.com and may dispute information directly with each "
    "consumer reporting agency at no cost. Fees are charged for document "
    "preparation and mailing only. Individual results vary."
)

# One-line version for letter footers and dense UI.
FINE_PRINT_SHORT = (
    "Prepared using self-help document preparation software. Not a credit repair "
    "organization, credit counselor, or law firm. Not legal advice. No result "
    "promised. You may dispute directly with each bureau free of charge."
)


# ── Validation ──────────────────────────────────────────────────────────────

def missing_acknowledgements(submitted: dict) -> list[str]:
    """
    Which required acknowledgements were not affirmed.

    Returns a list of ids. Empty list means all present and true.
    """
    if not isinstance(submitted, dict):
        return list(REQUIRED_IDS)
    return [aid for aid in REQUIRED_IDS if not bool(submitted.get(aid))]


def acknowledgement_record(submitted: dict, client_ip: str = "") -> dict:
    """
    Build the audit record for a consumer's acknowledgement.

    Deliberately carries no PII: the acknowledgement ids, the version of the
    text they were shown, a timestamp, and a salted hash of the caller's IP.
    Enough to show what was agreed to and when, without storing who.

    The IP is hashed *here* rather than trusting the caller to do it. A
    parameter named `ip_hash` that silently accepts a raw address is exactly
    how PII ends up in a table that promises it holds none.
    """
    ip_digest = ""
    if client_ip:
        ip_digest = hashlib.sha256(
            client_ip.encode() + _IP_SALT.encode()
        ).hexdigest()[:16]

    return {
        "version": DISCLOSURE_VERSION,
        "acknowledged": sorted(aid for aid in REQUIRED_IDS if submitted.get(aid)),
        "complete": not missing_acknowledgements(submitted),
        "at": datetime.now(timezone.utc).isoformat(),
        "ip_hash": ip_digest,
    }


def disclosure_payload() -> dict:
    """Everything the frontend needs to render the consent screen."""
    return {
        "version": DISCLOSURE_VERSION,
        "sections": DISCLOSURE_SECTIONS,
        "acknowledgements": REQUIRED_ACKNOWLEDGEMENTS,
        "fine_print": FINE_PRINT,
        "fine_print_short": FINE_PRINT_SHORT,
    }
