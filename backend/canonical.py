"""
Canonical report shape — one contract between every parser and the letter engine.

Four parsers feed the letter engine and each hands it a different shape. The
Experian parser emits `furnisher` and `on_record_until`; the Equifax parser
emits `account_name` and `falloff_status`; the keyword scanner emits eight thin
fields and calls the furnisher `target`; Claude emits whatever the prompt
happened to ask for. Downstream, the engine hunts for whichever key exists.

That hunting is the direct cause of defects already found in mailed output:
`Account Name: Equifax` (the bureau printed as the account holder, because
`furnisher` was absent and `target` was used), `Reported Balance: 4111.00`
(three different money representations reaching one document), and a
`date_reported` that is permanently empty because the adapter reads `reported`
while the producer writes `date_reported`.

So every parser now normalises through here. After this layer:

  * every item has every field, always, in the same order;
  * a field that is unknown is an empty string or None — never absent, never a
    placeholder like "Unknown" that can be printed by accident;
  * items are ordered deterministically, so the same report always produces the
    same letter and two different reports produce comparable ones;
  * money is `Decimal`, not `float`.

The consumer whose file has nineteen collections and the consumer whose file
has one get the same structure. Only the contents differ.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation

from money import money_str

# Ranking used to order items within a letter. Highest first: a closed
# statutory window is arithmetic, a "please verify this" is an opinion. Keeping
# the order deterministic means a letter is reproducible from its inputs, and
# that two consumers' letters are comparable side by side.
SEVERITY = {
    "obsolete": 100,
    "identity_theft": 95,
    "identity_error": 95,
    "deceased_indicator": 92,
    "re_aging": 90,
    "mixed_file": 88,
    "duplicate": 85,
    "bankruptcy": 82,
    "judgment_lien": 80,
    "debt_buyer": 78,
    "foreclosure": 74,
    "repossession": 72,
    "collection": 70,
    "medical_debt": 68,
    "child_support": 66,
    "rental_eviction": 64,
    "student_loan": 60,
    "charge_off": 55,
    "inquiry": 50,
    "status_inaccuracy": 45,
    "balance_inaccuracy": 40,
    "late_payment": 35,
    "personal_info": 30,
    "creditor_direct": 25,
}

# Values a parser may emit to mean "I could not read this". They must never
# reach a letter: "Dear Unknown," and "Account Number: Unknown" both shipped.
_NULLISH = {"unknown", "n/a", "na", "none", "null", "-", "--", "?", ""}


def _clean(value) -> str:
    """A display string, or empty. Never a placeholder word."""
    if value is None:
        return ""
    s = str(value).strip()
    return "" if s.lower() in _NULLISH else s


def _money(value) -> Decimal | None:
    """
    Money as Decimal.

    Balances drive the amounts printed in a legal demand. Floats do not
    represent decimal money exactly, and the codebase was carrying balances as
    float, str and None interchangeably.
    """
    if value is None or value == "":
        return None
    s = re.sub(r"[^\d.\-]", "", str(value))
    if not s or s in ("-", ".", "-."):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _date(value) -> str:
    """ISO date, or empty. Accepts YYYY-MM-DD, MM/DD/YYYY and 'Mon YYYY'."""
    s = _clean(value)
    if not s:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        mm, dd, yyyy = (int(g) for g in m.groups())
        return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if m:
        return f"{s}-01"
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    m = re.fullmatch(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{4})", s)
    if m and m.group(1).lower() in months:
        return f"{int(m.group(2)):04d}-{months[m.group(1).lower()]:02d}-01"
    return ""


@dataclass
class CanonicalItem:
    """
    One disputed item, in the shape the letter engine may rely on.

    Every field is always present. The engine never needs to ask whether a key
    exists, only whether it is empty — which is the difference between a letter
    that omits a line and a letter that prints the word "Unknown".
    """

    # Identity
    item_id: str = ""
    bureau: str = ""
    furnisher: str = ""
    original_creditor: str = ""
    account_masked: str = ""
    account_type: str = ""
    responsibility: str = ""

    # Dates — ISO or empty, never a bare year, never a US format
    opened: str = ""
    reported: str = ""
    dofd: str = ""
    dofd_source: str = ""          # "disclosed" | "implied" | ""
    falloff_date: str = ""
    falloff_state: str = ""        # within_window | imminent | past_stated_window | undisclosed

    # Money — Decimal or None, never float, never str
    balance: Decimal | None = None
    high_balance: Decimal | None = None
    credit_limit: Decimal | None = None
    written_off: Decimal | None = None

    # Classification
    category: str = ""
    status_text: str = ""
    grounds: list = field(default_factory=list)
    duplicate_of: str = ""
    duplicate_count: int = 0

    # Provenance — which parser produced this, and how sure it is
    source: str = ""
    confidence: str = "medium"

    @property
    def severity(self) -> int:
        return SEVERITY.get(self.category, 0)

    def to_engine(self) -> dict:
        """
        The dict shape the existing dispute engine consumes.

        Kept as an explicit translation rather than passing the dataclass
        through, so the engine's expectations are written down in one place
        instead of being discovered by a KeyError in production.
        """
        return {
            "id": self.item_id,
            "type": "bureau",
            "target": self.bureau or "Experian",
            "furnisher": self.furnisher,
            "original_creditor": self.original_creditor,
            "account": self.account_masked,
            "account_type": self.account_type,
            "bucket": self.category,
            # Decimal out as an exact decimal string. Casting to float here
            # undid the whole reason these are held as Decimal — see money.py.
            "amount": money_str(self.balance),
            "highest_balance": money_str(self.high_balance),
            "opened": self.opened,
            "dofd": self.dofd,
            "date_reported": self.reported,
            "falloff_status": self.falloff_state,
            "reason": self.status_text,
            "categories": [dict(g) for g in self.grounds],
            "category_count": len(self.grounds),
            "confidence": self.confidence,
        }


def _item_id(bureau: str, furnisher: str, account: str, opened: str, n: int) -> str:
    """
    Stable id for one tradeline.

    Derived from the tradeline's own identifying fields so the same account
    gets the same id on every run and across rounds — which is what lets a
    follow-up letter refer to the same item, and what lets the outcome ledger
    count one dispute once. The index is a tiebreaker for genuine duplicates,
    which is the one case where two items legitimately share every field.
    """
    seed = "|".join((bureau, furnisher, account, opened, str(n)))
    return "ITEM" + hashlib.sha256(seed.encode()).hexdigest()[:8].upper()


def canonicalise(items: list[dict], bureau: str = "", source: str = "") -> list[CanonicalItem]:
    """
    Any parser's output -> the canonical shape, deterministically ordered.

    Field aliases are resolved here, once, instead of at each read site. That
    is the fix for `date_reported` vs `reported` and `furnisher` vs `target`:
    a producer may use either name, and the engine never sees the difference.
    """
    def pick(src: dict, *names, default=""):
        """First non-empty value among aliases for the same field."""
        for name in names:
            if src.get(name) not in (None, ""):
                return src[name]
        return default

    out: list[CanonicalItem] = []
    for n, raw in enumerate(items or []):

        # `target` is the recipient bureau in some parsers and the furnisher in
        # others. Only trust it as a furnisher when it is not a bureau name.
        target = _clean(raw.get("target"))
        is_bureau_name = target.lower() in ("experian", "equifax", "transunion")
        furnisher = _clean(pick(raw, "furnisher", "account_name", "creditor")) or (
            "" if is_bureau_name else target)

        opened = _date(pick(raw, "opened", "date_opened"))
        account = _clean(pick(raw, "account", "account_number", "account_masked"))
        item_bureau = bureau or (target if is_bureau_name else "") or "Experian"

        falloff = _date(pick(raw, "falloff_date", "on_record_until"))
        dofd = _date(pick(raw, "dofd", "date_of_first_delinquency"))
        implied = _clean(raw.get("implied_dofd"))
        if not dofd and implied:
            dofd, dofd_source = _date(implied + "-01" if len(implied) == 7 else implied), "implied"
        else:
            dofd_source = "disclosed" if dofd else ""

        out.append(CanonicalItem(
            item_id=raw.get("id") or _item_id(item_bureau, furnisher, account, opened, n),
            bureau=item_bureau,
            furnisher=furnisher,
            original_creditor=_clean(pick(raw, "original_creditor")),
            account_masked=account,
            account_type=_clean(pick(raw, "account_type")),
            responsibility=_clean(pick(raw, "responsibility")),
            opened=opened,
            reported=_date(pick(raw, "reported", "date_reported")),
            dofd=dofd,
            dofd_source=dofd_source,
            falloff_date=falloff,
            falloff_state=_clean(pick(raw, "falloff_state", "falloff_status")),
            balance=_money(pick(raw, "balance", "amount", "current_balance")),
            high_balance=_money(pick(raw, "high_balance", "highest_balance")),
            credit_limit=_money(pick(raw, "credit_limit")),
            written_off=_money(pick(raw, "written_off")),
            category=_clean(pick(raw, "category", "bucket")),
            status_text=_clean(pick(raw, "status_text", "status", "reason")),
            grounds=[dict(g) for g in (raw.get("categories") or [])],
            duplicate_of=_clean(raw.get("duplicate_note")),
            duplicate_count=int(raw.get("duplicate_count") or 0),
            source=source or _clean(raw.get("source")),
            confidence=_clean(raw.get("confidence")) or "medium",
        ))

    # Deterministic order: strongest ground first, then oldest, then furnisher.
    # Reproducible from the inputs alone — no clock, no dict ordering.
    out.sort(key=lambda i: (-i.severity, i.opened or "9999", i.furnisher, i.item_id))
    return out


def normalise_report(items: list[dict], bureau: str = "", source: str = "",
                     meta: dict | None = None) -> dict:
    """
    The whole report in one fixed envelope.

    Same keys for every consumer. A file with nineteen collections and a file
    with one produce identically-shaped output; only the contents differ.
    """
    canon = canonicalise(items, bureau=bureau, source=source)
    by_category: dict[str, int] = {}
    for item in canon:
        by_category[item.category] = by_category.get(item.category, 0) + 1

    return {
        "bureau": bureau or (canon[0].bureau if canon else ""),
        "source": source,
        "counts": {
            "items": len(canon),
            "with_account_number": sum(1 for i in canon if i.account_masked),
            "with_opened_date": sum(1 for i in canon if i.opened),
            "with_dofd": sum(1 for i in canon if i.dofd),
            "duplicates": sum(1 for i in canon if i.duplicate_count > 1),
            "by_category": dict(sorted(by_category.items())),
        },
        "items": canon,
        "meta": dict(meta or {}),
    }


def as_dicts(report: dict) -> list[dict]:
    """Canonical items in the shape the existing engine consumes."""
    return [i.to_engine() for i in report["items"]]


def field_coverage(report: dict) -> dict:
    """
    How much of the canonical shape this report actually filled.

    Worth surfacing: a letter built from items with no dates and no account
    numbers is a weak letter, and that is a property of the upload, not of the
    engine. This is how we tell the difference.
    """
    items = report["items"]
    if not items:
        return {}
    total = len(items)
    tracked = ("furnisher", "account_masked", "opened", "dofd", "falloff_date",
               "original_creditor", "status_text")
    return {
        name: f"{sum(1 for i in items if getattr(i, name))}/{total}"
        for name in tracked
    } | {"balance": f"{sum(1 for i in items if i.balance is not None)}/{total}"}


def to_json_safe(report: dict) -> dict:
    """Envelope with Decimals as strings, for storage or an API response."""
    out = dict(report)
    out["items"] = [
        {k: (str(v) if isinstance(v, Decimal) else v)
         for k, v in asdict(i).items()}
        for i in report["items"]
    ]
    return out
