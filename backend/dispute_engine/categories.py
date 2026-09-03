"""
Dispute categories — the full consumer-facing taxonomy.

This is the bridge between what a consumer (or the Claude extractor) can
recognise on a credit report and the violation theories in `legal_library`.

A *category* is what the item looks like on the report ("collection account",
"repossession", "unauthorized inquiry"). A *theory* is the legal argument for
why it must come off. One category can arm several theories; the analyst
decides which actually fire based on the facts and the consumer's
affirmations.

Each category declares:
  label            human label shown in the UI
  type             'bureau' | 'creditor' | 'public_record' | 'personal_info'
  severity         1-5, used for ranking the attack surface (5 = most damaging)
  fcra_sections    the sections a letter about this item should anchor on
  theories         violation theory ids in legal_library that this category arms
  affirmations     affirmation keys the consumer is asked to confirm
  keywords         tokens the fallback keyword scanner looks for
  falloff_years    how long the item may legally be reported, when fixed
  note             one line of plain-English guidance for the UI

Nothing here asserts an outcome. A category arming a theory only means the
theory is *tested*; `analyst.analyze()` still has to match the facts.
"""
from __future__ import annotations

# ── Statutory shorthand used across categories ──────────────────────────────
FCRA_CITATIONS = {
    "604": "FCRA § 604 (15 U.S.C. § 1681b) — permissible purpose",
    "605": "FCRA § 605 (15 U.S.C. § 1681c) — obsolete information",
    "605B": "FCRA § 605B (15 U.S.C. § 1681c-2) — identity theft block",
    "607b": "FCRA § 607(b) (15 U.S.C. § 1681e(b)) — maximum possible accuracy",
    "609": "FCRA § 609 (15 U.S.C. § 1681g) — full file disclosure",
    "611": "FCRA § 611 (15 U.S.C. § 1681i) — reinvestigation",
    "611MOV": "FCRA § 611(a)(6)(B)(iii) (15 U.S.C. § 1681i) — method of verification",
    "623": "FCRA § 623 (15 U.S.C. § 1681s-2) — furnisher accuracy duties",
    "1681n": "FCRA § 616 (15 U.S.C. § 1681n) — willful noncompliance",
    "1681o": "FCRA § 617 (15 U.S.C. § 1681o) — negligent noncompliance",
    "1692g": "FDCPA § 809 (15 U.S.C. § 1692g) — debt validation",
    "1692e": "FDCPA § 807 (15 U.S.C. § 1692e) — false or misleading representations",
}

# Standard reporting windows under FCRA § 605(a). Bankruptcy chapter 7 runs
# ten years from the date of filing; most other adverse items run seven years
# from the date of first delinquency.
DEFAULT_FALLOFF_YEARS = 7


