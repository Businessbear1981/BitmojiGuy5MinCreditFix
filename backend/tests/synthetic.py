"""
Synthetic consumers and credit reports, for testing coverage rather than load.

Running one real file through the pipeline a hundred times proves the pipeline
is deterministic. It proves nothing about a Michigan consumer, a file whose
only negative item is already obsolete, or a report with nothing wrong in it at
all. This module makes those cases.

Two rules it holds to:

  * **Everything here is unmistakably fake.** Surnames come from a list of
    invented words, and every generated report carries `is_demo` in its header
    text. Nothing in this file may ever be presented as a real consumer, a real
    furnisher, or a real balance.

  * **Seeded and reproducible.** A profile is a pure function of its index, so
    a failure names the seed that reproduces it exactly. No wall-clock, no
    unseeded randomness.

The report text is generated in the Equifax export shape, because that is the
format the product tells customers to bring and the one its strongest parser
reads. `assert_parseable()` checks the sniff markers so a format drift fails
here rather than as a mysteriously empty parse downstream.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta

# ── Beta regions, mirrored from fishbowl.BETA_REGIONS ───────────────────────
# Kept as explicit (city, zip) pairs rather than generated, so every ZIP is
# inside the real prefix range the eligibility gate accepts.
STATE_PLACES: dict[str, list[tuple[str, str]]] = {
    "TX": [("Austin", "78745"), ("Dallas", "75201"), ("Houston", "77002"),
           ("San Antonio", "78205"), ("Fort Worth", "76102")],
    "CA": [("Los Angeles", "90013"), ("San Jose", "95113"), ("Oakland", "94607"),
           ("Sacramento", "95814"), ("Fresno", "93721")],
    "WA": [("Seattle", "98107"), ("Spokane", "99201"), ("Tacoma", "98402"),
           ("Everett", "98201"), ("Bellingham", "98225")],
    "MI": [("Detroit", "48226"), ("Grand Rapids", "49503"), ("Lansing", "48933"),
           ("Ann Arbor", "48104"), ("Flint", "48502")],
}

# Invented surnames — not drawn from any real directory.
_SURNAMES = [
    "Vandermolt", "Quillfeather", "Brackenwaite", "Orrimander", "Thistlewood",
    "Marrowgate", "Pennyfarthing", "Grimsdotter", "Yarrowfield", "Halbrooke",
    "Cindermere", "Wexlowe", "Ravenscroft", "Dunmorrow", "Ashenvale",
    "Corrigal", "Vellichor", "Stormhollow", "Fennimore", "Blackwold",
]
_GIVEN = [
    "Marisol", "Dashiell", "Ottoline", "Cassius", "Elodie", "Barnaby",
    "Seraphina", "Thaddeus", "Wilhelmina", "Ignatius", "Perpetua", "Lysander",
    "Anneliese", "Cornelius", "Rosalind", "Ambrose", "Genevieve", "Peregrine",
    "Clementine", "Fitzwilliam",
]
_STREETS = [
    "Halloway Bend", "Kestrel Row", "Marlin Reach", "Ondine Way",
    "Pellham Rise", "Sable Court", "Tanager Loop", "Umbra Lane",
    "Wrenfield Pass", "Yarrow Terrace",
]

# Invented furnisher names. Deliberately not real collectors or banks: a test
# fixture that names a real company invites someone to paste it into a letter.
_FURNISHERS = [
    "NORTHGATE RECOVERY LLC", "PELICAN ASSET PARTNERS", "STONEBRIDGE CARD SVC",
    "MERIDIAN PORTFOLIO GRP", "CALDERA LENDING CO", "ARBOR CREST BANK NA",
    "TIDEWATER COLLECTIONS", "VERGE FINANCIAL SVCS", "HOLLOWAY CREDIT UNION",
    "SUMMIT LEDGER RECOVERY", "BRIGHTON AUTO FINANCE", "CROWN MEADOW MEDICAL",
]
_ORIGINALS = [
    "ARBOR CREST BANK NA", "CALDERA LENDING CO", "STONEBRIDGE CARD SVC",
    "HOLLOWAY CREDIT UNION",
]


@dataclass(frozen=True)
class Account:
    """One synthetic tradeline, plus the ground it was built to trigger."""

    furnisher: str
    account_number: str
    loan_type: str
    status: str
    opened: date
    dofd: date | None
    balance: int
    high_credit: int
    credit_limit: int | None
    past_due: int
    narrative: str
    closed: bool
    grid: str
    original_creditor: str
    # What this account is here to exercise. "" means it is a clean account
    # that must produce no dispute at all — the negative case.
    expects: str


@dataclass(frozen=True)
class Profile:
    """A synthetic consumer and their file."""

    seed: int
    name: str
    street: str
    city: str
    state: str
    zip_code: str
    dob: str
    ssn_last4: str
    phone: str
    email: str
    accounts: list[Account] = field(default_factory=list)

    @property
    def intake(self) -> dict:
        return {
            "name": self.name, "address": self.street, "city": self.city,
            "state": self.state, "zip": self.zip_code, "dob": self.dob,
            "ssn_last4": self.ssn_last4, "phone": self.phone,
            "email": self.email,
        }

    @property
    def expected_grounds(self) -> set[str]:
        return {a.expects for a in self.accounts if a.expects}

    @property
    def clean_accounts(self) -> int:
        return sum(1 for a in self.accounts if not a.expects)

    @property
    def source_dofds(self) -> set[str]:
        """Every DOFD the file actually states, ISO formatted."""
        return {a.dofd.isoformat() for a in self.accounts if a.dofd}


# ── Account archetypes ──────────────────────────────────────────────────────
# Each builder takes an rng and "today", and returns one Account. The `expects`
# field records the dispute ground the account is designed to produce, so the
# runner can assert the engine actually found it.

def _acct_no(rng: random.Random) -> str:
    return f"*{rng.randint(1000, 9999)}"


def _obsolete_collection(rng: random.Random, today: date) -> Account:
    """DOFD past the seven-year window: § 1681c, and it is arithmetic."""
    dofd = today - timedelta(days=rng.randint(2740, 3600))
    return Account(
        furnisher=rng.choice(_FURNISHERS), account_number=_acct_no(rng),
        loan_type="Collection", status="Collection account",
        opened=dofd + timedelta(days=rng.randint(30, 200)), dofd=dofd,
        balance=rng.randint(150, 4200), high_credit=rng.randint(150, 4200),
        credit_limit=None, past_due=0, narrative="Placed for collection",
        closed=True, grid="C C C", original_creditor=rng.choice(_ORIGINALS),
        expects="obsolete",
    )


def _reaged_collection(rng: random.Random, today: date) -> Account:
    """DOFD later than the tradeline's own open date."""
    opened = today - timedelta(days=rng.randint(400, 900))
    return Account(
        furnisher=rng.choice(_FURNISHERS), account_number=_acct_no(rng),
        loan_type="Collection", status="Collection account",
        opened=opened, dofd=opened + timedelta(days=rng.randint(60, 300)),
        balance=rng.randint(200, 6000), high_credit=rng.randint(200, 6000),
        credit_limit=None, past_due=rng.randint(100, 900),
        narrative="Placed for collection", closed=False, grid="C 120 90",
        original_creditor=rng.choice(_ORIGINALS), expects="re_aging",
    )


