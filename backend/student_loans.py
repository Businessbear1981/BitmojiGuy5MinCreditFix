"""
Federal student loans — the patterns that only show up across tradelines.

A federal loan portfolio does not look like a credit card. One consumer can
carry eight or nine separate tradelines from a single holder and every one of
them can be accurate, because federal aid is disbursed per academic term and
each disbursement is commonly reported as its own account. The per-item
parser sees eight lines from the same furnisher and has no way to tell that
apart from eight copies of one debt: it only ever looks at one tradeline at a
time. That is the gap this module fills — it reads the *set*.

── What this module will and will not say ─────────────────────────────────

It will say what the file shows: how many lines, whose they are, which dates
collide, which line carries delinquency, which line is missing a date of
first delinquency. Those are facts printed on the report and they are
disputable when they contradict each other.

It will **not** say whether a loan qualifies for any forgiveness or discharge
program. `FORGIVENESS_PROGRAMS` is a directory of program *names* and the
documents worth gathering before the consumer talks to their servicer. It
carries no eligibility rules, no dollar thresholds, no payment counts and no
deadlines, because every one of those has moved in recent years and this
platform has no way to verify the current version. Every entry points at
studentaid.gov, which is the only source that is current by construction.

The same restraint applies to payment pauses. Federal repayment has been
interrupted by deferments, forbearances, administrative forbearances and
servicer-side processing holds, and a month inside one of those periods must
not be reported as delinquent. This module flags delinquent months as
*worth checking against the servicer's own deferment and forbearance record*
and stops there. It never states which periods were in effect, because
asserting a pause date that turns out to be wrong would put a false statement
in a dispute letter over the consumer's signature.

This platform is not a student-loan servicer, not a loan holder, and not a
financial advisor. Nothing here is eligibility advice.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

# ── Who counts as a federal holder or servicer ─────────────────────────────
# Name fragments, matched case-insensitively against the furnisher. This list
# identifies loans that are *probably* federal so the federal-specific checks
# below fire on them. It is deliberately not used to assert that a loan is
# federal — a private loan serviced by one of these names would match too, and
# the consumer confirms the loan type at studentaid.gov, not here.
FEDERAL_SERVICER_MARKERS = (
    "dept of ed", "department of education", "us dept of ed", "usa funds",
    "aidvantage", "nelnet", "mohela", "edfinancial", "great lakes",
    "fedloan", "pheaa", "navient", "sallie mae", "cornerstone",
    "granite state", "osla", "ecsi", "maximus", "default resolution",
)

# Account-type strings Equifax and the other bureaus use for education debt.
EDUCATION_TYPE_MARKERS = ("education loan", "student loan", "educational")

# Status and narrative text that means the furnisher is reporting delinquency,
# independently of the payment grid.
DELINQUENCY_TEXT_MARKERS = (
    "past due", "delinquen", "default", "charge off", "charged off",
    "collection", "repossess", "120 days", "150 days", "180 days",
)

# Payment-grid keys that represent a delinquent month.
_LATE_KEYS = ("30", "60", "90", "120", "150", "180", "CO", "C")

# Two open dates this far apart or less are treated as the same disbursement
# window. Federal aid for one term is disbursed within days; anything inside a
# month is close enough to be worth asking about.
NEAR_IDENTICAL_DAYS = 31


# ── The standing disclaimer, carried in every payload ──────────────────────
# It travels with the data rather than living only in the UI, because the
# analyst, the letter preview and the print packet all read the payload and
# any one of them could otherwise surface a program name with no caveat
# attached.
FORGIVENESS_DISCLAIMER = (
    "This is a pointer to official sources, not eligibility advice. "
    "This platform is not a student-loan servicer, lender, or financial "
    "advisor, and it cannot determine whether you qualify for any program. "
    "Program rules, payment counts, dollar amounts and deadlines change; "
    "the only current source is studentaid.gov and your own loan servicer. "
    "Confirm everything there before acting."
)

VERIFY_AT = "https://studentaid.gov"


FORGIVENESS_PROGRAMS: dict[str, dict] = {
    # Each entry names a program and says what to bring to the conversation.
    # `generally_for` describes the population the program exists to serve, in
    # the loosest terms that are still useful. It is not a test, and the
    # wording deliberately avoids payment counts, dollar figures, employment
    # percentages and dates — all of which have changed and none of which this
    # module can verify.
    "pslf": {
        "name": "Public Service Loan Forgiveness (PSLF)",
        "generally_for":
            "Borrowers who work for government or certain non-profit employers "
            "while repaying federal loans. What counts as qualifying "
            "employment, a qualifying loan and a qualifying payment is set by "
            "the Department of Education and has changed more than once.",
        "verify_at": VERIFY_AT,
        "documents_to_gather": [
            "Employment records for every employer since you began repayment "
            "(dates, employer name, employer tax status)",
            "Your loan servicer's full payment history",
            "Any PSLF employer-certification forms you have previously filed",
        ],
        "note":
            "Use the official PSLF help tool at studentaid.gov to check "
            "employer and loan status rather than relying on any summary.",
    },
    "idr_forgiveness": {
        "name": "Income-Driven Repayment (IDR) forgiveness",
        "generally_for":
            "Borrowers repaying federal loans on an income-driven plan, where "
            "a remaining balance may be addressed after a long period of "
            "qualifying repayment. Which plans exist, and what counts toward "
            "them, has changed repeatedly.",
        "verify_at": VERIFY_AT,
        "documents_to_gather": [
            "Your servicer's payment history and the count of qualifying "
            "payments they have credited to you",
            "Records of any deferment or forbearance periods",
            "Tax returns or income documentation for the years in repayment",
        ],
        "note":
            "Ask your servicer in writing for their qualifying-payment count "
            "and compare it against your own records. Miscounts are the usual "
            "reason a borrower's total is lower than expected.",
    },
    "teacher": {
        "name": "Teacher Loan Forgiveness",
        "generally_for":
            "Borrowers who have taught in schools or educational service "
            "agencies serving low-income students. The service requirements, "
            "eligible subjects and amounts are set by the Department of "
            "Education.",
        "verify_at": VERIFY_AT,
        "documents_to_gather": [
            "Employment verification from each school, with dates",
            "Confirmation that each school appeared in the federal directory "
            "of low-income schools for the years you taught there",
            "Your teaching certification records",
        ],
        "note":
            "Teacher Loan Forgiveness and PSLF interact with each other. "
            "Check the interaction at studentaid.gov before filing either.",
    },
    "tpd": {
        "name": "Total and Permanent Disability (TPD) discharge",
        "generally_for":
            "Borrowers who are totally and permanently disabled, as determined "
            "through the process the Department of Education runs with the "
            "Social Security Administration, the VA, or a physician's "
            "certification.",
        "verify_at": VERIFY_AT,
        "documents_to_gather": [
            "VA disability determination, or SSA award notice, or a "
            "physician's certification, whichever applies to you",
            "Your loan list from studentaid.gov",
        ],
        "note":
            "There is a dedicated TPD servicer with its own process. Start at "
            "studentaid.gov rather than with your repayment servicer.",
    },
    "closed_school": {
        "name": "Closed School discharge",
        "generally_for":
            "Borrowers whose school closed while they were enrolled, or within "
            "a window after they withdrew. The length of that window and the "
            "conditions are set by the Department of Education.",
        "verify_at": VERIFY_AT,
        "documents_to_gather": [
            "Enrollment and withdrawal dates from the school or its records "
            "custodian",
            "Any notice you received about the closure",
            "Transcripts, if you completed the program elsewhere — completing "
            "the program elsewhere can affect this",
        ],
        "note":
            "The Department maintains a list of closed schools and their "
            "closure dates. Check yours against it at studentaid.gov.",
    },
    "borrower_defense": {
        "name": "Borrower Defense to Repayment",
        "generally_for":
            "Borrowers whose school misled them or engaged in misconduct "
            "related to the loans or the education it promised. The standard "
            "of proof and the application process have been rewritten several "
            "times.",
        "verify_at": VERIFY_AT,
        "documents_to_gather": [
            "Enrollment agreement, catalogue, and any advertising or "
            "recruiter claims about job placement, earnings, accreditation or "
            "credit transfer",
            "Emails, texts, or notes from conversations with recruiters",
            "Any state attorney general or CFPB action involving the school",
        ],
        "note":
            "Applications are filed with the Department of Education directly. "
            "Nobody needs to be paid to file one.",
    },
    "false_certification": {
        "name": "False Certification discharge",
        "generally_for":
            "Borrowers whose school falsely certified their eligibility for a "
            "loan — for example by signing for them, enrolling someone who "
            "could not benefit from the training, or using their identity "
            "without authorisation.",
        "verify_at": VERIFY_AT,
        "documents_to_gather": [
            "Your loan application and promissory note, and any signature on "
            "them that is not yours",
            "High-school diploma or equivalency record, if the school "
            "certified one you do not have",
            "A police report or FTC identity-theft report, if the loan was "
            "taken in your name without your knowledge",
        ],
        "note":
            "If the loan was taken in your name without your authorisation, "
            "that is also an identity-theft dispute on the credit report, "
            "which this platform can help with directly.",
    },
}


# ── Field access ───────────────────────────────────────────────────────────
# Items reach this module from three places: the structured Equifax parser,
# the Claude extractor, and the keyword scanner. They agree on most field
# names and disagree on a few, so every read goes through a tolerant getter
# rather than assuming one producer.

def _first(item: dict, *keys, default=""):
    for k in keys:
        v = item.get(k)
        if v not in (None, "", []):
            return v
    return default


def _money(item: dict, *keys) -> Optional[float]:
    """Read a money field that may arrive as a float, or as a string with $ and commas."""
    raw = _first(item, *keys, default=None)
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = str(raw).replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _date(item: dict, *keys) -> Optional[datetime]:
    raw = _first(item, *keys, default="")
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(raw)[:10], fmt)
        except ValueError:
            continue
    return None


def _furnisher(item: dict) -> str:
    return str(_first(item, "furnisher", "account_name", "creditor", "target")).strip()


def _norm_furnisher(item: dict) -> str:
    """Fold case and punctuation so 'DEPT OF ED/AIDVANTAGE' groups with itself."""
    name = _furnisher(item).lower()
    for ch in ("/", "\\", ".", ",", "-", "'", "#"):
        name = name.replace(ch, " ")
    return " ".join(name.split())


def _late_months(item: dict) -> int:
    grid = item.get("payment_grid") or {}
    if not isinstance(grid, dict):
        return 0
    return sum(int(grid.get(k, 0) or 0) for k in _LATE_KEYS)


def _text_blob(item: dict) -> str:
    codes = item.get("narrative_codes") or []
    if isinstance(codes, (list, tuple)):
        codes = " ".join(str(c) for c in codes)
    return " ".join([
        str(_first(item, "status", default="")),
        str(_first(item, "account_type", "type", default="")),
        str(codes),
        str(_first(item, "reason", default="")),
    ]).lower()


def is_student_loan(item: dict) -> bool:
    """
    Does this tradeline look like education debt?

    Three independent signals, any one of which is enough: the bureau's own
    account-type label, a known federal servicer or holder in the furnisher
    name, or the parser having already tagged it `student_loan`. Any one
    alone is imperfect — a servicer name can appear on private debt, and the
    account-type field is sometimes blank — but a miss here only means the
    federal-specific checks do not run, so the union is the right call.
    """
    atype = str(_first(item, "account_type", "type", default="")).lower()
    if any(m in atype for m in EDUCATION_TYPE_MARKERS):
        return True

    furnisher = _norm_furnisher(item)
    if any(m in furnisher for m in FEDERAL_SERVICER_MARKERS):
        return True

    for c in item.get("categories") or []:
        if isinstance(c, dict) and c.get("category") == "student_loan":
            return True

    return str(item.get("bucket") or "") == "student_loan"


def looks_federal(item: dict) -> bool:
    """
    Is the *holder* one of the federal servicers or the Department itself?

    Separate from `is_student_loan` because the federal-specific checks —
    deferment, forbearance, consolidation, the discharge programs — only make
    sense for federal debt. A private loan gets the duplicate and accuracy
    checks and none of the federal ones.
    """
    return any(m in _norm_furnisher(item) for m in FEDERAL_SERVICER_MARKERS)


def _has_delinquency(item: dict) -> bool:
    """
    Is the furnisher reporting delinquency on this line, by any route?

    A grid full of late codes, a status string that says past due, or a stated
    date of first delinquency each mean the same thing to a score, so each one
    counts. A line with none of the three is a clean line and the delinquency
    checks skip it.
    """
    if _late_months(item):
        return True
    if _date(item, "date_of_first_delinquency", "dofd"):
        return True
    blob = _text_blob(item)
    return any(m in blob for m in DELINQUENCY_TEXT_MARKERS)


def _label(item: dict) -> str:
    """Short human handle for an item inside evidence text."""
    acct = str(_first(item, "account_number", "account", default="")).strip()
    opened = _first(item, "date_opened", "opened", default="")
    bits = [b for b in (acct, f"opened {opened}" if opened else "") if b]
    return " / ".join(bits) or str(_first(item, "item_id", default="this account"))


def _cat(category: str, strength: str, evidence: str) -> dict:
    """A dispute-ready entry in exactly the shape `item['categories']` holds."""
    return {"category": category, "strength": strength, "evidence": evidence}


# ── Detectors ──────────────────────────────────────────────────────────────

def _detect_servicer_split(group: list[dict]) -> list[dict]:
    """
    Several tradelines from one holder, opened on the same or near-identical day.

    This is the check that most needs a steady hand. Federal aid is disbursed
    per academic term, and a subsidised and an unsubsidised loan for the same
    term are two genuinely distinct obligations that will share an open date.
    So N tradelines from one holder is not evidence of anything, and a same-day
    pair is the *expected* shape of one term's aid, not a smoking gun.

    What does warrant a written answer is the combination the consumer cannot
    resolve from the file: identical open dates, identical masked account
    numbers and identical $0 balances across lines, with nothing on the face of
    the report distinguishing them. That may be one obligation reported N
    times, or it may be N disbursements the bureau is displaying badly, and the
    furnisher is the only party who knows which.

    Strength is set by how much distinguishes the lines:
      moderate  the lines are indistinguishable on the report — same date, same
                masked number, same balance, and no differing original amount
      weak      the lines collide on date but report different original
                amounts, which is what separate disbursements normally look
                like; still worth confirming, not worth leading with
    """
    findings: list[dict] = []
    if len(group) < 2:
        return findings

    # Bucket by exact open date first. Exact collisions are the strong case.
    by_date: dict[str, list[dict]] = {}
    undated: list[dict] = []
    for it in group:
        d = _date(it, "date_opened", "opened")
        if d is None:
            undated.append(it)
        else:
            by_date.setdefault(d.strftime("%Y-%m-%d"), []).append(it)

    furnisher = _furnisher(group[0])

    for opened, lines in sorted(by_date.items()):
        if len(lines) < 2:
            continue

        accts = {str(_first(it, "account_number", "account", default="")).strip()
                 for it in lines}
        balances = {_money(it, "current_balance", "amount", "balance") for it in lines}
        originals = {_money(it, "highest_balance", "high_credit", "original_amount")
                     for it in lines}
        originals.discard(None)

        same_acct = len(accts) == 1 and bool(next(iter(accts)))
        all_zero = balances == {0.0}
        distinct_originals = len(originals) == len(lines) and len(originals) > 1

        # Differing original amounts are the ordinary per-disbursement pattern.
        # They do not clear the furnisher, but they are a real answer to the
        # question the finding asks, so the argument is weaker for it.
        strength = "weak" if distinct_originals else "moderate"

        detail = [
            f"{len(lines)} tradelines from {furnisher} all report a date opened "
            f"of {opened}"
        ]
        if same_acct:
            detail.append(
                f"and all display the same masked account number "
                f"{next(iter(accts))}")
        if all_zero:
            detail.append("and all report a $0 balance")
        if distinct_originals:
            amounts = ", ".join(
                f"${a:,.0f}" for a in sorted(originals, reverse=True))
            detail.append(
                f"though the original amounts differ ({amounts}), which is "
                f"consistent with separate disbursements")

        evidence = (
            ", ".join(detail)
            + ". Federal aid is commonly disbursed per academic term and "
              "reported one line per disbursement, so separate lines are not "
              "by themselves an error. Nothing on the face of the report, "
              "however, distinguishes these lines from one another. Under "
              "15 U.S.C. § 1681e(b) and § 1681s-2 the furnisher is asked to "
              "state, in writing, whether these are distinct obligations with "
              "distinct account numbers and disbursement dates, or one "
              "obligation reported more than once, and to correct the file if "
              "it is the latter."
        )

        findings.append({
            "code": "servicer_split_duplicates",
            "furnisher": furnisher,
            "item_ids": [it.get("item_id") for it in lines],
            "summary": (
                f"{len(lines)} {furnisher} tradelines share an open date of "
                f"{opened}"),
            "detail": evidence,
            "facts": {
                "date_opened": opened,
                "line_count": len(lines),
                "same_masked_account_number": same_acct,
                "all_zero_balance": all_zero,
                "distinct_original_amounts": distinct_originals,
            },
            "categories": [_cat("duplicate", strength, evidence)],
        })

    # Near-identical, but not identical, open dates across the remaining lines.
    # Reported separately and always weak: a few days apart is what a real
    # two-part disbursement looks like.
    dated = sorted(
        ((d, lines) for d, lines in by_date.items() if len(lines) == 1),
        key=lambda kv: kv[0])
    for i in range(len(dated) - 1):
        d1 = datetime.strptime(dated[i][0], "%Y-%m-%d")
        d2 = datetime.strptime(dated[i + 1][0], "%Y-%m-%d")
        gap = (d2 - d1).days
        if 0 < gap <= NEAR_IDENTICAL_DAYS:
            lines = dated[i][1] + dated[i + 1][1]
            evidence = (
                f"Two {furnisher} tradelines report open dates {gap} days apart "
                f"({dated[i][0]} and {dated[i + 1][0]}). Disbursements for one "
                f"term can fall days apart, so this is not by itself an error; "
                f"the furnisher is asked to confirm that these are distinct "
                f"obligations and not one loan split across two tradelines."
            )
            findings.append({
                "code": "near_identical_open_dates",
                "furnisher": furnisher,
                "item_ids": [it.get("item_id") for it in lines],
                "summary": (
                    f"Two {furnisher} tradelines opened {gap} days apart"),
                "detail": evidence,
                "facts": {"gap_days": gap,
                          "dates": [dated[i][0], dated[i + 1][0]]},
                "categories": [_cat("duplicate", "weak", evidence)],
            })

    if undated:
        evidence = (
            f"{len(undated)} {furnisher} tradelines report no date opened at "
            f"all. Without it the reporting window under 15 U.S.C. § 1681c "
            f"cannot be checked and the line cannot be distinguished from the "
            f"other tradelines this furnisher reports."
        )
        findings.append({
            "code": "missing_open_date",
            "furnisher": furnisher,
            "item_ids": [it.get("item_id") for it in undated],
            "summary": f"{len(undated)} {furnisher} tradelines have no date opened",
            "detail": evidence,
            "facts": {"line_count": len(undated)},
            "categories": [_cat("duplicate", "weak", evidence)],
        })

    return findings


def _detect_zero_balance_with_delinquency(item: dict) -> Optional[dict]:
    """
    A $0 balance reported alongside live delinquency markers.

    Historical late payments on a loan that was later paid off are accurate
    reporting and this check is not about those. What it targets is the
    *status* field: a line that owes nothing but is still described as past
    due, in default, or over 120 days delinquent, is describing a condition
    that cannot be true of a zero balance. A loan that has been paid,
    consolidated, discharged or transferred away has a terminal status, and
    the furnisher has to pick one and report it.

    The distinction matters to a score, not just to a pedant: a current
    delinquency status is read as an active problem, where the same account
    reported as paid-and-closed with historical lates is not.
    """
    balance = _money(item, "current_balance", "amount", "balance")
    if balance is None or balance > 0:
        return None
    if not _has_delinquency(item):
        return None

    blob = _text_blob(item)
    late = _late_months(item)
    dofd = _first(item, "date_of_first_delinquency", "dofd", default="")
    status = str(_first(item, "status", default="")).strip()

    parts = [f"{_furnisher(item)} reports a $0 balance on {_label(item)}"]
    if status:
        parts.append(f"while the status field reads '{status}'")
    if late:
        parts.append(f"and the payment grid carries {late} delinquent months")
    if dofd:
        parts.append(f"with a date of first delinquency of {dofd}")

    # Called out because each of these has a different correct terminal status,
    # and the furnisher choosing the wrong one is the error being disputed.
    evidence = (
        ", ".join(parts)
        + ". A balance of zero means the obligation is no longer outstanding — "
          "whether it was paid, consolidated into another loan, discharged, or "
          "transferred to another holder. Each of those has its own correct "
          "terminal status, and none of them is an open delinquency. The "
          "furnisher is asked under 15 U.S.C. § 1681e(b) and § 1681s-2(a) to "
          "state which one occurred and on what date, and to report the status "
          "that corresponds to it. If the balance moved to another holder, the "
          "file must also show that this line is not a second copy of a debt "
          "reported elsewhere."
    )

    return {
        "code": "zero_balance_with_delinquency",
        "furnisher": _furnisher(item),
        "item_ids": [item.get("item_id")],
        "summary": (
            f"{_furnisher(item)} reports $0 owed but still reports delinquency"),
        "detail": evidence,
        "facts": {
            "balance": balance,
            "delinquent_months": late,
            "date_of_first_delinquency": dofd,
            "status": status,
            "transfer_language_present": (
                "transfer" in blob or "sold" in blob),
        },
        "categories": [_cat("status_inaccuracy", "moderate", evidence)],
    }


def _detect_pause_period_check(item: dict) -> Optional[dict]:
    """
    Delinquent months that should be checked against deferment and forbearance.

    Federal repayment is interrupted routinely — in-school deferment, economic
    hardship forbearance, administrative forbearance during a servicer
    transfer, and department-level pauses. A month inside any of those is a
    month when no payment was due, and reporting it as late is inaccurate.

    This module does not know which periods applied to this consumer, and it
    deliberately does not guess. Stating a pause window that turns out to be
    wrong would put a false statement in a letter over the consumer's
    signature, and the consumer can get the true answer in one request: the
    servicer's own deferment and forbearance history. So the finding names the
    months the report treats as delinquent and hands the consumer the question
    to ask, rather than answering it for them.

    The dispute category emitted is `late_payment` at moderate — above the
    parser's default weak, because a specific, checkable contradiction has been
    identified rather than a general request to verify.
    """
    if not looks_federal(item):
        return None
    late = _late_months(item)
    dofd_dt = _date(item, "date_of_first_delinquency", "dofd")
    if not late and not dofd_dt:
        return None

    dofd = _first(item, "date_of_first_delinquency", "dofd", default="")
    window = f" beginning {dofd}" if dofd else ""

    evidence = (
        f"{_furnisher(item)} reports {late or 'multiple'} delinquent months on "
        f"{_label(item)}{window}. Federal student loans are subject to "
        f"deferment, forbearance, administrative forbearance during servicer "
        f"transfers, and department-level payment pauses, and a month in which "
        f"no payment was due cannot be reported as a late payment. The "
        f"furnisher is asked to produce the deferment and forbearance history "
        f"for this account covering every month it reports as delinquent, and "
        f"to delete any month falling inside a period when payment was not "
        f"required, under 15 U.S.C. § 1681s-2(a)(1)."
    )

    return {
        "code": "verify_against_forbearance_record",
        "furnisher": _furnisher(item),
        "item_ids": [item.get("item_id")],
        "summary": (
            "Delinquent months reported on a federal loan — check them against "
            "your servicer's deferment and forbearance record"),
        "detail": evidence,
        "facts": {
            "delinquent_months": late,
            "date_of_first_delinquency": dofd,
        },
        # Said plainly so no downstream surface can turn this into a claim
        # about a specific policy window.
        "consumer_action": (
            "Request your full deferment and forbearance history from your "
            "servicer in writing, and download your loan and payment history "
            f"from {VERIFY_AT}. Compare them month by month against the "
            "delinquent months on this tradeline. This platform does not know "
            "which pause periods applied to your loans and does not assert "
            "any — your servicer's record is the answer."),
        "asserts_no_policy_dates": True,
        "categories": [_cat("late_payment", "moderate", evidence)],
    }


def _detect_missing_dofd(item: dict) -> Optional[dict]:
    """
    A line that looks delinquent but states no date of first delinquency.

    The DOFD is what starts the seven-year clock under 15 U.S.C. § 1681c(a).
    Without it the consumer cannot check whether the item is already obsolete,
    and the furnisher is required to report it. The absence is the violation,
    independent of whether the underlying delinquency is accurate.

    Note what does *not* trigger this: a clean line with no DOFD. Eight paid,
    zero-balance loans reporting no delinquency date are reporting correctly,
    and flagging them would be noise that costs the real findings their
    credibility.
    """
    if _date(item, "date_of_first_delinquency", "dofd"):
        return None

    late = _late_months(item)
    blob = _text_blob(item)
    text_signal = any(m in blob for m in DELINQUENCY_TEXT_MARKERS)
    if not late and not text_signal:
        return None

    reason = (f"{late} delinquent months in the payment grid" if late
              else f"a status of '{_first(item, 'status', default='')}'")
    evidence = (
        f"{_furnisher(item)} reports {reason} on {_label(item)} but states no "
        f"date of first delinquency. Under 15 U.S.C. § 1681c(a) the reporting "
        f"period runs from that date, and under 15 U.S.C. § 1681s-2(a)(5) the "
        f"furnisher is required to report it. Without it neither the consumer "
        f"nor the bureau can determine whether this item is already past its "
        f"reporting period. The furnisher is asked to supply the date or "
        f"delete the delinquency."
    )

    return {
        "code": "missing_dofd_on_delinquent_line",
        "furnisher": _furnisher(item),
        "item_ids": [item.get("item_id")],
        "summary": (
            f"{_furnisher(item)} reports delinquency with no date of first "
            f"delinquency"),
        "detail": evidence,
        "facts": {"delinquent_months": late, "text_signal": text_signal},
        "categories": [_cat("re_aging", "moderate", evidence)],
    }


def _detect_possible_consolidation(group: list[dict]) -> Optional[dict]:
    """
    A later line from the same holder whose size is near the sum of the earlier ones.

    Context, not a dispute ground. When a cluster of zero-balance lines is
    followed by one newer line of roughly their combined size, the likely story
    is a consolidation: the old loans were paid off by the new one, which is
    exactly why they report $0. Surfacing it stops the consumer disputing eight
    correctly-reported paid loans as duplicates, and it tells them which single
    line actually matters.

    Carries no dispute categories on purpose. If the reading is right, the
    reporting is right, and there is nothing here to dispute.
    """
    if len(group) < 3:
        return None

    dated = [(d, it) for it in group
             if (d := _date(it, "date_opened", "opened")) is not None]
    if len(dated) < 3:
        return None
    dated.sort(key=lambda kv: kv[0])

    newest_date, newest = dated[-1]
    earlier = [it for _, it in dated[:-1]]

    # The candidate has to be the delinquent, distinguishable one; a cluster of
    # equals is not a consolidation story.
    earlier_zero = [it for it in earlier
                    if _money(it, "current_balance", "amount", "balance") == 0.0]
    if len(earlier_zero) < 2:
        return None

    total = 0.0
    for it in earlier_zero:
        amt = _money(it, "highest_balance", "high_credit", "original_amount")
        if amt is None:
            return None
        total += amt
    new_amt = _money(newest, "highest_balance", "high_credit", "original_amount")
    if not total or new_amt is None:
        return None

    ratio = new_amt / total
    # Wide band on purpose. A consolidation capitalises accrued interest, so
    # the new principal runs above the sum; a partial consolidation runs below.
    # Anything in this range is worth raising as a question and nothing outside
    # it is.
    if not 0.75 <= ratio <= 1.75:
        return None

    return {
        "code": "possible_consolidation",
        "furnisher": _furnisher(newest),
        "item_ids": [newest.get("item_id")],
        "summary": (
            f"The {newest_date.strftime('%Y-%m-%d')} tradeline is close in size "
            f"to the combined total of the {len(earlier_zero)} older $0 lines"),
        "detail": (
            f"{len(earlier_zero)} older {_furnisher(newest)} tradelines report "
            f"$0 balances with original amounts totalling ${total:,.0f}, and a "
            f"later line opened {newest_date.strftime('%Y-%m-%d')} reports an "
            f"original amount of ${new_amt:,.0f} ({ratio:.2f}x the total). That "
            f"pattern is consistent with the older loans having been "
            f"consolidated into the newer one, which would make their $0 "
            f"balances correct rather than duplicative. Confirm the "
            f"consolidation date and the list of loans it paid off at "
            f"{VERIFY_AT} before disputing the older lines — if they were "
            f"consolidated, the line worth attention is the newer one."),
        "facts": {
            "older_zero_lines": len(earlier_zero),
            "older_total": round(total, 2),
            "newer_amount": round(new_amt, 2),
            "ratio": round(ratio, 3),
            "newer_opened": newest_date.strftime("%Y-%m-%d"),
        },
        # Deliberately empty: if this reading is correct, nothing here is wrong.
        "categories": [],
    }


# ── Public API ─────────────────────────────────────────────────────────────

def analyze_student_loans(items: list[dict]) -> dict:
    """
    Read a set of tradelines for the federal-loan patterns no single line shows.

    Takes the parsed `accounts` list (or any list of items carrying the same
    fields) and returns findings keyed both as a flat list — for review and
    display — and per item id, in the exact `{category, strength, evidence}`
    shape `item['categories']` already holds, so a finding can be appended
    straight onto an item and flow into the existing letter generator with no
    adapter in between.

    Returns:
        is_student_loan_file  whether any education debt was found at all
        loan_count            how many education tradelines
        federal_count         how many of those name a federal holder/servicer
        servicers             {furnisher: line count}
        findings              flat list, each with code, summary, detail,
                              item_ids, facts, and dispute categories
        findings_by_item      {item_id: [{category, strength, evidence}, ...]}
        forgiveness           the program directory plus the standing
                              disclaimer, so no consumer sees a program name
                              without the caveat attached
        disclaimer            the standing disclaimer, repeated at top level
    """
    items = items or []
    loans = [it for it in items if is_student_loan(it)]

    payload: dict = {
        "is_student_loan_file": bool(loans),
        "loan_count": len(loans),
        "federal_count": sum(1 for it in loans if looks_federal(it)),
        "servicers": {},
        "findings": [],
        "findings_by_item": {},
        "forgiveness": {
            "disclaimer": FORGIVENESS_DISCLAIMER,
            "verify_at": VERIFY_AT,
            "programs": FORGIVENESS_PROGRAMS,
            "is_eligibility_advice": False,
            "platform_role": (
                "This platform disputes credit-report inaccuracies. It is not "
                "a student-loan servicer, loan holder, or financial advisor."),
        },
        "disclaimer": FORGIVENESS_DISCLAIMER,
    }
    if not loans:
        return payload

    # Group by holder. Every cross-line check is a within-holder check: two
    # lines from two different servicers colliding on a date means nothing.
    groups: dict[str, list[dict]] = {}
    for it in loans:
        groups.setdefault(_norm_furnisher(it), []).append(it)
    payload["servicers"] = {
        _furnisher(g[0]): len(g) for g in groups.values()}

    findings: list[dict] = []

    for group in groups.values():
        findings.extend(_detect_servicer_split(group))
        consolidation = _detect_possible_consolidation(group)
        if consolidation:
            findings.append(consolidation)

    for it in loans:
        for detector in (_detect_zero_balance_with_delinquency,
                         _detect_pause_period_check,
                         _detect_missing_dofd):
            found = detector(it)
            if found:
                findings.append(found)

    # Strongest argument first, so a reviewer reading the top of the list is
    # reading the case rather than the footnotes.
    rank = {"moderate": 0, "weak": 1}

    def _best(f):
        strengths = [c["strength"] for c in f.get("categories") or []]
        if not strengths:
            return 2  # context-only findings sort last
        return min(rank.get(s, 1) for s in strengths)

    findings.sort(key=_best)
    payload["findings"] = findings

    by_item: dict[str, list[dict]] = {}
    for f in findings:
        for iid in f.get("item_ids") or []:
            if not iid:
                continue
            for c in f.get("categories") or []:
                by_item.setdefault(iid, []).append(dict(c))
    payload["findings_by_item"] = by_item

    return payload


def attach_findings(items: list[dict], analysis: Optional[dict] = None) -> list[dict]:
    """
    Merge the student-loan findings onto the items themselves, in place.

    The letter generator reads `item['categories']`, so a finding that stays in
    a side payload never reaches a letter. This appends each finding into the
    item it belongs to, using the same merge rule the parser uses: one entry
    per category, additional facts folded into the evidence rather than added
    as a second argument. Two observations about the same category are one
    argument with two supports — treating them as two would inflate the
    combined removal probability in `scoring.combine`, which assumes the
    grounds it is given are distinct.

    Where a category already exists on the item, the stronger strength wins.
    Returns the same list, for chaining.
    """
    analysis = analysis or analyze_student_loans(items)
    by_item = analysis.get("findings_by_item") or {}
    if not by_item:
        return items

    order = {"strong": 0, "moderate": 1, "weak": 2}

    for item in items:
        new = by_item.get(item.get("item_id"))
        if not new:
            continue

        existing = item.get("categories") or []
        merged: dict[str, dict] = {c["category"]: dict(c) for c in existing
                                   if isinstance(c, dict) and c.get("category")}

        for c in new:
            cid = c["category"]
            if cid in merged:
                prior = merged[cid]
                if prior["evidence"] != c["evidence"]:
                    prior["evidence"] += f"; also, {c['evidence']}"
                if order.get(c["strength"], 2) < order.get(prior["strength"], 2):
                    prior["strength"] = c["strength"]
            else:
                merged[cid] = dict(c)

        cats = sorted(merged.values(), key=lambda c: order.get(c["strength"], 2))
        item["categories"] = cats
        item["category_count"] = len(cats)
        if cats:
            item["strongest"] = cats[0]["strength"]
            item["bucket"] = cats[0]["category"]

    return items


def forgiveness_signals(items: list[dict],
                        profile: Optional[dict] = None) -> list[dict]:
    """
    Which programs are worth the consumer *asking about*, based on the file only.

    This reads the credit report and nothing else. The report shows how many
    federal loans there are, how long they have been open, and whether any are
    delinquent. It does not show employment, income, disability status, or
    whether a school closed — which is to say it does not show any of the
    things the programs actually turn on.

    So every signal here is a prompt to go and check, never a finding of
    eligibility. Each entry says what in the file prompted it, names the
    program, and points at studentaid.gov. `qualifies` is not a field this
    function returns, and should not be added: nothing in a credit report can
    establish it.

    `profile` is accepted and read defensively — it may be empty, and no signal
    depends on it. If a consumer has told the platform something relevant (an
    employer, a school closure), it sharpens which programs get surfaced first
    without ever changing them into a determination.
    """
    profile = profile or {}
    loans = [it for it in (items or []) if is_student_loan(it)]
    federal = [it for it in loans if looks_federal(it)]
    if not federal:
        return []

    signals: list[dict] = []

    def add(key: str, observed: str, action: str):
        prog = FORGIVENESS_PROGRAMS[key]
        signals.append({
            "program_key": key,
            "program": prog["name"],
            "observed_in_report": observed,
            "worth_checking_because": prog["generally_for"],
            "what_to_do": action,
            "documents_to_gather": prog["documents_to_gather"],
            "verify_at": prog["verify_at"],
            # Repeated per signal, not just once at the top. Any surface can
            # render a single signal on its own, and it must carry its caveat.
            "is_eligibility_determination": False,
            "disclaimer": FORGIVENESS_DISCLAIMER,
        })

    count = len(federal)
    plural = "loan" if count == 1 else "loans"

    # Baseline: federal debt is present, so the two general programs exist and
    # the consumer may not know it. No further condition — this is the "did
    # anyone tell you these exist" signal.
    add("idr_forgiveness",
        f"{count} federal student {plural} appear on this report.",
        "Log in at studentaid.gov, confirm which of your loans are federal, and "
        "ask your servicer in writing which repayment plan you are on and how "
        "many qualifying payments they have credited to you. Worth checking "
        "with your servicer — this platform cannot tell you whether you "
        "qualify.")

    add("pslf",
        f"{count} federal student {plural} appear on this report.",
        "If you have worked for a government agency or a non-profit at any "
        "point during repayment, run the official PSLF help tool at "
        "studentaid.gov and file employer certification for every employer. "
        "Worth checking with your servicer — this platform cannot tell you "
        "whether your employment qualifies.")

    # Long history: a portfolio opened many years ago may have accumulated
    # repayment time the consumer has never had counted.
    opens = [d for it in federal
             if (d := _date(it, "date_opened", "opened")) is not None]
    if opens:
        oldest = min(opens)
        years = (datetime.now() - oldest).days / 365.25
        if years >= 10:
            signals[0]["observed_in_report"] += (
                f" The oldest opened {oldest.strftime('%Y-%m-%d')}, roughly "
                f"{years:.0f} years ago. Long-standing federal debt is worth a "
                f"specific question about how much of that time has been "
                f"credited as qualifying repayment.")

    # Delinquency or default markers: the discharge programs and the
    # rehabilitation route are the ones to ask about, and only if the
    # circumstances behind them are real.
    if any(_has_delinquency(it) for it in federal):
        for key, observed in (
            ("tpd", "A federal loan on this report carries delinquency or "
                    "default markers."),
            ("borrower_defense", "A federal loan on this report carries "
                                 "delinquency or default markers."),
            ("closed_school", "A federal loan on this report carries "
                              "delinquency or default markers."),
            ("false_certification", "A federal loan on this report carries "
                                    "delinquency or default markers."),
        ):
            add(key, observed,
                "This is listed because delinquency is on the file, not "
                "because anything in the report suggests you meet this "
                "program's conditions — the report does not show disability, "
                "school conduct, or school closure. If the circumstances "
                "described apply to you, start at studentaid.gov. Also ask "
                "your servicer about rehabilitation and consolidation options "
                "for a defaulted loan.")

    # Teaching is not visible in a credit report at all, so this one only
    # surfaces when the consumer has already told the platform.
    occupation = " ".join(str(profile.get(k, "")) for k in
                          ("occupation", "employer", "employment")).lower()
    if any(w in occupation for w in ("teach", "school", "educator", "isd")):
        add("teacher",
            "You have told this platform about employment in education. "
            "Nothing in the credit report itself shows employment.",
            "Confirm at studentaid.gov whether the schools you taught at "
            "appeared in the federal low-income schools directory for the "
            "years you were there, and check how Teacher Loan Forgiveness "
            "interacts with PSLF before filing either. Worth checking with "
            "your servicer.")

    return signals


def summary_lines(analysis: dict) -> list[str]:
    """One line per finding, for the review screen and the print packet."""
    if not analysis.get("is_student_loan_file"):
        return []
    out = [
        f"{analysis['loan_count']} student loan tradelines "
        f"({analysis['federal_count']} from a federal holder or servicer)"
    ]
    out.extend(f"{f['code']}: {f['summary']}" for f in analysis.get("findings", []))
    return out