DISPUTE_CATEGORIES: dict[str, dict] = {

    # ── Collections and debt buyers ─────────────────────────────────────────
    "collection": {
        "label": "Collection Account",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["609", "611", "623", "1692g"],
        "theories": [
            "improper_chain_of_ownership",
            "validation_failure",
            "duplicate_inconsistent_reporting",
        ],
        "affirmations": ["not_recognized", "uncertain_chain", "no_validation_received"],
        "keywords": [
            "collection", "collections", "placed for collection", "sold to",
            "transferred to", "debt buyer", "assigned to", "purchased by",
            "factoring company account",
        ],
        "falloff_years": 7,
        "note": "Runs seven years from the original delinquency, not from when the "
                "collector bought it. Selling a debt does not restart the clock.",
    },
    "debt_buyer": {
        "label": "Debt Buyer / Junk Debt",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["611", "623", "1692g", "1692e"],
        "theories": ["improper_chain_of_ownership", "validation_failure"],
        "affirmations": ["not_recognized", "uncertain_chain", "no_validation_received"],
        "keywords": [
            "portfolio recovery", "midland", "lvnv", "cavalry", "resurgent",
            "jefferson capital", "unifund", "asset acceptance", "encore capital",
        ],
        "falloff_years": 7,
        "note": "The buyer must be able to show an unbroken assignment trail from "
                "the original creditor. Many cannot.",
    },
    "medical_debt": {
        "label": "Medical Debt",
        "type": "bureau",
        "severity": 4,
        "fcra_sections": ["611", "623", "1692g"],
        "theories": ["validation_failure", "improper_chain_of_ownership",
                     "duplicate_inconsistent_reporting"],
        "affirmations": ["not_recognized", "no_validation_received"],
        "keywords": [
            "medical", "hospital", "health", "clinic", "physician", "dental",
            "radiology", "anesthesia", "emergency room", "ambulance",
        ],
        "falloff_years": 7,
        "note": "Since 2023 the three national bureaus voluntarily exclude paid "
                "medical collections and unpaid ones under $500, and wait a year "
                "before reporting. That is bureau policy, not statute — but it is "
                "still grounds to demand removal.",
    },

    # ── Payment history and account status ──────────────────────────────────
    "late_payment": {
        "label": "Late Payment",
        "type": "bureau",
        "severity": 3,
        "fcra_sections": ["609", "611", "623", "607b"],
        "theories": ["re_aging", "duplicate_inconsistent_reporting"],
        "affirmations": ["dates_inconsistent", "dofd_uncertain"],
        "keywords": [
            "30 days late", "60 days late", "90 days late", "120 days late",
            "150 days late", "180 days late", "past due", "delinquent",
            "was late", "late payment",
        ],
        "falloff_years": 7,
        "note": "Each late marker is its own data point. Check that the month "
                "reported matches your own records — misaligned grids are common.",
    },
    "charge_off": {
        "label": "Charge-Off",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["609", "611", "623", "607b"],
        "theories": ["re_aging", "duplicate_inconsistent_reporting",
                     "improper_chain_of_ownership"],
        "affirmations": ["dofd_uncertain", "dates_inconsistent", "uncertain_chain"],
        "keywords": [
            "charge off", "charged off", "charge-off", "profit and loss",
            "written off", "bad debt", "unpaid balance charged to",
        ],
        "falloff_years": 7,
        "note": "A charge-off and a collection on the same debt are often reported "
                "together. That double-counting is itself disputable.",
    },
    "balance_inaccuracy": {
        "label": "Wrong Balance or Credit Limit",
        "type": "bureau",
        "severity": 3,
        "fcra_sections": ["611", "623", "607b"],
        "theories": ["duplicate_inconsistent_reporting"],
        "affirmations": ["dates_inconsistent"],
        "keywords": [
            "balance", "high balance", "credit limit", "past due amount",
            "amount owed", "original amount",
        ],
        "falloff_years": DEFAULT_FALLOFF_YEARS,
        "note": "A missing credit limit makes utilization uncomputable and can "
                "depress the score on its own. Worth fixing even on a good account.",
    },
    "status_inaccuracy": {
        "label": "Wrong Account Status",
        "type": "bureau",
        "severity": 3,
        "fcra_sections": ["611", "623", "607b"],
        "theories": ["duplicate_inconsistent_reporting", "re_aging"],
        "affirmations": ["dates_inconsistent"],
        "keywords": [
            "closed by credit grantor", "account closed", "settled",
            "paid in full", "included in bankruptcy", "transferred",
            "status", "account condition",
        ],
        "falloff_years": DEFAULT_FALLOFF_YEARS,
        "note": "Closed-by-consumer reported as closed-by-grantor, or a settled "
                "account still showing a balance, are both § 607(b) accuracy failures.",
    },
    "re_aging": {
        "label": "Re-Aged Account",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["605", "611", "623", "607b"],
        "theories": ["re_aging", "obsolescence"],
        "affirmations": ["dofd_uncertain", "dates_inconsistent"],
        "keywords": [
            "date of first delinquency", "dofd", "date opened", "date assigned",
            "date reported", "last active",
        ],
        "falloff_years": 7,
        "note": "Moving the date of first delinquency forward keeps an item on the "
                "file past its lawful window. It is one of the strongest theories "
                "you have when the dates disagree across bureaus.",
    },

    # ── Identity, ownership and file integrity ──────────────────────────────
    "identity_error": {
        "label": "Not My Account",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["609", "611", "623", "607b"],
        "theories": ["mixed_file_indicators", "identity_theft_documented",
                     "improper_chain_of_ownership"],
        "affirmations": ["not_recognized", "name_not_mine"],
        "keywords": [
            "not mine", "unknown account", "never opened", "unauthorized",
            "do not recognize",
        ],
        "falloff_years": 0,
        "note": "If the account is not yours it should not be on the file at all — "
                "no waiting period applies.",
    },
    "mixed_file": {
        "label": "Mixed File / Wrong Consumer",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["609", "611", "607b"],
        "theories": ["mixed_file_indicators", "address_inaccuracy"],
        "affirmations": ["name_not_mine", "address_mismatch", "not_recognized"],
        "keywords": [
            "jr", "sr", "ii", "iii", "also known as", "aka", "similar name",
            "different ssn",
        ],
        "falloff_years": 0,
        "note": "Usually shows up as a relative's or stranger's data merged into "
                "your file. Names, addresses and partial SSNs are the tell.",
    },
    "identity_theft": {
        "label": "Identity Theft",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["605B", "609", "611", "623"],
        "theories": ["identity_theft_documented"],
        "affirmations": ["confirmed_fraud", "ftc_report_number", "not_recognized"],
        "keywords": ["identity theft", "fraud", "fraudulent", "stolen identity"],
        "falloff_years": 0,
        "note": "With an FTC Identity Theft Report, § 605B requires the bureau to "
                "block the information within four business days. This is a "
                "different and faster path than an ordinary dispute.",
    },
    "duplicate": {
        "label": "Duplicate Reporting",
        "type": "bureau",
        "severity": 4,
        "fcra_sections": ["611", "623", "607b"],
        "theories": ["duplicate_inconsistent_reporting"],
        "affirmations": ["not_recognized", "dates_inconsistent"],
        "keywords": ["duplicate", "same account", "reported twice"],
        "falloff_years": DEFAULT_FALLOFF_YEARS,
        "note": "One debt counted twice damages the score twice. Original creditor "
                "plus collector on the same balance is the usual pattern.",
    },
    "personal_info": {
        "label": "Wrong Personal Information",
        "type": "personal_info",
        "severity": 2,
        "fcra_sections": ["609", "611", "607b"],
        "theories": ["address_inaccuracy", "mixed_file_indicators"],
        "affirmations": ["address_mismatch", "name_not_mine"],
        "keywords": [
            "address", "former address", "employer", "aka", "name variation",
            "date of birth",
        ],
        "falloff_years": 0,
        "note": "Addresses you never lived at are how mixed files start. Clean "
                "these first — it makes every other dispute harder to deflect.",
    },
    "deceased_indicator": {
        "label": "Deceased Indicator",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["611", "607b"],
        "theories": ["mixed_file_indicators"],
        "affirmations": ["name_not_mine"],
        "keywords": ["deceased", "date of death"],
        "falloff_years": 0,
        "note": "A deceased flag on a living consumer blocks all credit. Treat it "
                "as urgent and dispute with all three bureaus at once.",
    },

    # ── Secured lending outcomes ────────────────────────────────────────────
    "repossession": {
        "label": "Repossession",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["611", "623", "607b"],
        "theories": ["re_aging", "duplicate_inconsistent_reporting",
                     "improper_chain_of_ownership"],
        "affirmations": ["dofd_uncertain", "dates_inconsistent", "not_recognized"],
        "keywords": [
            "repossession", "repossessed", "voluntary surrender", "involuntary repo",
            "redeemed", "deficiency balance",
        ],
        "falloff_years": 7,
        "note": "Check the deficiency balance against the sale proceeds — many "
                "post-repossession balances are reported without the credit for sale.",
    },
    "foreclosure": {
        "label": "Foreclosure",
        "type": "bureau",
        "severity": 5,
        "fcra_sections": ["611", "623", "607b"],
        "theories": ["re_aging", "improper_chain_of_ownership"],
        "affirmations": ["dofd_uncertain", "dates_inconsistent", "uncertain_chain"],
        "keywords": [
            "foreclosure", "foreclosed", "deed in lieu", "short sale",
            "settled for less than full balance",
        ],
        "falloff_years": 7,
        "note": "Servicing transfers on mortgages are frequent, and each transfer "
                "is a chance for the reported dates to drift.",
    },

    # ── Public records ──────────────────────────────────────────────────────
    "bankruptcy": {
        "label": "Bankruptcy",
        "type": "public_record",
        "severity": 5,
        "fcra_sections": ["605", "611", "607b"],
        "theories": ["obsolescence", "duplicate_inconsistent_reporting"],
        "affirmations": ["dates_inconsistent"],
        "keywords": ["bankruptcy", "chapter 7", "chapter 13", "chapter 11", "discharged"],
        "falloff_years": 10,
        "note": "Chapter 7 reports for ten years from filing; chapter 13 is "
                "typically removed at seven. Accounts discharged in the bankruptcy "
                "must show a zero balance — many do not.",
    },
    "judgment_lien": {
        "label": "Judgment or Tax Lien",
        "type": "public_record",
        "severity": 5,
        "fcra_sections": ["605", "611", "607b"],
        "theories": ["obsolescence", "mixed_file_indicators"],
        "affirmations": ["not_recognized", "dates_inconsistent", "name_not_mine"],
        "keywords": ["judgment", "civil judgment", "tax lien", "lien", "satisfied"],
        "falloff_years": 7,
        "note": "Since the National Consumer Assistance Plan the bureaus no longer "
                "report most civil judgments and tax liens at all. If one is still "
                "on your file, say so directly.",
    },
    "rental_eviction": {
        "label": "Eviction or Rental Debt",
        "type": "bureau",
        "severity": 3,
        "fcra_sections": ["611", "623", "1692g"],
        "theories": ["validation_failure", "improper_chain_of_ownership"],
        "affirmations": ["not_recognized", "no_validation_received"],
        "keywords": ["eviction", "landlord", "property management", "rental", "lease"],
        "falloff_years": 7,
        "note": "Rental debt is often sold on with no lease documentation attached. "
                "Ask for the signed lease and the ledger.",
    },

    # ── Inquiries ───────────────────────────────────────────────────────────
    "inquiry": {
        "label": "Unauthorized Hard Inquiry",
        "type": "bureau",
        "severity": 2,
        "fcra_sections": ["604", "609", "611"],
        "theories": ["identity_theft_documented", "mixed_file_indicators"],
        "affirmations": ["not_recognized", "confirmed_fraud"],
        "keywords": ["inquiry", "inquiries", "hard pull", "credit check", "requested by"],
        "falloff_years": 2,
        "note": "Hard inquiries fall off after two years and only affect the score "
                "for one. Dispute them when you never authorized the pull — "
                "§ 604 requires a permissible purpose.",
    },

    # ── Specialty loans ─────────────────────────────────────────────────────
    "student_loan": {
        "label": "Student Loan",
        "type": "bureau",
        "severity": 4,
        "fcra_sections": ["611", "623", "607b"],
        "theories": ["duplicate_inconsistent_reporting", "re_aging"],
        "affirmations": ["dates_inconsistent", "dofd_uncertain"],
        "keywords": [
            "student loan", "sallie mae", "navient", "nelnet", "mohela",
            "great lakes", "fedloan", "department of education", "deferment",
            "forbearance",
        ],
        "falloff_years": 7,
        "note": "Servicer transfers routinely create duplicate tradelines for one "
                "loan, and deferment periods often get reported as delinquency.",
    },
    "child_support": {
        "label": "Child Support Arrears",
        "type": "public_record",
        "severity": 4,
        "fcra_sections": ["611", "607b"],
        "theories": ["mixed_file_indicators", "duplicate_inconsistent_reporting"],
        "affirmations": ["not_recognized", "dates_inconsistent"],
        "keywords": ["child support", "support arrears", "domestic relations"],
        "falloff_years": 7,
        "note": "Verify against the state disbursement unit's own ledger before "
                "disputing — the state record controls.",
    },

    # ── Aging out ───────────────────────────────────────────────────────────
    "obsolete": {
        "label": "Obsolete Item (past the reporting window)",
        "type": "bureau",
        "severity": 4,
        "fcra_sections": ["605", "611"],
        "theories": ["obsolescence"],
        "affirmations": ["dates_inconsistent"],
        "keywords": ["date opened", "date of first delinquency", "date reported"],
        "falloff_years": 7,
        "note": "Past the window it must come off regardless of whether the debt "
                "is real. This is the cleanest removal argument there is.",
    },

    # ── Direct-to-furnisher ─────────────────────────────────────────────────
    "creditor_direct": {
        "label": "Direct Creditor Dispute (§ 623)",
        "type": "creditor",
        "severity": 3,
        "fcra_sections": ["623", "607b", "1692g"],
        "theories": ["validation_failure", "duplicate_inconsistent_reporting"],
        "affirmations": ["no_validation_received", "dates_inconsistent"],
        "keywords": [],
        "falloff_years": DEFAULT_FALLOFF_YEARS,
        "note": "Goes to the furnisher rather than the bureau. Useful when the "
                "bureau keeps 'verifying' an item the creditor's own records "
                "contradict.",
    },
}