def _charge_off(rng: random.Random, today: date) -> Account:
    opened = today - timedelta(days=rng.randint(900, 2000))
    return Account(
        furnisher=rng.choice(_FURNISHERS), account_number=_acct_no(rng),
        loan_type="Credit Card", status="Charge-off",
        opened=opened, dofd=opened + timedelta(days=rng.randint(120, 400)),
        balance=rng.randint(400, 9000), high_credit=rng.randint(900, 12000),
        credit_limit=rng.choice([None, rng.randint(1000, 15000)]),
        past_due=rng.randint(300, 4000), narrative="Charged off account",
        closed=True, grid="CO 180 150 120", original_creditor="",
        expects="charge_off",
    )


def _balance_equals_past_due(rng: random.Random, today: date) -> Account:
    """Balance and amount-past-due identical, no credit limit."""
    amount = rng.randint(300, 2500)
    opened = today - timedelta(days=rng.randint(300, 1200))
    return Account(
        furnisher=rng.choice(_FURNISHERS), account_number=_acct_no(rng),
        loan_type="Installment", status="Past due 90 days",
        opened=opened, dofd=opened + timedelta(days=rng.randint(90, 300)),
        balance=amount, high_credit=amount, credit_limit=None,
        past_due=amount, narrative="Account past due", closed=False,
        grid="90 60 30", original_creditor="", expects="balance_inaccuracy",
    )


