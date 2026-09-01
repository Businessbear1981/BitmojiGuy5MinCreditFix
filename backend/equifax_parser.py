"""
Equifax report parser — structured, deterministic, no API key required.

The old path was: try Claude, fall back to a keyword scanner. On a real
Equifax file both fail. Claude is skipped when ANTHROPIC_API_KEY is unset,
and the keyword scanner hunts for loose phrases like "charge off" in running
prose — but Equifax doesn't write prose. It writes labelled pairs:

    MIDLAND CREDIT MANAGEMENT - Closed
    320 E BIG BEAVER RD, TROY, MI | (877) 822-0381
    Date Reported:  08/27/2026 | Balance:  $527
    Account Number:  *7839 | Owner:  Individual Account
    Credit Limit:   | High Credit:  $527
    Loan/Account Type:  Debt Buyer Account | Status:
    Date Opened:  03/26/2024
    Date of 1st Delinquency:  09/13/2023

Every signal we care about is already labelled. The report *tells* us an
account is a Debt Buyer Account; it *tells* us the date of first
delinquency, which is the field the obsolescence and re-aging theories turn
on. Reading labels is more accurate than any model guessing from prose, and
it costs nothing per report.

Claude stays available for formats this parser doesn't recognise — but for
Equifax, which is what we ask consumers to pull, this is the primary path.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

# ── Account-block boundaries ────────────────────────────────────────────────
# Equifax opens each tradeline with an indented "NAME - Open|Closed" line.
_ACCOUNT_SPLIT = re.compile(
    r"\n\s{4,}([A-Z0-9][A-Z0-9 &.,'\-/#]{3,60}?)\s+-\s+(Open|Closed)\n"
)

# Labels are "Label:  value" and may share a line, separated by "|".
def _field(block: str, label: str) -> str:
    m = re.search(rf"{re.escape(label)}:\s*([^\n|]*?)(?:\s*\||\n)", block)
    if not m:
        return ""
    val = m.group(1).strip()
    # Guard against a blank field swallowing the next label off the same line.
    if val.endswith(":") or re.match(r"^[A-Z][A-Za-z /]+:$", val):
        return ""
    return val


_MONEY = re.compile(r"-?[\d,]+(?:\.\d{2})?")


def _money(raw: str) -> Optional[float]:
    if not raw:
        return None
    m = _MONEY.search(raw.replace("$", ""))
    if not m:
        return None
    try:
        return float(m.group().replace(",", ""))
    except ValueError:
        return None


def _date(raw: str) -> str:
    """Normalise MM/DD/YYYY to ISO. Returns '' when absent or unparseable."""
    if not raw:
        return ""
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    if not m:
        return ""
    mm, dd, yyyy = m.groups()
    try:
        return datetime(int(yyyy), int(mm), int(dd)).strftime("%Y-%m-%d")
    except ValueError:
        return ""


# ── Account type → our dispute taxonomy ─────────────────────────────────────
# Equifax states the type outright. No inference needed.
_TYPE_MAP = {
    "debt buyer account": "debt_buyer",
    "collection": "collection",
    "factoring company account": "collection",
    "education loan": "student_loan",
    "credit card": "late_payment",
    "flexible spending credit card": "late_payment",
    "secured credit card": "late_payment",
    "charge account": "late_payment",
    "auto": "repossession",
    "mortgage": "foreclosure",
    "real estate": "foreclosure",
}


def _categories(atype: str, status: str, past_due, dofd: str, opened: str,
                narrative: str, grid: dict, limit, high, balance,
                falloff_status: str) -> list[dict]:
    """
    Every dispute category this one tradeline supports — not just the best one.

    A single account usually gives you more than one angle, and the angles are
    independent: if any one of them holds, the item comes off. Sending three
    arguments about the same account is not padding, it is how you stop a
    bureau resolving the easy one and calling the matter closed.

    Each entry carries a `strength` and the `evidence` it rests on, so a
    reviewer can see at a glance which argument is the real one and which is
    a long shot worth including anyway.

    strength:
      strong    the report contradicts itself, or a hard deadline has passed
      moderate  a real discrepancy that the furnisher has to explain
      weak      arguable, included because it costs nothing to raise
    """
    cats: list[dict] = []
    t = (atype or "").lower()
    blob = f"{status} {narrative}".lower()

    def add(cat, strength, evidence):
        cats.append({"category": cat, "strength": strength, "evidence": evidence})

    # ── What the report calls it ────────────────────────────────────────────
    if "debt buyer" in t:
        add("debt_buyer", "moderate",
            f"Equifax classifies this as '{atype}' — a purchased debt, not an "
            f"account opened with this entity")
    elif "collection" in t or "factoring" in t:
        add("collection", "moderate", f"reported as '{atype}'")
    elif "education loan" in t:
        add("student_loan", "moderate", f"reported as '{atype}'")

    if "charge" in blob and "off" in blob or grid.get("CO"):
        n = grid.get("CO", 0)
        add("charge_off", "moderate",
            f"charge-off status reported" + (f" across {n} months" if n else ""))
    if "repossess" in blob or grid.get("R"):
        add("repossession", "moderate", "repossession reported")
    if "foreclos" in blob or grid.get("F"):
        add("foreclosure", "moderate", "foreclosure reported")
    if "bankrupt" in blob or grid.get("B"):
        add("bankruptcy", "moderate", "bankruptcy notation reported")

    # ── The clock ───────────────────────────────────────────────────────────
    if falloff_status == "expired":
        add("obsolete", "strong",
            "the seven-year reporting window measured from the stated date of "
            "first delinquency has already closed")
    elif falloff_status == "imminent":
        add("obsolete", "moderate",
            "the reporting window closes within 90 days; the stated dates should "
            "be confirmed before the item ages off")

    # ── Dates that contradict each other ────────────────────────────────────
    if dofd and opened and dofd < opened:
        add("re_aging", "strong",
            f"the account is reported as opened {opened} but carries a delinquency "
            f"date of {dofd}, which precedes it — the obligation predates this "
            f"tradeline and the dates must be consistent across the transfer")

    # ── Fields that cannot both be right ────────────────────────────────────
    if high and not limit:
        add("balance_inaccuracy", "weak",
            "a high balance is reported with no credit limit, leaving utilisation "
            "uncomputable from the file as furnished")

    if balance and past_due and abs(float(balance) - float(past_due)) < 0.01 and balance > 0:
        add("balance_inaccuracy", "weak",
            f"balance and amount past due are both reported as {balance:.2f}, with no "
            f"payment history explaining the equivalence")

    late = sum(grid.get(k, 0) for k in ("30", "60", "90", "120", "150", "180"))
    if late and not dofd:
        add("re_aging", "moderate",
            f"{late} months of delinquency are reported with no date of first "
            f"delinquency stated")

    if late and dofd:
        add("late_payment", "weak",
            f"{late} months of late payment reported; each marker should be "
            f"verifiable against the furnisher's own ledger")

    # Nothing negative found at all — not a dispute candidate.
    if not cats:
        return []

    order = {"strong": 0, "moderate": 1, "weak": 2}
    cats.sort(key=lambda c: order[c["strength"]])

    # One entry per category. Two weak balance findings are one balance
    # argument with two supporting facts, not two arguments.
    merged: dict[str, dict] = {}
    for c in cats:
        if c["category"] in merged:
            merged[c["category"]]["evidence"] += f"; also, {c['evidence']}"
        else:
            merged[c["category"]] = dict(c)
    return list(merged.values())


# ── Reporting windows, FCRA § 605(a) ───────────────────────────────────────
# Most adverse items run seven years from the date of first delinquency.
# Chapter 7 bankruptcy runs ten years from filing. Nothing here is a
# judgement call — it is arithmetic on a date the report already states.
_FALLOFF_YEARS = {
    "bankruptcy": 10,
    "debt_buyer": 7,
    "collection": 7,
    "charge_off": 7,
    "late_payment": 7,
    "repossession": 7,
    "foreclosure": 7,
    "student_loan": 7,
    "judgment_lien": 7,
    "medical_debt": 7,
    "inquiry": 2,
}


def _falloff(dofd: str, category: str) -> dict:
    """
    When this item drops off the file on its own.

    Worth surfacing before anyone spends a dispute on it: an item three weeks
    from ageing off will be gone before the bureau's thirty days are up, and
    disputing it burns the consumer's attention on something the calendar
    was going to fix regardless.
    """
    if not dofd:
        return {"date": "", "days": None, "status": "unknown"}

    years = _FALLOFF_YEARS.get(category, 7)
    try:
        start = datetime.strptime(dofd, "%Y-%m-%d")
    except ValueError:
        return {"date": "", "days": None, "status": "unknown"}

    # Calendar years, not 365-day approximations — the window is stated in years.
    try:
        off = start.replace(year=start.year + years)
    except ValueError:  # 29 Feb
        off = start.replace(year=start.year + years, day=28)

    days = (off - datetime.now()).days
    if days <= 0:
        status = "expired"          # already past the window — should be gone
    elif days <= 90:
        status = "imminent"         # will age off before a dispute concludes
    elif days <= 365:
        status = "within_a_year"
    else:
        status = "distant"

    return {"date": off.strftime("%Y-%m-%d"), "days": days, "status": status}


def _payment_grid(block: str) -> dict:
    """
    Count the monthly status letters Equifax prints in the payment history.

    C=collection, CO=charge-off, 30/60/90/120/150/180=days late,
    R=repossession, F=foreclosure, B=bankruptcy, V=voluntary surrender.
    """
    m = re.search(r"Payment History(.*?)(?:24 Month History|Narrative|\Z)", block, re.S)
    if not m:
        return {}
    seg = m.group(1)
    # Strip the legend block, which lists every code and would inflate counts.
    seg = seg.split("Paid on Time")[0]
    tokens = re.findall(r"\b(CO|C|30|60|90|120|150|180|R|F|B|V|TN)\b", seg)
    out: dict[str, int] = {}
    for tok in tokens:
        out[tok] = out.get(tok, 0) + 1
    return out


def parse_equifax(text: str) -> dict:
    """
    Parse a full Equifax consumer disclosure.

    Returns the `parsed_data` shape the dispute engine expects, plus a
    `report_meta` block carrying file-level signals (address count, inquiry
    counts, history length) that individual tradelines don't show.
    """
    accounts: list[dict] = []
    parts = _ACCOUNT_SPLIT.split(text)

    for i in range(1, len(parts), 3):
        name, open_closed, block = parts[i].strip(), parts[i + 1], parts[i + 2]

        atype = _field(block, "Loan/Account Type")
        status = _field(block, "Status")
        narrative = _field(block, "Narrative Code(s)")
        past_due = _money(_field(block, "Amount Past Due"))
        dofd = _date(_field(block, "Date of 1st Delinquency"))
        opened = _date(_field(block, "Date Opened"))
        limit = _money(_field(block, "Credit Limit"))
        high = _money(_field(block, "High Credit"))
        balance = _money(_field(block, "Balance"))

        grid = _payment_grid(block)
        # Falloff needs a category, and category needs falloff. Compute a
        # provisional window from the account type, then refine.
        provisional = ("bankruptcy" if "bankrupt" in f"{status}{narrative}".lower()
                       else "charge_off")
        falloff = _falloff(dofd, provisional)

        cats = _categories(atype, status, past_due, dofd, opened, narrative,
                           grid, limit, high, balance, falloff["status"])
        if not cats:
            continue  # clean, current account — nothing to dispute

        category = cats[0]["category"]   # primary = strongest argument

        accounts.append({
            "item_id": f"EFX{len(accounts) + 1:03d}",
            "account_name": name,
            "account_number": _field(block, "Account Number"),
            "account_type": atype,
            "original_creditor": "",
            "current_balance": f"{balance:.2f}" if balance is not None else "",
            "highest_balance": f"{high:.2f}" if high is not None else "",
            "credit_limit": f"{limit:.2f}" if limit is not None else "",
            "status": f"{status} {open_closed}".strip(),
            "date_opened": opened,
            "date_of_first_delinquency": dofd,
            "date_reported": _date(_field(block, "Date Reported")),
            "months_reviewed": _field(block, "Months Reviewed"),
            "narrative_codes": [c.strip() for c in narrative.split(",") if c.strip()],
            "payment_grid": grid,
            "amount_past_due": past_due,
            # Primary category = the strongest argument available.
            "bucket": category,
            # Every angle this account supports. One item, several independent
            # grounds — if any holds, the item comes off.
            "categories": cats,
            "category_count": len(cats),
            "strongest": cats[0]["strength"],
            "type": "bureau",
            # Who the letter goes to.
            "target": "Equifax",
            # Who is actually reporting the item. The letter names this, not
            # the bureau — "Equifax (Acct: *7839)" reads as nonsense to a
            # clerk who knows Equifax did not lend anyone $527.
            "furnisher": name,
            "account": _field(block, "Account Number"),
            "amount": balance,
            "opened": opened,
            "dofd": dofd,
            # When the FCRA window closes on this item, and how to read it.
            "falloff_date": falloff["date"],
            "falloff_days": falloff["days"],
            "falloff_status": falloff["status"],
            "reason": "",  # filled by the analyst from the matched theory
        })

    return {
        "file_metadata": {"bureau": "Equifax", "parser": "equifax_structured"},
        "consumer_profile": _profile(text),
        "accounts": accounts,
        "report_meta": _report_meta(text, accounts),
        "data_quality_flags": _quality_flags(text, accounts),
    }


def _profile(text: str) -> dict:
    name = ""
    m = re.search(r"Prepared for:\s*\n([A-Z][A-Z .'\-]+)\n", text)
    if m:
        name = m.group(1).strip()

    addresses = re.findall(
        r"\n(\d+[^\n,]{2,40},\s*[A-Z][A-Za-z ]+,\s*[A-Z]{2}\s*\n?\s*\d{5})", text)
    cleaned = [re.sub(r"\s+", " ", a).strip() for a in addresses]

    return {
        "primary_name": name,
        "current_address": cleaned[0] if cleaned else "",
        "all_addresses": list(dict.fromkeys(cleaned)),
        "data_quality_flags": [],
    }


def _report_meta(text: str, accounts: list[dict]) -> dict:
    hard = re.findall(
        r"\n([A-Z][A-Z0-9 &.,'\-/#]{3,50})\n[^\n]*\nPhone:[^\n]*\nHard\n([0-9/,\s]+)", text)
    soft = re.findall(
        r"\n([A-Z][A-Z0-9 &.,'\-/#]{3,50})\n[^\n]*\nPhone:[^\n]*\nSoft\n([0-9/,\s]+)", text)

    def _hist(label):
        m = re.search(rf"{label}\s*\n([^\n]+)", text)
        return m.group(1).strip() if m else ""

    return {
        "hard_inquiries": [{"company": h[0].strip(), "dates": h[1].split(",")} for h in hard],
        "soft_inquiries": [{"company": s[0].strip(), "dates": s[1].split(",")} for s in soft],
        "hard_inquiry_count": len(hard),
        "soft_inquiry_count": len(soft),
        "length_of_history": _hist("Length of Credit History"),
        "average_account_age": _hist("Average Account Age"),
        "oldest_account": _hist("Oldest Account"),
        "disputable_accounts": len(accounts),
    }


def _quality_flags(text: str, accounts: list[dict]) -> list[str]:
    """
    File-level signals the analyst can use. These are observations about the
    report itself, not accusations — the analyst decides what they mean.
    """
    flags = []
    profile = _profile(text)

    addr_count = len(profile["all_addresses"])
    if addr_count >= 4:
        flags.append(
            f"address_variance: {addr_count} addresses on file — relevant to "
            f"mixed-file and address-accuracy review")

    # Same creditor, multiple tradelines: servicer splits and duplicates.
    from collections import Counter
    names = Counter(a["account_name"] for a in accounts)
    for name, n in names.items():
        if n >= 2:
            flags.append(f"repeat_furnisher: {name} reports {n} separate tradelines")

    # Missing credit limit makes utilisation uncomputable for that card.
    no_limit = [a for a in accounts if not a["credit_limit"] and a["highest_balance"]]
    if no_limit:
        flags.append(
            f"missing_credit_limit: {len(no_limit)} account(s) report a high balance "
            f"with no credit limit")

    # An account opened *after* its own first delinquency is a chain-of-custody
    # signal: the debt predates the tradeline, i.e. it was transferred.
    for a in accounts:
        if a["date_opened"] and a["date_of_first_delinquency"]:
            if a["date_of_first_delinquency"] < a["date_opened"]:
                flags.append(
                    f"transferred_debt: {a['account_name']} opened {a['date_opened']} "
                    f"but reports delinquency from {a['date_of_first_delinquency']}")

    expired = [a for a in accounts if a.get("falloff_status") == "expired"]
    if expired:
        flags.append(
            f"past_reporting_window: {len(expired)} item(s) appear to be beyond the "
            f"seven-year window and should no longer be reported")

    imminent = [a for a in accounts if a.get("falloff_status") == "imminent"]
    if imminent:
        names = ", ".join(f"{a['account_name']} ({a['falloff_days']}d)" for a in imminent[:3])
        flags.append(
            f"ageing_off_soon: {len(imminent)} item(s) fall off within 90 days — {names}")

    return flags


def has_category(item: dict, category: str) -> bool:
    """
    Does this item support the given dispute category?

    Check this rather than `item["bucket"]`. `bucket` holds the *strongest*
    argument, so a debt-buyer account whose dates contradict each other comes
    through as "re_aging" — filtering on bucket would miss it entirely.
    """
    if item.get("bucket") == category:
        return True
    return any(c["category"] == category for c in item.get("categories") or [])


def looks_like_equifax(text: str) -> bool:
    """Cheap sniff so the caller can route without trying every parser."""
    markers = ("Loan/Account Type:", "Date of 1st Delinquency:", "888-EQUIFAX")
    return sum(1 for m in markers if m in text) >= 2