# Categories the AI extractor is allowed to assign. Kept separate so the
# prompt and the validator can never drift apart.
CATEGORY_IDS = tuple(DISPUTE_CATEGORIES.keys())


def get_category(category_id: str) -> dict:
    """Look up one category. Returns {} when unknown."""
    return DISPUTE_CATEGORIES.get(category_id, {})


def all_categories() -> dict:
    """Compact form for the UI and the admin panel — no keywords or templates."""
    return {
        cid: {
            "label": c["label"],
            "type": c["type"],
            "severity": c["severity"],
            "fcra_sections": c["fcra_sections"],
            "theories": c["theories"],
            "falloff_years": c["falloff_years"],
            "note": c["note"],
        }
        for cid, c in DISPUTE_CATEGORIES.items()
    }


def theories_for(category_id: str) -> list[str]:
    """Violation theory ids this category arms."""
    return list(DISPUTE_CATEGORIES.get(category_id, {}).get("theories", []))


def affirmations_for(category_id: str) -> list[str]:
    """Affirmation keys the consumer should be asked to confirm for this category."""
    return list(DISPUTE_CATEGORIES.get(category_id, {}).get("affirmations", []))


def citations_for(category_id: str) -> list[str]:
    """Full statutory citations for this category, in the order they should appear."""
    sections = DISPUTE_CATEGORIES.get(category_id, {}).get("fcra_sections", [])
    return [FCRA_CITATIONS[s] for s in sections if s in FCRA_CITATIONS]