def _medical_collection(rng: random.Random, today: date) -> Account:
    opened = today - timedelta(days=rng.randint(200, 1400))
    return Account(
        furnisher="CROWN MEADOW MEDICAL", account_number=_acct_no(rng),
        loan_type="Collection", status="Collection account",
        opened=opened, dofd=opened - timedelta(days=rng.randint(30, 240)),
        balance=rng.randint(80, 3200), high_credit=rng.randint(80, 3200),
        credit_limit=None, past_due=0,
        narrative="Medical collection, placed for collection", closed=True,
        grid="C C", original_creditor="", expects="medical_debt",
    )


def _auto_repossession(rng: random.Random, today: date) -> Account:
    opened = today - timedelta(days=rng.randint(1100, 2400))
    return Account(
        furnisher="BRIGHTON AUTO FINANCE", account_number=_acct_no(rng),
        loan_type="Auto Loan", status="Repossession",
        opened=opened, dofd=opened + timedelta(days=rng.randint(300, 700)),
        balance=rng.randint(2000, 18000), high_credit=rng.randint(9000, 40000),
        credit_limit=None, past_due=rng.randint(1000, 9000),
        narrative="Repossession, deficiency balance", closed=True,
        grid="R 180 150", original_creditor="", expects="repossession",
    )


def _student_loan(rng: random.Random, today: date) -> Account:
    opened = today - timedelta(days=rng.randint(2000, 6000))
    return Account(
        furnisher="VERGE FINANCIAL SVCS", account_number=_acct_no(rng),
        loan_type="Student Loan", status="Paying as agreed",
        opened=opened, dofd=None, balance=rng.randint(1500, 42000),
        high_credit=rng.randint(1500, 42000), credit_limit=None, past_due=0,
        narrative="Student loan, transferred", closed=False, grid="",
        original_creditor="", expects="student_loan",
    )


