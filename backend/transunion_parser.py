"""
TransUnion export parser.

Written against a real 38-tradeline TransUnion consumer disclosure, not a
synthetic fixture. Until this existed TransUnion fell through to the keyword
scanner, which read the report's own section headings as creditors and
produced items whose furnisher was `Addresses` and whose account was
`Unknown` — twenty of them, from a file with eighteen genuinely adverse
tradelines in it.

Three things about the format matter, and all three break a naive reader:

  * **The block header is two labels then two values.** `Account Name` and
    `Account Number` sit on consecutive lines, and only then do the furnisher
    and the masked number follow. Reading label/value pairs in order gets the
    furnisher into the account-number field.

  * **Values wrap mid-word.** PDF extraction splits tokens across lines:
    `Installmen` + `t Account`, `>Charge-of` + `f<`, `Maximum Delinquenc` +
    `y of 90 days`. Continuation lines join with no separator, which is why
    this reads a value as "everything until the next known label" rather than
    "the next line".

  * **`>brackets<` mark adverse information.** The report says so itself:
    "we have added >brackets< to those items". `>Charge-off<` is the bureau's
    own adverse flag, and it survives into `Pay Status`.

TransUnion is also the only one of the three that prints the furnisher's
mailing address and phone on every tradeline — exactly what a § 1681i(a)(7)
method-of-verification demand needs to name.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from money import money_str

# Every label the export uses. A value runs from its label to the next one,
# which is what makes wrapped values recoverable.
_LABELS = frozenset({
    "Account Name", "Account Number", "Address", "Phone", "Monthly Payment",
    "Date Opened", "Responsibility", "Account Type", "Loan Type", "Balance",
    "Date Updated", "Payment Received", "Last Payment Made",
    "Original Creditor", "Pay Status", "Terms", "Date Closed", "Remarks",
    "High Balance", "Credit Limit", "Maximum Delinquency Note",
    "High Balance (Hist.)", "Payment History", "Bureau Code",
    "Estimated month and year this item will be removed",
})

# Page furniture that lands inside a block when a tradeline spans a page.
_PAGE_NOISE = re.compile(r"\b\d{1,3}\s*/\s*\d{1,3}\b")

_SECTION_ADVERSE = "Accounts with Adverse"
_SECTION_SATISFACTORY = "Satisfactory Accounts"

# Pay Status prose -> dispute category. Ordered: the first hit wins, so the
# more specific statuses are listed before the general ones.
_STATUS_RULES = [
    ("charge-off", "charge_off"),
    ("charged off", "charge_off"),
    ("collection", "collection"),
    ("placed for collection", "collection"),
    ("repossession", "repossession"),
    ("foreclosure", "foreclosure"),
    ("bankruptcy", "bankruptcy"),
    ("late", "late_payment"),
    ("past due", "late_payment"),
    ("settled", "status_inaccuracy"),
    ("paid, closed", ""),
    ("paying as agreed", ""),
    ("current", ""),
]

_COLLECTOR_HINTS = (
    "COLLECT", "RECOVERY", "PORTFOLIO", "ASSET", "LVNV", "MIDLAND",
    "RESURGENT", "CBE", "TRANSWORLD", "CREDENCE", "ENHANCED", "RECEIVABLE",
)

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def _clean(lines: list[str]) -> list[str]:
    return [ln.strip() for ln in lines]


def _is_collector(name: str) -> bool:
    up = (name or "").upper()
    return any(h in up for h in _COLLECTOR_HINTS)


def _us_date(raw: str) -> str:
    """MM/DD/YYYY -> ISO. Returns '' when absent or unparseable."""
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw or "")
    if not m:
        return ""
    mm, dd, yyyy = m.groups()
    try:
        return datetime(int(yyyy), int(mm), int(dd),
                        tzinfo=timezone.utc).strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _month_year(raw: str) -> str:
    """MM/YYYY -> ISO first-of-month, which is the precision on offer."""
    m = re.search(r"(\d{1,2})/(\d{4})", raw or "")
    if m:
        mm, yyyy = m.groups()
        try:
            return datetime(int(yyyy), int(mm), 1,
                            tzinfo=timezone.utc).strftime("%Y-%m-%d")
        except ValueError:
            return ""
    m = re.search(r"([A-Za-z]{3})\w*\s+(\d{4})", raw or "")
    if m and m.group(1).lower() in _MONTHS:
        return f"{int(m.group(2)):04d}-{_MONTHS[m.group(1).lower()]:02d}-01"
    return ""


def looks_like_transunion(text: str) -> bool:
    """Cheap sniff so the router can pick a parser without trying each one."""
    markers = (
        "Your TransUnion Credit Report",
        "transunion.com/dispute",
        "Estimated month and year this item will be removed",
        "Accounts with Adverse Information",
    )
    return sum(1 for m in markers if m in text) >= 2


def _fields(block: list[str]) -> dict[str, str]:
    """
    Label -> value for one tradeline block.

    A value is every line between its label and the next known label, joined
    with no separator because the export wraps mid-word. `Account Name` and
    `Account Number` are handled by the caller, since their labels are
    adjacent and their values follow together.
    """
    out: dict[str, str] = {}
    i = 0
    while i < len(block):
        label = block[i]
        if label not in _LABELS:
            i += 1
            continue
        parts: list[str] = []
        j = i + 1
        while j < len(block) and block[j] not in _LABELS:
            piece = _PAGE_NOISE.sub("", block[j]).strip()
            if piece:
                parts.append(piece)
            j += 1
        out[label] = "".join(parts)
        i = j
    return out


def _name_and_number(block: list[str]) -> tuple[str, str]:
    """
    The furnisher and the masked account number.

    Their labels are consecutive — `Account Name` then `Account Number` — and
    both values follow after. Reading them as ordinary label/value pairs puts
    the furnisher's name into the account-number field.
    """
    try:
        n_idx = block.index("Account Name")
        a_idx = block.index("Account Number", n_idx)
    except ValueError:
        return "", ""
    if a_idx != n_idx + 1:
        # Not the adjacent-pair layout; fall back to reading them separately.
        f = _fields(block)
        return f.get("Account Name", ""), f.get("Account Number", "")

    values: list[str] = []
    k = a_idx + 1
    while k < len(block) and block[k] not in _LABELS and len(values) < 2:
        piece = _PAGE_NOISE.sub("", block[k]).strip()
        if piece:
            values.append(piece)
        k += 1
    name = values[0] if values else ""
    number = values[1] if len(values) > 1 else ""
    return name, number


def _category_for(status: str, furnisher: str, remarks: str) -> str:
    """
    Dispute category from the Pay Status, with the collector test applied.

    `>brackets<` are the bureau's own adverse marker and are stripped before
    matching — the text inside them is the status.
    """
    low = re.sub(r"[><]", "", f"{status} {remarks}").lower()
    for needle, bucket in _STATUS_RULES:
        if needle in low:
            if not bucket:
                return ""
            if bucket in ("collection", "charge_off") and _is_collector(furnisher):
                return "debt_buyer"
            return bucket
    return ""


def _falloff(removal: str) -> str:
    """
    Where the account sits against its own stated removal date.

    TransUnion publishes the date the item comes off, which makes obsolescence
    arithmetic rather than inference: past that date it may not be reported at
    all, § 1681c(a) regardless of accuracy.
    """
    if not removal:
        return ""
    try:
        when = datetime.strptime(removal, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return ""
    days = (when - datetime.now(timezone.utc)).days
    if days <= 0:
        return "expired"
    if days <= 180:
        return "closing"
    return "within_window"


def _accounts(text: str) -> list[dict]:
    lines = _clean(text.splitlines())
    starts = [i for i, ln in enumerate(lines) if ln == "Account Name"]
    if not starts:
        return []

    try:
        satisfactory_at = next(
            i for i, ln in enumerate(lines) if ln.startswith(_SECTION_SATISFACTORY))
    except StopIteration:
        satisfactory_at = len(lines)

    out: list[dict] = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        block = lines[start:end]
        name, number = _name_and_number(block)
        if not name:
            continue
        f = _fields(block)
        removal = _month_year(f.get(
            "Estimated month and year this item will be removed", ""))
        out.append({
            "furnisher": name,
            "account": number,
            "account_type": f.get("Account Type", ""),
            "loan_type": f.get("Loan Type", ""),
            "responsibility": f.get("Responsibility", ""),
            "date_opened": _us_date(f.get("Date Opened", "")),
            "date_closed": _us_date(f.get("Date Closed", "")),
            "date_updated": _us_date(f.get("Date Updated", "")),
            "last_payment": _us_date(f.get("Last Payment Made", "")),
            "status": re.sub(r"[><]", "", f.get("Pay Status", "")).strip(),
            "balance": money_str(f.get("Balance", "")),
            "high_balance": money_str(f.get("High Balance", "")),
            "credit_limit": money_str(f.get("Credit Limit", "")),
            "original_creditor": f.get("Original Creditor", "").strip(),
            "remarks": f.get("Remarks", ""),
            "max_delinquency": f.get("Maximum Delinquency Note", ""),
            "on_record_until": removal,
            # The report's own adverse marker, twice over: the section it sits
            # in, and the brackets around its status.
            "adverse": start < satisfactory_at or ">" in f.get("Pay Status", ""),
            # Uniquely TransUnion: the furnisher's own contact details, which
            # is what a method-of-verification demand has to name.
            "furnisher_address": f.get("Address", ""),
            "furnisher_phone": f.get("Phone", ""),
        })
    return out


def _grounds(a: dict, category: str) -> list[dict]:
    """Every independent ground this tradeline supports, not just the first."""
    grounds: list[dict] = []

    def add(cat: str, strength: str, evidence: str) -> None:
        grounds.append({"category": cat, "strength": strength, "evidence": evidence})

    if category:
        add(category, "strong" if a["adverse"] else "moderate",
            a["status"] or "reported as adverse by the bureau's own marker")

    falloff = _falloff(a["on_record_until"])
    if falloff == "expired":
        add("obsolete", "strong",
            f"the bureau states this item is removed by {a['on_record_until']}, "
            f"which has passed")
    elif falloff == "closing":
        add("obsolete", "moderate",
            f"the bureau's own removal date is {a['on_record_until']}")

    # A collection tradeline that never names who it bought the debt from
    # cannot show the chain a consumer is entitled to see.
    if category in ("collection", "debt_buyer") and not a["original_creditor"]:
        add("debt_buyer", "moderate",
            "reported by a collection entity with no original creditor named, "
            "so the chain of assignment cannot be verified from the file")

    # Closed and still carrying a balance is a contradiction on the face of it.
    if a["date_closed"] and a["balance"] not in ("", "0.00"):
        add("balance_inaccuracy", "moderate",
            f"the account is reported closed on {a['date_closed']} while still "
            f"showing a balance of {a['balance']}")

    return grounds


def parse_transunion(text: str) -> list[dict]:
    """
    Dispute items from a TransUnion export, in the shape the engine consumes.

    Only adverse tradelines become items. A satisfactory account is not a
    dispute, and manufacturing one for a healthy tradeline is the failure this
    parser exists to end.
    """
    items: list[dict] = []
    for a in _accounts(text):
        category = _category_for(a["status"], a["furnisher"], a["remarks"])
        falloff = _falloff(a["on_record_until"])
        if not a["adverse"] and not category and falloff != "expired":
            continue

        grounds = _grounds(a, category)
        if not grounds:
            continue

        items.append({
            "bucket": category or grounds[0]["category"],
            "type": "bureau",
            "target": "TransUnion",
            "furnisher": a["furnisher"],
            "account": a["account"],
            "amount": a["balance"],
            "opened": a["date_opened"],
            "highest_balance": a["high_balance"],
            "original_creditor": a["original_creditor"],
            "account_type": a["account_type"],
            "responsibility": a["responsibility"],
            "status_text": a["status"],
            "on_record_until": a["on_record_until"],
            "falloff_status": falloff,
            "furnisher_address": a["furnisher_address"],
            "furnisher_phone": a["furnisher_phone"],
            "categories": grounds,
            "category_count": len(grounds),
            "reason": a["status"] or "This item is inaccurate as reported.",
            "confidence": "high",
            # TransUnion publishes a removal date rather than a date of first
            # delinquency. Saying so plainly stops anything downstream from
            # inferring one — an invented DOFD in the field that sets the
            # § 1681c clock is the worst thing this pipeline can print.
            "dofd_disclosed": False,
        })
    return items


def report_summary(text: str) -> dict:
    """File-level context the analyst reads without re-parsing the PDF."""
    accounts = _accounts(text)
    adverse = [a for a in accounts if a["adverse"]]
    return {
        "bureau": "TransUnion",
        "tradelines": len(accounts),
        "adverse": len(adverse),
        "with_original_creditor": sum(1 for a in accounts if a["original_creditor"]),
        "with_removal_date": sum(1 for a in accounts if a["on_record_until"]),
        "with_furnisher_contact": sum(1 for a in accounts if a["furnisher_address"]),
        "expired": sum(1 for a in accounts if _falloff(a["on_record_until"]) == "expired"),
    }