# Default dispute reasons, used when the extractor gives us a category but no
# reason of its own. Written in the consumer's voice — these end up in the
# letter and in the review screen, so they state a position, not a conclusion.
_REASON_TEMPLATES = {
    # Says nothing about whose debt it is — because the software cannot know
    # that, and the consumer never said it. The old text opened with "I do not
    # recognise this collection account and have no contractual relationship
    # with {target}", fired from a parser classification, and put a factual
    # denial in the consumer's mouth that they had not made. A furnisher
    # answers that in one move by producing the account log, and the letter
    # becomes the problem instead of the reporting.
    #
    # Accuracy, completeness and verifiability are the grounds that survive
    # the log: they are the bureau's own duties under § 1681e(b) and
    # § 1681i, and none of them depends on the debt not being owed.
    "collection": "I dispute the accuracy and completeness of this collection account as "
                  "reported. I am requesting verification of the amount, the dates, and "
                  "{target}'s authority to report it, including documentation of the "
                  "assignment from the original creditor.",
    "debt_buyer": "{target} is not the original creditor. I am requesting documentation "
                  "of the complete chain of title from the original creditor to {target}.",
    "medical_debt": "This medical account is disputed. I am requesting validation and an "
                    "itemised statement of the charges.",
    "late_payment": "The late payment history reported on account {account} does not match "
                    "my records. I am requesting verification against the furnisher's "
                    "own payment ledger.",
    "charge_off": "The charge-off reported on account {account} is disputed, including its "
                  "date of first delinquency and the balance shown.",
    "balance_inaccuracy": "The balance or credit limit reported on account {account} is "
                          "inaccurate as shown.",
    "status_inaccuracy": "The account status reported for {account} does not reflect the "
                         "actual condition of the account.",
    "re_aging": "The date of first delinquency reported for account {account} appears to "
                "have been moved forward, extending the reporting period beyond what "
                "15 U.S.C. § 1681c permits.",
    "identity_error": "This account does not belong to me. I did not open it and I am not "
                      "responsible for it.",
    "mixed_file": "This information belongs to another consumer and appears in my file in "
                  "error.",
    "identity_theft": "This account was opened fraudulently without my knowledge or "
                      "authorisation.",
    "duplicate": "This debt appears more than once on my file, counting a single obligation "
                 "multiple times.",
    # A former address usually IS the consumer's, and reportable. "Not mine"
    # was a denial the parser had no basis for; outdated-and-unverified is
    # what a stale entry actually is, and it is what the consumer can stand
    # behind without knowing which entry the software flagged.
    "personal_info": "This personal information is outdated or inaccurate as reported. I am "
                     "requesting that it be verified against the furnisher's records or "
                     "removed from my file.",
    "deceased_indicator": "My file carries a deceased indicator in error. I am living and "
                          "this flag is blocking my access to credit.",
    "repossession": "The repossession reported on account {account} is disputed, including "
                    "the deficiency balance and the dates shown.",
    "foreclosure": "The foreclosure information reported for account {account} is disputed, "
                   "including the dates and the balance shown.",
    "bankruptcy": "The bankruptcy information reported is inaccurate as shown, or the "
                  "accounts included in it are not reporting a zero balance as required.",
    "judgment_lien": "This public record is disputed. I am requesting verification against "
                     "the court's own records.",
    "rental_eviction": "This rental debt is disputed. I am requesting the signed lease and "
                       "the full account ledger.",
    "inquiry": "I did not authorise {target} to access my credit file, and no permissible "
               "purpose under 15 U.S.C. § 1681b applies.",
    "student_loan": "The information reported on this student loan account is inaccurate, "
                    "including its status and payment history.",
    "child_support": "This child support record is disputed. I am requesting verification "
                     "against the state disbursement unit's own ledger.",
    "obsolete": "This item is past the reporting period permitted by 15 U.S.C. § 1681c and "
                "must be removed regardless of its accuracy.",
    "creditor_direct": "The information you are furnishing on account {account} is "
                       "inaccurate. I am disputing it with you directly under "
                       "15 U.S.C. § 1681s-2.",
}