def _clean_account(rng: random.Random, today: date) -> Account:
    """
    Nothing wrong with it. The engine must produce NO dispute for this.

    The negative case is the one a load test can never provide: a pipeline
    that reports a violation on a healthy tradeline is worse than one that
    finds nothing, because it puts a false claim in a letter.
    """
    opened = today - timedelta(days=rng.randint(700, 4000))
    limit = rng.randint(2000, 25000)
    return Account(
        furnisher=rng.choice(_FURNISHERS), account_number=_acct_no(rng),
        loan_type="Credit Card", status="Pays as agreed",
        opened=opened, dofd=None, balance=rng.randint(0, limit // 3),
        high_credit=rng.randint(limit // 3, limit), credit_limit=limit,
        past_due=0, narrative="Current account", closed=False, grid="",
        original_creditor="", expects="",
    )


ARCHETYPES = [
    _obsolete_collection, _reaged_collection, _charge_off,
    _balance_equals_past_due, _medical_collection, _auto_repossession,
    _student_loan, _clean_account,
]


# ── Profile construction ────────────────────────────────────────────────────

# Fixed reference date. A generated DOFD must not drift relative to "today" or
# an obsolete account silently stops being obsolete and the suite rots.
TODAY = date(2026, 9, 1)


def make_profile(index: int, state: str) -> Profile:
    """
    Profile `index` for `state`. Pure function of its arguments.

    The seed is `index`, so a failing profile is reproduced by asking for that
    index again — no log-scraping, no wall-clock.
    """
    rng = random.Random(index)
    city, zip_code = STATE_PLACES[state][index % len(STATE_PLACES[state])]

    # Shape of the file varies: some consumers bring one bad item, some bring
    # a dozen, and one in five brings a file with nothing wrong in it.
    if index % 5 == 4:
        picks = [_clean_account] * rng.randint(2, 4)
    else:
        n = rng.randint(3, 9)
        picks = [rng.choice(ARCHETYPES) for _ in range(n)]
        # Guarantee at least one clean account in most files, so the negative
        # assertion has something to bite on.
        if _clean_account not in picks:
            picks.append(_clean_account)

    accounts = [p(rng, TODAY) for p in picks]

    given = _GIVEN[index % len(_GIVEN)]
    surname = _SURNAMES[(index * 7) % len(_SURNAMES)]
    birth = date(rng.randint(1955, 2002), rng.randint(1, 12), rng.randint(1, 28))

    return Profile(
        seed=index,
        name=f"{given} {surname}",
        street=f"{rng.randint(100, 9899)} {rng.choice(_STREETS)}",
        city=city, state=state, zip_code=zip_code,
        dob=birth.isoformat(),
        ssn_last4=f"{rng.randint(1000, 9999)}",
        phone=f"{rng.randint(2, 9)}{rng.randint(10, 99)}555{rng.randint(1000, 9999)}",
        email=f"{given.lower()}.{surname.lower()}@example.invalid",
        accounts=accounts,
    )


def all_profiles(per_state: int = 5) -> list[Profile]:
    """`per_state` profiles for each beta region, in a stable order."""
    out: list[Profile] = []
    index = 0
    for state in sorted(STATE_PLACES):
        for _ in range(per_state):
            out.append(make_profile(index, state))
            index += 1
    return out


# ── Report rendering ────────────────────────────────────────────────────────

def _money(n: int | None) -> str:
    return "" if n is None else f"{n:,}.00"


def render_report(profile: Profile) -> str:
    """
    The profile as an Equifax-shaped export.

    Block headers are `\\n    NAME - Open\\n` and fields are `Label:  value`,
    which is what `equifax_parser._ACCOUNT_SPLIT` and `_field` read. The
    `888-EQUIFAX` line is in the header so the format sniff passes even for a
    file with no delinquency dates in it at all.
    """
    lines = [
        "EQUIFAX CREDIT FILE - SYNTHETIC TEST DATA (is_demo)",
        "This file was generated for automated testing. It describes no real",
        "person, no real creditor and no real debt.",
        "Consumer Referral Services 888-EQUIFAX",
        "",
        f"Name: {profile.name}",
        (f"Current Address: {profile.street}, {profile.city}, "
         f"{profile.state} {profile.zip_code}"),
        f"Date of Birth: {profile.dob}",
        f"Social Security Number: XXX-XX-{profile.ssn_last4}",
        "",
        "        ACCOUNT INFORMATION",
        "",
    ]

    for acct in profile.accounts:
        state_word = "Closed" if acct.closed else "Open"
        lines.append(f"    {acct.furnisher} - {state_word}")
        lines.append(f"Account Number: {acct.account_number} | "
                     f"Loan/Account Type: {acct.loan_type}")
        lines.append(f"Date Opened: {acct.opened.strftime('%m/%d/%Y')} | "
                     f"Date Reported: {TODAY.strftime('%m/%d/%Y')}")
        if acct.dofd:
            lines.append(
                f"Date of 1st Delinquency: {acct.dofd.strftime('%m/%d/%Y')}")
        else:
            lines.append("Date of 1st Delinquency:")
        lines.append(f"Balance: ${_money(acct.balance)} | "
                     f"High Credit: ${_money(acct.high_credit)}")
        lines.append(f"Credit Limit: {'$' + _money(acct.credit_limit) if acct.credit_limit else ''}")
        lines.append(f"Amount Past Due: ${_money(acct.past_due)}")
        lines.append(f"Status: {acct.status}")
        lines.append("Months Reviewed: 24")
        lines.append(f"Narrative Code(s): {acct.narrative}")
        if acct.original_creditor:
            lines.append(f"Original Creditor: {acct.original_creditor}")
        if acct.grid:
            lines.append("Payment History")
            lines.append(f"  {acct.grid}")
        lines.append("")

    return "\n".join(lines)


def assert_parseable(text: str) -> None:
    """
    Fail loudly here if the generated shape stops matching the parser.

    Without this a format drift shows up as an empty parse three layers away
    and reads as a product bug rather than a fixture bug.
    """
    markers = ("Loan/Account Type:", "Date of 1st Delinquency:", "888-EQUIFAX")
    hits = sum(1 for m in markers if m in text)
    if hits < 2:
        raise AssertionError(
            f"generated report matches only {hits} Equifax sniff marker(s); "
            f"equifax_parser.looks_like_equifax needs at least 2"
        )
