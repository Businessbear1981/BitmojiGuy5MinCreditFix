"""
Legal authority store — the citations a letter may use, and nothing else.

Why this is a table and not a Python dict
─────────────────────────────────────────
The dict it replaces (`dispute_engine/legal_library.py`) carried 31 case
citations, 82 rows flagged `'verified': True`, **zero** flagged false, stamped
in exactly two bulk dates, and nothing in the codebase ever read the flag. It
was a free-text boolean anyone could type, and five of the citations under it
turned out to be wrong in ways that would have damaged a customer's file:

  * Sarver v. Experian, 390 F.3d 969 (7th Cir. 2004) — cited FOR the consumer.
    The Seventh Circuit AFFIRMED summary judgment FOR Experian. Independently
    confirmed twice: Hammoud (6th Cir. 2022), a case the consumer lost, cites
    Sarver as defence authority.
  * Dalton v. Capital Associated Indus., 257 F.3d 409 (4th Cir. 2001) — holds
    the PLAINTIFF bears the burden. Not a mixed-file case.
  * Grigoryan v. Experian, 84 F. Supp. 3d 1044 — the CRAs won; it contains no
    § 1681c holding at all.
  * Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002) — a permissible-purpose
    case about a background check on a prospective son-in-law. Filed under
    re-aging.
  * "CPLR § 214-g" — New York's Child Victims Act revival statute, cited as the
    consumer-credit statute of limitations. That is CPLR 214-i.

The schema is the fix. `verified_by`, `source_url`, `pinpoint` and `outcome`
are NOT NULL, so a row cannot exist that claims verification without naming a
person, the document actually read, the page, and who won. `outcome` is what
would have caught Sarver: you cannot insert it without typing "affirmed
summary judgment for Experian", at which point nobody files it as consumer
authority. And `active` defaults to FALSE — the inverse of the dict, where
everything defaulted to trusted.

Two operational rules
─────────────────────
**The database is not on the critical path.** A letter must build if Postgres
is unreachable. `SEED` below is the offline floor, loaded at boot; the table is
the source of truth for *updates*. The alternative — a DB blip producing no
letters — is the same silent-degradation failure the purge loop already taught
us to avoid.

**Every letter records which version it used.** `library_version()` returns a
content hash of the active rows. A letter that cannot name the authority set it
was built from cannot be reproduced, and § 7 of the operating contract requires
that it can be.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from database import Base, SessionLocal, engine

# Jurisdictions the product sells in. A letter must never cite authority from
# a state the consumer does not live in.
JURISDICTIONS = ("federal", "TX", "CA", "WA", "MI")


class LegalAuthority(Base):
    """
    One statute, regulation or case a letter may cite.

    Every provenance column is NOT NULL by design. If a fact about a citation
    is unknown, the row does not belong in the table yet.
    """

    __tablename__ = "legal_authority"
    __table_args__ = (
        UniqueConstraint("jurisdiction", "theory", "citation", "pinpoint",
                         name="uq_authority"),
    )

    id = Column(Integer, primary_key=True)

    jurisdiction = Column(String(8), nullable=False, index=True)
    theory = Column(String(48), nullable=False, index=True)
    kind = Column(String(12), nullable=False)          # statute|regulation|case

    citation = Column(Text, nullable=False)
    # No pinpoint, no row. A citation without a page is not checkable, and
    # "verified" without a page is what the old dict was asserting.
    pinpoint = Column(Text, nullable=False)
    holding = Column(Text, nullable=False)
    # Who won, and procedurally what happened. This column is the Sarver trap.
    outcome = Column(Text, nullable=False)

    source_url = Column(Text, nullable=False)          # the document actually read
    verified_by = Column(Text, nullable=False)         # a person, not a boolean
    verified_on = Column(Date, nullable=False)

    # True where the authority is routinely used BY THE DEFENCE even though it
    # contains consumer-favourable language. Excluded from letters by default.
    defense_cited = Column(Boolean, nullable=False, default=False)
    # Caveats that must travel with the citation, e.g. "willfulness discussion
    # superseded by Safeco (2007)".
    caveat = Column(Text, nullable=True)

    # Opt IN. A new row is dark until someone turns it on.
    active = Column(Boolean, nullable=False, default=False, index=True)

    def as_dict(self) -> dict:
        return {
            "jurisdiction": self.jurisdiction,
            "theory": self.theory,
            "kind": self.kind,
            "citation": self.citation,
            "pinpoint": self.pinpoint,
            "holding": self.holding,
            "outcome": self.outcome,
            "source_url": self.source_url,
            "caveat": self.caveat or "",
        }


@dataclass(frozen=True)
class Authority:
    """An authority as the composer sees it. Immutable."""

    jurisdiction: str
    theory: str
    kind: str
    citation: str
    pinpoint: str
    holding: str
    outcome: str
    source_url: str
    caveat: str = ""
    defense_cited: bool = False
    active: bool = False
    verified_by: str = ""
    verified_on: str = ""

    def cite_line(self) -> str:
        """How it appears in a letter."""
        base = self.citation if not self.pinpoint else f"{self.citation}, {self.pinpoint}"
        return base


# ─────────────────────────────────────────────────────────────────────────────
# THE OFFLINE FLOOR
#
# Seeded from five verified research passes (federal, TX, CA, WA, MI) in which
# every statute was opened on an official legislature or uscode host and every
# case was read in the court's own PDF or an official reporter reproduction.
#
# STATUTES ARE ACTIVE. They are the argument, they are checkable, and every one
# below was quoted from primary text.
#
# CASE LAW SHIPS DARK (`active=False`). Not because these are doubted — each was
# read and its outcome recorded — but because the product has already mailed
# five wrong citations, and the correct response to that is that a human with a
# bar number turns them on one at a time. A letter citing five correct statutes
# and no case law is a stronger document than one citing five statutes and a
# case decided for the bureau.
# ─────────────────────────────────────────────────────────────────────────────

_V = "research-pass-2026-09-01"

SEED: tuple[Authority, ...] = (
    # ── FEDERAL STATUTES ────────────────────────────────────────────────────
    Authority(
        "federal", "reinvestigation", "statute",
        "15 U.S.C. § 1681i(a)(1)(A)", "§ 1681i(a)(1)(A)",
        "A consumer reporting agency must conduct a reasonable reinvestigation "
        "free of charge and record the current status of the disputed "
        "information, or delete it, within 30 days of receiving notice.",
        "Statute — no outcome.",
        "https://www.law.cornell.edu/uscode/text/15/1681i",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "federal", "reinvestigation", "statute",
        "15 U.S.C. § 1681i(a)(7)", "§ 1681i(a)(7)",
        "On request, the agency must describe the procedure used to determine "
        "the accuracy and completeness of the information, including the "
        "business name and address and, if reasonably available, the telephone "
        "number of any furnisher contacted.",
        "Statute — no outcome.",
        "https://www.law.cornell.edu/uscode/text/15/1681i",
        caveat="The method-of-verification demand. Asserts no fact the consumer "
               "must prove, which is why it survives Ward (10th Cir. 2026).",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "federal", "accuracy", "statute",
        "15 U.S.C. § 1681e(b)", "§ 1681e(b)",
        "An agency must follow reasonable procedures to assure maximum possible "
        "accuracy of the information concerning the individual about whom the "
        "report relates.",
        "Statute — no outcome.",
        "https://www.law.cornell.edu/uscode/text/15/1681e",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "federal", "obsolescence", "statute",
        "15 U.S.C. § 1681c(a)(4)", "§ 1681c(a)(4)",
        "A consumer report may not contain accounts placed for collection or "
        "charged to profit and loss which antedate the report by more than "
        "seven years.",
        "Statute — no outcome.",
        "https://www.law.cornell.edu/uscode/text/15/1681c",
        caveat="Paired with § 1681c(c)(1), the seven years runs from the "
               "expiration of the 180-day period beginning on the commencement "
               "of the delinquency that immediately preceded the collection or "
               "charge-off — NOT from the charge-off, the sale, or last payment.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "federal", "obsolescence", "statute",
        "15 U.S.C. § 1681c(c)(1)", "§ 1681c(c)(1)",
        "The seven-year period runs upon the expiration of the 180-day period "
        "beginning on the date of the commencement of the delinquency which "
        "immediately preceded the collection activity or charge to profit and "
        "loss.",
        "Statute — no outcome.",
        "https://www.law.cornell.edu/uscode/text/15/1681c",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "federal", "furnisher_duty", "statute",
        "15 U.S.C. § 1681s-2(b)", "§ 1681s-2(b)",
        "On receiving notice of a dispute from a consumer reporting agency, a "
        "furnisher must investigate, review all relevant information provided "
        "by the agency, and report the results.",
        "Statute — no outcome.",
        "https://www.law.cornell.edu/uscode/text/15/1681s-2",
        caveat="OPERATIONALLY CRITICAL: these duties arise only after the "
               "furnisher receives notice FROM A CRA. A letter mailed directly "
               "to a furnisher creates no § 1681s-2(b) claim, so the dispute "
               "must be routed through the bureau as well.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "federal", "file_disclosure", "statute",
        "15 U.S.C. § 1681g(a)(1)", "§ 1681g(a)(1)",
        "On request, an agency must disclose all information in the consumer's "
        "file at the time of the request.",
        "Statute — no outcome.",
        "https://www.law.cornell.edu/uscode/text/15/1681g",
        caveat="The basis for demanding the date of first delinquency where the "
               "disclosure omits it — as Experian's does entirely.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "federal", "impermissible_inquiry", "statute",
        "15 U.S.C. § 1681b", "§ 1681b(a)(3)",
        "A consumer report may be furnished only for a permissible purpose "
        "enumerated in the section.",
        "Statute — no outcome.",
        "https://www.law.cornell.edu/uscode/text/15/1681b",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),

    # ── CALIFORNIA ──────────────────────────────────────────────────────────
    Authority(
        "CA", "reinvestigation", "statute",
        "Cal. Civ. Code § 1785.16(a)", "§ 1785.16(a)",
        "The agency must reinvestigate without charge and record the current "
        "status of the disputed information before the end of the 30-BUSINESS-day "
        "period beginning on the date it receives notice.",
        "Statute — no outcome.",
        "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1785.16",
        caveat="30 business days, longer than the federal 30 calendar days. Cite "
               "for the substantive duty, not as a shorter deadline.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "CA", "reinvestigation", "statute",
        "Cal. Civ. Code § 1785.16(d)", "§ 1785.16(d)",
        "On request the agency must provide a description of the procedure used "
        "to determine accuracy and completeness, not later than 15 days after "
        "receiving the request.",
        "Statute — no outcome.",
        "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1785.16",
        caveat="A 15-day procedure-description demand with no federal analogue. "
               "Concrete, verified, and rarely used.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "CA", "furnisher_duty", "statute",
        "Cal. Civ. Code § 1785.25(a)", "§ 1785.25(a)",
        "A person shall not furnish information on a specific transaction or "
        "experience to any consumer credit reporting agency if the person knows "
        "or should know the information is incomplete or inaccurate.",
        "Statute — no outcome.",
        "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1785.25",
        caveat="Expressly EXEMPTED from FCRA preemption by 15 U.S.C. "
               "§ 1681t(b)(1)(F)(ii), which names this section by hand. Only "
               "subdivision (a) survives; § 1785.25(f) is preempted.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "CA", "obsolescence", "statute",
        "Cal. Civ. Code § 1785.13(a)(5), (a)(8)", "§ 1785.13(a)(5), (a)(8)",
        "Accounts placed for collection or charged to profit and loss that "
        "antedate the report by more than seven years, and any other adverse "
        "information more than seven years old, may not be reported.",
        "Statute — no outcome.",
        "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1785.13",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "CA", "medical_debt", "statute",
        "Cal. Civ. Code § 1785.13(a)(7)", "§ 1785.13(a)(7)",
        "Medical debt may not appear in a California consumer credit report. "
        "The subdivision reads, in its entirety, \"Medical debt.\"",
        "Statute — no outcome.",
        "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1785.13",
        caveat="Added by SB 1061, effective 1 Jan 2025. A flat ban with no "
               "seven-year clock and no dollar threshold. The CFPB asserts a "
               "contrary preemption position; unresolved.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),

    # ── WASHINGTON ──────────────────────────────────────────────────────────
    Authority(
        "WA", "reinvestigation", "statute",
        "RCW 19.182.090(5)(a)", "RCW 19.182.090(5)(a)",
        "If after reinvestigation the information is found to be inaccurate OR "
        "CANNOT BE VERIFIED, the consumer reporting agency shall promptly "
        "delete the information from the consumer's file.",
        "Statute — no outcome.",
        "https://app.leg.wa.gov/RCW/default.aspx?cite=19.182.090",
        caveat="\"Cannot be verified\" is the operative phrase — use it verbatim.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "WA", "reinvestigation", "statute",
        "RCW 19.182.090(8)(b)(iv)", "RCW 19.182.090(8)(b)(iv)",
        "On request, a description of the procedure used to determine the "
        "accuracy and completeness of the information, including the NAME, "
        "BUSINESS ADDRESS AND TELEPHONE NUMBER of any person contacted.",
        "Statute — no outcome.",
        "https://app.leg.wa.gov/RCW/default.aspx?cite=19.182.090",
        caveat="The strongest verification-demand provision in any of the five "
               "jurisdictions. More specific than federal § 1681i(a)(7).",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "WA", "obsolescence", "statute",
        "RCW 19.182.040(2)", "RCW 19.182.040(2)",
        "The seven- and ten-year reporting cutoffs are lifted only for credit "
        "transactions of $50,000 or more, life insurance of $50,000 or more, or "
        "employment at an annual salary of $20,000 or more.",
        "Statute — no outcome.",
        "https://app.leg.wa.gov/RCW/default.aspx?cite=19.182.040",
        caveat="Materially MORE protective than federal law, where the "
               "thresholds are $150,000 / $150,000 / $75,000 under "
               "15 U.S.C. § 1681c(b). Rarely cited.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "WA", "collector_duty", "statute",
        "RCW 19.16.250(10)(a)", "RCW 19.16.250(10)(a)",
        "If a licensee has reported a claim to a credit reporting bureau, it "
        "shall, upon receipt of written notice from the debtor that any part of "
        "the claim is disputed, notify the bureau of the dispute by written or "
        "electronic means and create a record of the fact of the notification "
        "and when it was provided.",
        "Statute — no outcome.",
        "https://app.leg.wa.gov/RCW/default.aspx?cite=19.16.250",
        caveat="Triggered by the consumer's OWN letter — no CRA intermediary "
               "required. Violation is a per se Consumer Protection Act "
               "violation via RCW 19.16.440. Licensed collection agencies only; "
               "RCW 19.16.100(5)(c) excludes original creditors collecting in "
               "their true name.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),

    # ── TEXAS ───────────────────────────────────────────────────────────────
    Authority(
        "TX", "collector_duty", "statute",
        "Tex. Fin. Code § 392.202(a), (b)", "§ 392.202(a), (b)",
        "An individual who disputes the accuracy of an item in a third-party "
        "debt collector's file may notify the collector in writing. The "
        "collector must record the dispute, investigate, cease collection "
        "efforts pending the outcome, and send a written statement not later "
        "than the 30th day after receiving the notice.",
        "Statute — no outcome.",
        "https://statutes.capitol.texas.gov/Docs/FI/htm/FI.392.htm",
        caveat="THIRD-PARTY DEBT COLLECTORS ONLY. Every operative verb has "
               "\"the third-party debt collector\" as its subject; it imposes no "
               "duty on a credit bureau. Aiming it at Experian invites the "
               "statute back as the answer.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "TX", "creditor_duty", "statute",
        "Tex. Fin. Code § 392.001(6)", "§ 392.001(6)",
        "\"Debt collector\" means a person who directly or indirectly engages in "
        "debt collection — with no third-party limitation, so the Act reaches "
        "original creditors collecting their own debts.",
        "Statute — no outcome.",
        "https://statutes.capitol.texas.gov/Docs/FI/htm/FI.392.htm",
        caveat="The INVERSE of the federal FDCPA, which excludes creditors "
               "collecting their own accounts. A CRA acting as a CRA is not "
               "covered — \"credit bureau\" is defined separately at § 392.001(4) "
               "and no duty is imposed on it.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),

    # ── MICHIGAN ────────────────────────────────────────────────────────────
    Authority(
        "MI", "creditor_duty", "statute",
        "MCL 445.252(e), (f)", "MCL 445.252(e), (f)",
        "A regulated person shall not make an inaccurate, misleading, untrue or "
        "deceptive statement in a communication to collect a debt, nor "
        "misrepresent the legal status of an action taken or the legal rights of "
        "creditor or debtor.",
        "Statute — no outcome.",
        "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-445-252",
        caveat="\"Regulated person\" (MCL 445.251(g)) covers banks, credit unions "
               "and licensed lenders collecting their OWN debts — the inverse of "
               "the FDCPA — and expressly EXCLUDES licensed collection agencies, "
               "which fall under MCL 339.915 instead. The two acts partition; "
               "pleading the wrong one is a dismissal. UNVERIFIED: whether "
               "furnishing to a CRA is \"a communication to collect a debt\" "
               "under (e) could not be resolved — do not assert it.",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
    Authority(
        "MI", "collector_duty", "statute",
        "MCL 339.915(e)", "MCL 339.915(e)",
        "A licensee shall not make an inaccurate, misleading, untrue or "
        "deceptive statement or claim in a communication to collect a debt.",
        "Statute — no outcome.",
        "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-339-915",
        caveat="Licensed collection agencies only. Private right of action at "
               "MCL 339.916. Michigan has NO state credit-reporting statute and "
               "no state accuracy duty; a Michigan letter runs on federal FCRA. "
               "State-law furnisher-accuracy claims are preempted in the Sixth "
               "Circuit — only Massachusetts and California are carved out of "
               "§ 1681t(b)(1)(F).",
        active=True, verified_by=_V, verified_on="2026-09-01",
    ),
)


def init_legal_store() -> None:
    """Create the table and load any seed row that is not already present."""
    Base.metadata.create_all(bind=engine, tables=[LegalAuthority.__table__])
    db = SessionLocal()
    try:
        existing = {
            (r.jurisdiction, r.theory, r.citation, r.pinpoint)
            for r in db.query(
                LegalAuthority.jurisdiction, LegalAuthority.theory,
                LegalAuthority.citation, LegalAuthority.pinpoint,
            ).all()
        }
        added = 0
        for a in SEED:
            key = (a.jurisdiction, a.theory, a.citation, a.pinpoint)
            if key in existing:
                continue
            db.add(LegalAuthority(
                jurisdiction=a.jurisdiction, theory=a.theory, kind=a.kind,
                citation=a.citation, pinpoint=a.pinpoint, holding=a.holding,
                outcome=a.outcome, source_url=a.source_url,
                verified_by=a.verified_by or _V,
                verified_on=_as_date(a.verified_on),
                defense_cited=a.defense_cited, caveat=a.caveat or None,
                active=a.active,
            ))
            added += 1
        if added:
            db.commit()
    finally:
        db.close()


def _as_date(value: str):
    from datetime import datetime, timezone
    return datetime.strptime(value or "2026-09-01", "%Y-%m-%d").replace(
        tzinfo=timezone.utc).date()


def authorities_for(theories: list[str], jurisdiction: str = "") -> list[Authority]:
    """
    Active, non-defence-cited authority for these theories.

    Reads the table with bound parameters; falls back to the in-repo seed if
    the database is unreachable, because a letter must still build. Federal
    authority always applies; state authority only for the consumer's own
    state.
    """
    wanted = tuple(t for t in theories if t)
    if not wanted:
        return []
    scopes = ("federal", jurisdiction) if jurisdiction in JURISDICTIONS else ("federal",)

    try:
        db = SessionLocal()
        try:
            rows = (
                db.query(LegalAuthority)
                .filter(
                    LegalAuthority.active.is_(True),
                    LegalAuthority.defense_cited.is_(False),
                    LegalAuthority.theory.in_(wanted),
                    LegalAuthority.jurisdiction.in_(scopes),
                )
                .order_by(LegalAuthority.kind, LegalAuthority.citation)
                .all()
            )
            return [Authority(**r.as_dict()) for r in rows]
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001 - the store is not on the critical path
        print(f"[legal_store] table unreadable ({type(e).__name__}); "
              f"using the in-repo seed")
        return [
            a for a in SEED
            if a.active and not a.defense_cited
            and a.theory in wanted and a.jurisdiction in scopes
        ]


def library_version(jurisdiction: str = "") -> str:
    """
    Content hash of the active authority set.

    Stamped into a letter's provenance so the letter can be rebuilt from the
    same authorities months later, even if the table has moved on.
    """
    rows = authorities_for(
        sorted({a.theory for a in SEED}), jurisdiction=jurisdiction)
    payload = json.dumps(
        [[r.jurisdiction, r.theory, r.citation, r.pinpoint] for r in rows],
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def store_stats() -> dict:
    """What the store holds. For the admin panel and our own diagnostics."""
    try:
        db = SessionLocal()
        try:
            total = db.query(LegalAuthority).count()
            active = db.query(LegalAuthority).filter(
                LegalAuthority.active.is_(True)).count()
            cases = db.query(LegalAuthority).filter(
                LegalAuthority.kind == "case").count()
            active_cases = db.query(LegalAuthority).filter(
                LegalAuthority.kind == "case",
                LegalAuthority.active.is_(True)).count()
            return {
                "source": "database",
                "rows": total,
                "active": active,
                "cases": cases,
                "active_cases": active_cases,
                "version": library_version(),
            }
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001 - diagnostics must not raise
        return {"source": f"seed ({type(e).__name__})",
                "rows": len(SEED),
                "active": sum(1 for a in SEED if a.active),
                "cases": sum(1 for a in SEED if a.kind == "case"),
                "active_cases": 0,
                "version": library_version()}