# Values a parser writes when a field is absent. They are strings, so they
# pass a truthiness guard and print: "Account Number: Unknown" reached real
# letters, and so did "the date of first delinquency reported for account
# Unknown", which is a legal demand about a tradeline it cannot name.
PLACEHOLDERS = frozenset({
    "unknown", "none", "n/a", "na", "null", "-", "--", "not reported",
})

# Categories whose dispute reason asserts something only the consumer can
# know: that an account is not theirs, that it was opened fraudulently, that
# the file has been mixed with someone else's, that a deceased flag is wrong.
#
# Nothing read off a credit report can establish any of these. Software must
# never reach them on its own — if it does, the letter states a personal fact
# the consumer never gave us, over their signature, and a furnisher answers it
# by producing the account log. Each one is unlocked only by the consumer
# ticking its affirmation on the review screen.
CONSUMER_ONLY_CATEGORIES = frozenset({
    "identity_theft", "identity_error", "mixed_file", "deceased_indicator",
})


def consumer_affirmed(category_id: str, affirmations: dict | None) -> bool:
    """
    Whether the consumer personally affirmed what this category asserts.

    Always True for the accuracy-based categories, which claim nothing about
    the consumer's own knowledge — they dispute what the file says, not whose
    debt it is, and that is a position the report itself supports.
    """
    if category_id not in CONSUMER_ONLY_CATEGORIES:
        return True
    required = set(affirmations_for(category_id))
    given = {k for k, v in (affirmations or {}).items() if v}
    return bool(required & given)


