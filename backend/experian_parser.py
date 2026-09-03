"""
Experian annual-disclosure parser (PDF export from usa.experian.com/acr).

Written against the real 91-page file, not against a guess. The keyword scanner
it replaces read the layout instead of the data: on this exact report it
returned twenty items whose "creditors" were `Individual`, `Signer`,
`Authorized User` and `Account Number` — those are Responsibility *values* and
field *labels* — every one with no date and no furnisher, while missing all six
charge-offs, all four collections and all thirty hard inquiries.

── The PDF's actual shape ──────────────────────────────────────────────────

Label and value alternate on their own lines. Every tradeline carries the same
eighteen labels, so a block is delimited by `Account Name` rather than by any
terminator:

    POTENTIALLY NEGATIVE          <- caps, and only on adverse items
    Account Info
    Account Name        AFFIRM INC
    Account Number      CVOKXXXX          <- masked, but present
    Account Type        Unsecured
    Responsibility      Individual
    Interest Type       Fixed
    Date Opened         09/16/2025
    Status              Account charged off. $39 written off. $39 past due as of Aug 2026.
    Status Updated      May 2026
    Balance             $39
    Balance Updated     08/03/2026
    On Record Until     Oct 2032          <- the bureau's own fall-off date
    Original Creditor   T-MOBILE          <- collections only

Page furniture interrupts blocks mid-field and must be discarded:
`9/1/26, 11:35 AM`, `Annual Credit Report - Experian`, the printReport URL,
and a `6/91` page number.

Note the web view and the PDF differ. The web page shows `Potentially Negative`
in title case and a `Do you see information you believe to be inaccurate?`
link; neither string exists in the PDF. Parse the PDF.

── What this file does and does not disclose ───────────────────────────────

**Account numbers: present but masked** (`CVOKXXXX`). Experian reveals the full
number only behind a details view. Masked is what the consumer actually holds,
and it is sufficient to identify a tradeline in a dispute — so the letter uses
it verbatim and never invents the rest.

**Date of first delinquency: absent.** There is no DOFD label anywhere in the
document. The DOFD is the date that decides whether an adverse item may
lawfully remain under § 1681c(a)(4), and the bureau's disclosure to the
consumer omits it.

**On Record Until: present.** This is the bureau's own statement of when the
item drops off, and it is derived from the DOFD it will not show. That makes it
the lever this parser is built around:

  * it implies a DOFD (roughly seven years earlier), which can be compared
    against Date Opened and the status text for internal contradiction; and
  * if it has already passed, the item is being reported beyond the window the
    bureau itself published.

This parser never asserts an item is obsolete on its own arithmetic. It reports
what the file says, and where the file contradicts itself.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from money import money_str

_LABELS = (
    "Account Name", "Account Number", "Account Type", "Responsibility",
    "Interest Type", "Date Opened", "Status", "Status Updated", "Balance",
    "Balance Updated", "Recent Payment", "Monthly Payment", "Highest Balance",
    "Credit Limit", "Original Balance", "Terms", "On Record Until",
    "Original Creditor", "Payment History", "Contact Info", "Address",
    "Phone Number", "Comment", "Account Info",
)

_NEGATIVE_FLAG = "POTENTIALLY NEGATIVE"

# Header/footer injected by the print view, mid-block.
_FURNITURE = re.compile(
    r"^(?:\d{1,2}/\d{1,2}/\d{2},\s+\d{1,2}:\d{2}\s+[AP]M"
    r"|Annual Credit Report - Experian"
    r"|https?://\S+"
    r"|\d{1,3}/\d{1,3}"
    r"|Payment history guide"
    r")$"
)

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Status sentence -> dispute category. First match wins; specific before broad.
_STATUS_RULES = (
    ("collection account", "collection"),
    ("charged off", "charge_off"),
    ("charge off", "charge_off"),
    ("repossess", "repossession"),
    ("foreclos", "foreclosure"),
    ("bankrupt", "bankruptcy"),
    ("paid in settlement", "status_inaccuracy"),
    ("settled", "status_inaccuracy"),
    ("past due", "late_payment"),
)

# Statuses that are not a dispute. Padding a letter with accounts the consumer
# has no quarrel with is how a file gets read as a mail-merge.
_BENIGN = ("never late", "current / terms met", "paid, closed.", "open/never late")

# ── Payment-history grid ────────────────────────────────────────────────────
# Cells that record a delinquency. Classifying on the status sentence alone
# misses accounts the bureau describes as healthy while its own grid says
# otherwise: one JPMCB card in a real file reads "Pays As Agreed" on Equifax
# and "Paid, Closed." on Experian, while every bureau's grid carries
# 30/30/30/60 across 2020 and 90/120 in 2021. The grid is the bureau's own
# data contradicting the bureau's own prose, which is a stronger dispute than
# anything the consumer could assert — and a status-string classifier cannot
# see it at all.
_GRID_ADVERSE = {"30", "60", "90", "120", "150", "180", "CO", "COL"}

# The legend printed under every grid repeats those same tokens as labels
# ("30" / "Past due 30 days"). Parsing past this line counts the legend as
# data and marks every account delinquent.
_GRID_LEGEND = "Current / Terms met"

_GRID_SEVERITY = {"30": 1, "60": 2, "90": 3, "120": 4, "150": 5, "180": 6,
                  "CO": 7, "COL": 7}

_COLLECTOR_MARKERS = (
    "MIDLAND", "PORTFOLIO RECOV", "LVNV", "RESURGENT", "CBE GROUP",
    "TRANSWORLD", "CREDENCE", "ENHANCED RECOVERY", "IC SYSTEM", "CONVERGENT",
    "CAVALRY", "JEFFERSON CAPITAL", "RECEIVABLES", "ASSET ACCEPTANCE",
)


def looks_like_experian(text: str) -> bool:
    """Structural markers, not the word "Experian" — that appears everywhere."""
    return sum((
        "Account Info" in text,
        "On Record Until" in text,
        "Balance Updated" in text,
        "Inquired on" in text,
    )) >= 3


def _clean(lines: list[str]) -> list[str]:
    return [ln.strip() for ln in lines
            if ln.strip() and not _FURNITURE.match(ln.strip())]


def _us_date(raw: str) -> str:
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", (raw or "").strip())
    if not m:
        return ""
    mm, dd, yyyy = (int(g) for g in m.groups())
    try:
        return datetime(yyyy, mm, dd, tzinfo=timezone.utc).strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _month_year(raw: str) -> str:
    m = re.search(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{4})", raw or "")
    if not m:
        return ""
    mon = _MONTHS.get(m.group(1).lower())
    return f"{int(m.group(2)):04d}-{mon:02d}-01" if mon else ""


def _money(raw: str) -> str:
    """
    A balance as an exact decimal string, or "" when the report shows none.

    Returns the storage form rather than a float: these figures are quoted
    back to the bureau, and a binary float cannot hold what the report
    printed. `money.py` owns the representation.
    """
    return money_str(raw)


def _is_collector(name: str) -> bool:
    up = (name or "").upper()
    return any(m in up for m in _COLLECTOR_MARKERS)


def _grid_markers(block: list[str]) -> list[str]:
    """
    Delinquency cells in this account's payment-history grid.

    Bounded by the legend, which repeats the same tokens as labels — reading
    past it would mark every account in the file delinquent.
    """
    try:
        start = block.index("Payment History")
    except ValueError:
        return []
    end = len(block)
    for k in range(start + 1, len(block)):
        if block[k] == _GRID_LEGEND:
            end = k
            break
    return [c for c in block[start + 1:end] if c in _GRID_ADVERSE]


def _category_for(status: str, furnisher: str, grid: list[str] | None = None) -> str:
    """
    The dispute category, from the status sentence and the payment grid.

    The grid is consulted second but is never overridden by a benign status:
    a tradeline the bureau calls "Paid, Closed/Never late" while its own grid
    shows a 90-day delinquency is not a clean account, and the discrepancy is
    itself the dispute.
    """
    low = (status or "").lower()
    grid = grid or []

    benign_prose = any(b in low for b in _BENIGN) and "past due" not in low
    if benign_prose and not grid:
        return ""

    for needle, bucket in _STATUS_RULES:
        if needle in low:
            if bucket == "collection" and _is_collector(furnisher):
                return "debt_buyer"
            return bucket

    if not grid:
        return ""
    # Status prose said nothing useful, or said the account was fine. Classify
    # on the worst cell the bureau itself recorded.
    worst = max(grid, key=lambda c: _GRID_SEVERITY.get(c, 0))
    if worst in ("CO", "COL"):
        return "debt_buyer" if _is_collector(furnisher) else "charge_off"
    return "late_payment"


def _blocks(lines: list[str]) -> list[list[str]]:
    """Split into per-tradeline blocks, delimited by `Account Name`."""
    starts = [i for i, ln in enumerate(lines) if ln == "Account Name"]
    out = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        # Reach back a few lines to catch the POTENTIALLY NEGATIVE flag, which
        # sits above `Account Info`.
        head = max(0, start - 6)
        out.append(lines[head:end])
    return out


def _fields(block: list[str]) -> dict[str, str]:
    """Label/value pairs. A value is every line until the next known label."""
    out: dict[str, str] = {}
    i = 0
    while i < len(block):
        label = block[i]
        if label in _LABELS:
            parts = []
            j = i + 1
            while j < len(block) and block[j] not in _LABELS:
                parts.append(block[j])
                j += 1
            if parts and label not in out:
                out[label] = " ".join(parts).strip()
            i = j
            continue
        i += 1
    return out


def _implied_dofd(on_record_until: str) -> str:
    """
    Back out the DOFD the bureau used from the fall-off date it published.

    § 1681c(a)(4) runs seven years from the date of first delinquency, so a
    stated fall-off implies a DOFD roughly seven years earlier. This is an
    inference from the bureau's own number, and it is labelled as one wherever
    it reaches a letter — it is never presented as a disclosed fact.
    """
    if not on_record_until:
        return ""
    try:
        end = datetime.strptime(on_record_until, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return ""
    return (end - timedelta(days=int(365.25 * 7))).strftime("%Y-%m")


def _falloff_state(on_record_until: str) -> str:
    if not on_record_until:
        return "undisclosed"
    try:
        end = datetime.strptime(on_record_until, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return "undisclosed"
    now = datetime.now(timezone.utc)
    if end < now:
        return "past_stated_window"
    if (end - now).days <= 90:
        return "imminent"
    return "within_window"


def _mark_duplicates(accounts: list[dict]) -> None:
    """
    Flag tradelines the bureau lists more than once.

    Real example from this file: DEPT OF ED/AIDVANTAGE across repeated
    Date Opened values. Duplicate reporting inflates the apparent number of
    delinquent accounts and is a § 1681e(b) accuracy dispute in its own right.
    """
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for a in accounts:
        groups[(a["furnisher"], a["date_opened"], a["balance"])].append(a)
    for (name, opened, _bal), grp in groups.items():
        if len(grp) > 1 and opened:
            for a in grp:
                a["duplicate_count"] = len(grp)
                a["duplicate_note"] = (
                    f"{name} appears {len(grp)} times with the same date "
                    f"opened ({opened}) and the same balance."
                )


def _accounts(text: str) -> list[dict]:
    lines = _clean(text.splitlines())
    out = []
    for block in _blocks(lines):
        f = _fields(block)
        name = f.get("Account Name", "").strip()
        if not name or name in _LABELS:
            continue
        out.append({
            "furnisher": name,
            "account": f.get("Account Number", "").strip(),
            "account_type": f.get("Account Type", ""),
            "responsibility": f.get("Responsibility", ""),
            "date_opened": _us_date(f.get("Date Opened", "")),
            "status": f.get("Status", ""),
            "status_updated": _month_year(f.get("Status Updated", "")),
            "balance": _money(f.get("Balance", "")),
            "balance_updated": _us_date(f.get("Balance Updated", "")),
            "highest_balance": _money(f.get("Highest Balance", "")),
            "credit_limit": _money(f.get("Credit Limit", "")),
            "on_record_until": _month_year(f.get("On Record Until", "")),
            "original_creditor": f.get("Original Creditor", "").strip(),
            "negative": any(_NEGATIVE_FLAG in ln.upper() for ln in block),
            "grid": _grid_markers(block),
        })
    _mark_duplicates(out)
    return out


# A line that closes the PREVIOUS inquiry entry: the retention sentence, or an
# address tail like "CARROLLTON TX, 75006". Walking the furnisher name backwards
# stops here.
_INQUIRY_TAIL = re.compile(
    r"(until\s+[A-Za-z]{3}\w*\s+\d{4}\.?$"
    r"|^[A-Z][A-Za-z .'-]*\s+[A-Z]{2},\s*\d{5}$"
    r"|^\d{5}$"
    r"|^\(\d{3}\)\s*\d{3}-\d{4}$)"
)


def _is_caps(line: str) -> bool:
    """A furnisher line: upper case, short, and not a sentence."""
    s = (line or "").strip()
    if not s or len(s) > 44 or s.endswith("."):
        return False
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 2:
        return False
    return sum(c.isupper() for c in letters) / len(letters) >= 0.9


def _join_wrapped(parts: list[str]) -> str:
    """
    Rejoin a furnisher name split across PDF lines.

    The inquiry column is narrow enough to break mid-token, so the fragments
    have to be glued rather than space-joined:

        "NOWCOM/WES"   + "TLAKE FINANCIA"  -> NOWCOM/WESTLAKE FINANCIA
        "NORDSTROM/T"  + "D BANK USA"      -> NORDSTROM/TD BANK USA
        "COMENITYCAP"  + "ITAL/BIGO"       -> COMENITYCAPITAL/BIGO
        "A+ FEDERAL"   + "CREDIT UNION"    -> A+ FEDERAL CREDIT UNION  (space)

    A break mid-token leaves a stub on one side of the join, so glue when
    either the trailing token of the left fragment or the leading token of the
    right one is short. This is a heuristic on layout, not a dictionary, and it
    is only ever used for a display name.
    """
    def _tail(s: str) -> str:
        return re.split(r"[\s/]+", s.strip())[-1] if s.strip() else ""

    def _head(s: str) -> str:
        return re.split(r"[\s/]+", s.strip())[0] if s.strip() else ""

    out = ""
    for part in parts:
        if not out:
            out = part.strip()
            continue
        if out.endswith(("/", "-")) or len(_tail(out)) <= 4 or len(_head(part)) <= 4:
            out += part.strip()
        else:
            out = f"{out} {part.strip()}"
    return re.sub(r"\s+", " ", out).strip()


def _hard_inquiries(text: str) -> list[dict]:
    """
    Hard inquiries only — soft inquiries carry no permissible-purpose claim.

    `Inquired on` is a label with the date on the following line, and furnisher
    names wrap across lines ("A+ FEDERAL" / "CREDIT UNION"), so the name is
    gathered by walking backwards until the previous entry's address or
    retention sentence is reached.
    """
    lines = _clean(text.splitlines())

    # The summary header near the top ("30 Hard Inquiries") is not the section.
    # Bound the region by the Soft Inquiries heading instead.
    soft = next((i for i, ln in enumerate(lines)
                 if ln.strip() in ("Soft Inquiries", "Soft inquiries")), len(lines))
    hard = next((i for i, ln in enumerate(lines)
                 if i < soft and ln.strip() in ("Hard Inquiries", "Hard inquiries")), 0)

    out, seen = [], set()
    for i in range(hard, soft):
        if lines[i] != "Inquired on" or i + 1 >= len(lines):
            continue
        date = _us_date(lines[i + 1])
        if not date:
            continue

        # Furnisher lines are upper case; the surrounding prose ("Unsecured.
        # This inquiry is scheduled to continue on record until May 2028.")
        # and the address tail are not. Stop at the first line that is not.
        parts = []
        for b in range(i - 1, max(hard - 1, i - 5), -1):
            cand = lines[b]
            if cand in _LABELS or _INQUIRY_TAIL.search(cand) or not _is_caps(cand):
                break
            parts.insert(0, cand)
        name = _join_wrapped(parts)
        if not name or (name, date) in seen:
            continue
        seen.add((name, date))
        out.append({"furnisher": name, "date": date})
    return out


def parse_experian(text: str) -> list[dict]:
    """
    Experian PDF -> dispute items in the app's shape.

    Only adverse tradelines, duplicates and hard inquiries are returned.

    Every adverse item carries a `verification_demand` ground. That is the
    posture the rest of this engine should lead with: it asserts no fact the
    consumer has to prove, so it cannot be defeated the way a bare "this is not
    my account" now can be — see Ward v. National Credit Systems (10th Cir.
    2026), which reversed a consumer verdict because the identity claim rested
    on the consumer's own say-so against objective evidence. Asking who was
    contacted, at what address, and on what documentation puts the burden where
    § 1681i(a)(7) and § 1681g(a)(3) already put it.
    """
    items: list[dict] = []

    for a in _accounts(text):
        grid = a.get("grid") or []
        bucket = _category_for(a["status"], a["furnisher"], grid)
        is_dupe = a.get("duplicate_count", 0) > 1
        if not bucket and not is_dupe:
            continue

        grounds = []
        if bucket:
            grounds.append({"category": bucket, "strength": "moderate",
                            "evidence": a["status"]})

        # Where the bureau's own grid contradicts its own status sentence, say
        # so explicitly. This needs no assertion from the consumer — it is one
        # document disagreeing with itself.
        if grid and any(b in (a["status"] or "").lower() for b in _BENIGN):
            worst = max(grid, key=lambda c: _GRID_SEVERITY.get(c, 0))
            label = {"CO": "a charge-off", "COL": "a collection"}.get(
                worst, f"a {worst}-day delinquency")
            grounds.append({
                "category": "status_inaccuracy",
                "strength": "strong",
                "evidence": (
                    f"The status reported for this account is "
                    f"\"{a['status']}\", but the payment history you publish for "
                    f"the same account records {label}. Both statements cannot "
                    f"be accurate."
                ),
            })
        if is_dupe:
            grounds.append({"category": "duplicate", "strength": "strong",
                            "evidence": a["duplicate_note"]})

        falloff = _falloff_state(a["on_record_until"])
        if falloff == "past_stated_window":
            grounds.append({
                "category": "obsolete", "strength": "strong",
                "evidence": (
                    f"Experian states this item remains on record until "
                    f"{a['on_record_until']}, a date that has passed."
                ),
            })

        # The demand that needs no factual assertion from the consumer.
        #
        # A named Original Creditor means the furnisher is collecting someone
        # else's debt — a collector. Its absence means the furnisher is most
        # likely the original creditor itself, which is the `creditor_direct`
        # posture. This was inverted, which labelled a JPMCB card as a
        # collection and would have aimed collector-only law at a bank.
        grounds.append({
            "category": "collection" if a["original_creditor"] else "creditor_direct",
            "strength": "moderate",
            "evidence": (
                "I am requesting the description of the procedure used to "
                "verify this item, including the business name, address and "
                "telephone number of the furnisher contacted, and the address "
                "at which I am recorded as having been contacted."
            ),
        })

        items.append({
            "bucket": bucket or "duplicate",
            "type": "bureau",
            "target": "Experian",
            "furnisher": a["furnisher"],
            "account": a["account"],
            "amount": a["balance"],
            "opened": a["date_opened"],
            "highest_balance": a["highest_balance"],
            "original_creditor": a["original_creditor"],
            "account_type": a["account_type"],
            "responsibility": a["responsibility"],
            "status_text": a["status"],
            "on_record_until": a["on_record_until"],
            "implied_dofd": _implied_dofd(a["on_record_until"]),
            "falloff_status": falloff,
            "duplicate_note": a.get("duplicate_note", ""),
            "duplicate_count": a.get("duplicate_count", 0),
            "categories": grounds,
            "category_count": len(grounds),
            "reason": a["status"] or "This item is inaccurate as reported.",
            "confidence": "high",
            "dofd_disclosed": False,
        })

    for inq in _hard_inquiries(text):
        items.append({
            "bucket": "inquiry",
            "type": "bureau",
            "target": "Experian",
            "furnisher": inq["furnisher"],
            "account": "",
            "amount": None,
            "opened": inq["date"],
            "categories": [{
                "category": "inquiry", "strength": "moderate",
                "evidence": f"Hard inquiry by {inq['furnisher']} on {inq['date']}.",
            }],
            "category_count": 1,
            "falloff_status": "",
            "reason": (
                f"I am requesting the permissible purpose under 15 U.S.C. "
                f"§ 1681b for the inquiry by {inq['furnisher']} on {inq['date']}."
            ),
            "confidence": "medium",
        })

    return items


def report_summary(text: str) -> dict:
    """Counts for the review screen and for our own diagnostics."""
    accounts = _accounts(text)
    return {
        "tradelines_total": len(accounts),
        "tradelines_negative": sum(1 for a in accounts if a["negative"]),
        "duplicates": sum(1 for a in accounts if a.get("duplicate_count", 0) > 1),
        "hard_inquiries": len(_hard_inquiries(text)),
        "past_stated_window": sum(
            1 for a in accounts if _falloff_state(a["on_record_until"]) == "past_stated_window"),
        "account_numbers_masked": sum(1 for a in accounts if "X" in (a["account"] or "")),
        "discloses_dofd": "first delinquen" in text.lower(),
    }