def real_value(value: object) -> str:
    """The value if it says something, otherwise an empty string."""
    text = str(value).strip() if value is not None else ""
    return "" if text.lower() in PLACEHOLDERS else text


def reason_for(category_id: str, target: str = "", account: str = "") -> str:
    """A default dispute reason for this category, in the consumer's voice."""
    template = _REASON_TEMPLATES.get(
        category_id,
        "The information reported on account {account} is inaccurate or incomplete "
        "as shown, and I am requesting verification.",
    )
    return template.format(
        target=real_value(target) or "this entity",
        account=real_value(account) or "this account",
    )


def prompt_taxonomy() -> str:
    """
    The category list, formatted for the extraction prompt.

    Generated from the taxonomy so the prompt and the validator can never
    disagree about which categories exist.
    """
    return "\n".join(
        f"- {cid}: {c['label']} — {c['note'].split('.')[0]}."
        for cid, c in DISPUTE_CATEGORIES.items()
    )


def guess_category(text: str) -> str:
    """
    Keyword fallback when the extractor gives us nothing usable.

    Scores every category by how many of its keywords appear, weighted by
    keyword length so that 'placed for collection' outranks a bare 'collection'.
    Falls back to a generic bureau dispute.
    """
    haystack = (text or "").lower()
    if not haystack:
        return "creditor_direct"

    best_id, best_score = "", 0
    for cid, cat in DISPUTE_CATEGORIES.items():
        score = sum(len(kw) for kw in cat["keywords"] if kw in haystack)
        if score > best_score:
            best_id, best_score = cid, score

    return best_id or "creditor_direct"


# Backwards compatibility: the original module called these "buckets" and a
# few call sites still do. Same data, older name.
DISPUTE_BUCKETS = DISPUTE_CATEGORIES
get_bucket = get_category
get_all_buckets = all_categories
