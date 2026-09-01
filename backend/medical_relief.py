"""
Medical debt — the relief routes that exist outside the dispute letter.

A medical collection is disputable like any other tradeline, and the rest of
this platform handles that. But medical debt is the one category where the
dispute is frequently the *second*-best move, because the bill itself is
often reducible or erasable at the source in ways no other debt is:

  - the charge may be wrong, and an itemised bill is free to demand
  - a non-profit hospital has a written financial-assistance policy it is
    obliged to have, and applying to it can retire the balance outright
  - the balance may never have been lawfully billable to the patient at all,
    if it came from out-of-network care the patient did not choose
  - the patient may have been Medicaid-eligible on the date of service

None of those are credit-report arguments. They are conversations with the
provider, and they can moot the tradeline rather than argue about it. This
module surfaces them next to the dispute so a consumer sees both.

── What this module will and will not say ─────────────────────────────────

It will say what the file shows: that a furnisher looks like a medical
provider or a medical collector, what the balance is, how old it is.

It will **not** say whether anyone qualifies for anything. Charity-care
thresholds are set per hospital, Medicaid rules are set per state, and the
credit-reporting treatment of medical collections has been changed by the
bureaus voluntarily, by regulation, and by litigation, more than once. This
module names the route and the authoritative source and stops.

── One thing it says loudly ───────────────────────────────────────────────

There is no federal grant program that pays an individual's medical bills or
credit-card debt. "Government grant" is the single most common framing used
to charge desperate people a fee for a form they could file free, and a
platform that surfaces the phrase without saying so is doing harm. See
`GRANT_REALITY` — it ships in every payload, not as a footnote.

This platform is not a hospital, an insurer, a benefits agency, or a
financial advisor. Nothing here is eligibility advice or legal advice.
"""
from __future__ import annotations

from datetime import datetime, timezone

# ── Recognising medical debt on a credit report ────────────────────────────
# Medical collections are frequently reported under the collector's name with
# no clue that the underlying service was medical. These markers catch the
# cases where the report does say so; a consumer can flag the rest themselves,
# which is why `analyze_medical()` accepts consumer-marked item ids.

PROVIDER_MARKERS = (
    "hospital", "health", "healthcare", "medical", "medicine", "clinic",
    "physician", "doctors", "dental", "dentist", "orthodon", "radiolog",
    "anesthes", "pathology", "surgery", "surgical", "emergency", "urgent care",
    "ambulance", "emt", "ems", "laborator", "imaging", "oncolog", "cardiolog",
    "orthoped", "pediatric", "obgyn", "ob gyn", "womens care", "family care",
    "wellness", "rehab", "therapy", "psychiatr", "behavioral health",
    "sleep center", "dialysis", "hospice", "home health", "nursing",
    "st jude", "st marys", "st. marys", "kaiser", "mayo", "cleveland clinic",
    "memorial", "baptist health", "methodist hospital", "presbyterian",
    "mercy health", "ascension", "advent health", "adventhealth", "sutter",
    "hca ", "tenet health", "community health system",
)

# Collection agencies whose book of business is predominantly medical. Their
# presence is a strong hint the underlying debt was a bill for care, even when
# the tradeline says nothing about medicine.
MEDICAL_COLLECTOR_MARKERS = (
    "medicredit", "medical revenue", "med business", "medbusiness",
    "healthcare revenue", "hrrg", "arstrat", "amca", "american medical coll",
    "medical data systems", "medical recovery", "medicalcoll",
    "professional account", "account resolution", "cardon", "credit systems",
    "npas", "parallon", "avectus", "revco", "receivable solutions",
)

# Account-type strings the bureaus use.
MEDICAL_TYPE_MARKERS = ("medical", "healthcare", "health care")


# ── The standing disclaimer, carried in every payload ──────────────────────
MEDICAL_DISCLAIMER = (
    "This is a pointer to official sources, not eligibility advice. This "
    "platform is not a hospital, insurer, benefits agency, or financial "
    "advisor, and it cannot determine whether you qualify for anything. "
    "Charity-care rules are set by each hospital, Medicaid rules are set by "
    "each state, and both change. Confirm everything with the provider and "
    "your state's agency before acting."
)

# Shipped with every payload. This is the anti-scam content and it is not
# optional — see the module docstring.
GRANT_REALITY = {
    "headline": "There is no federal grant that pays your medical or credit debt.",
    "detail":
        "Federal grants go to organisations, states and researchers — not to "
        "individuals to pay personal bills. Anyone who offers to get you a "
        "'government debt relief grant', charges a fee to apply for one, or "
        "asks for a payment to 'release' grant money, is running a scam. "
        "There is never a fee to apply for a real benefit programme.",
    "what_is_real":
        "What does exist is need-based assistance: hospital charity care, "
        "Medicaid, state and county indigent-care funds, utility and rent "
        "assistance, and disease-specific charitable funds. Those are real, "
        "they are free to apply for, and they are listed below.",
    "official_directories": [
        {"name": "Benefits.gov — official directory of federal benefit programmes "
                 "individuals can apply for",
         "url": "https://www.benefits.gov"},
        {"name": "USAGov on grant scams — how the government describes this scam",
         "url": "https://www.usa.gov/scams-and-fraud"},
        {"name": "Grants.gov — federal grants to organisations, not individuals. "
                 "Linked so you can see for yourself who is eligible.",
         "url": "https://www.grants.gov"},
        {"name": "FTC complaint line, if someone has charged you for this",
         "url": "https://reportfraud.ftc.gov"},
    ],
}


# ── The relief routes ──────────────────────────────────────────────────────
# `generally_for` describes who the route exists to serve in the loosest terms
# still useful. No dollar thresholds, no income multiples, no deadlines — all
# of those are set per hospital or per state and none can be verified here.

RELIEF_ROUTES: dict[str, dict] = {
    "itemized_bill": {
        "name": "Demand an itemised bill",
        "kind": "first_step",
        "generally_for":
            "Everyone with a medical balance, before doing anything else. A "
            "summary balance hides duplicate charges, services never "
            "rendered, and coding errors. You are entitled to ask the "
            "provider for the itemisation behind the number.",
        "why_it_matters":
            "This is also what makes a dispute letter strong. A balance you "
            "have asked the provider to itemise, and which they cannot "
            "itemise, is a balance whose accuracy the furnisher cannot "
            "confirm to the bureau either.",
        "documents_to_gather": [
            "The itemised statement, with CPT/HCPCS billing codes",
            ("Your insurer's Explanation of Benefits (EOB) for the same dates "
            "of service"),
            "Any bill you already paid toward the same visit",
        ],
        "verify_at": "",
        "cost": "Free. Ask the provider's billing department in writing.",
    },
    "charity_care": {
        "name": "Hospital financial assistance (charity care)",
        "kind": "reduce_or_erase",
        "generally_for":
            "Patients treated at a non-profit hospital. Federal tax law "
            "(26 U.S.C. § 501(r)) requires a tax-exempt hospital to maintain "
            "a written financial assistance policy and to publicise it. Who "
            "qualifies, and for how much, is set by each hospital in its own "
            "policy — there is no single national standard.",
        "why_it_matters":
            "Financial assistance can reduce or eliminate the balance "
            "outright rather than argue about it, and many hospitals will "
            "consider an application even after the account has gone to "
            "collections. Ask about their policy on accounts already placed "
            "with a collector.",
        "documents_to_gather": [
            ("The hospital's Financial Assistance Policy and its application "
            "form — they are required to be publicly available; ask billing "
            "or look on the hospital's own website"),
            ("Proof of household income (pay stubs, tax return, benefit award "
            "letters)"),
            "Household size and any other medical costs you are carrying",
        ],
        "verify_at": "",
        "cost": "Free to apply. Nobody needs to be paid to file it for you.",
        "note":
            "Ask the hospital directly whether it is a non-profit and what "
            "its policy says about accounts that have already been reported "
            "to a credit bureau. Under the § 501(r) rules, reporting a "
            "patient to a credit bureau is treated as an extraordinary "
            "collection action, which a tax-exempt hospital is limited in "
            "taking before it has made reasonable efforts to determine "
            "whether the patient is eligible for assistance. If that sequence "
            "was not followed in your case, raise it with the hospital and "
            "consider your state hospital regulator.",
    },
    "no_surprises": {
        "name": "No Surprises Act protections",
        "kind": "may_not_be_owed",
        "generally_for":
            "Patients billed by an out-of-network provider for emergency "
            "care, or by an out-of-network provider working at an in-network "
            "facility, and uninsured or self-pay patients who were not given "
            "a good-faith estimate before scheduled care.",
        "why_it_matters":
            "Where the Act applies, the balance may not be lawfully billable "
            "to you at all. A bill you do not owe is not a debt to negotiate "
            "— it is a debt to have withdrawn, which also removes the "
            "grounds for reporting it.",
        "documents_to_gather": [
            ("The bill, and the name and network status of every provider who "
            "billed you for that visit"),
            "Your insurer's EOB showing how the claim was processed",
            ("Any good-faith estimate you were given before the care, or a "
            "note that you were given none"),
            ("Any consent form you were asked to sign waiving these "
            "protections — read it, because some care cannot be waived"),
        ],
        "verify_at": "https://www.cms.gov/nosurprises",
        "cost": "Free. There is a federal complaint line and a "
                "patient–provider dispute resolution process.",
        "note":
            "The federal No Surprises Help Desk takes complaints directly. "
            "Start at cms.gov/nosurprises rather than with the collector.",
    },
    "medicaid_retroactive": {
        "name": "Medicaid, including coverage backdated to the date of service",
        "kind": "may_not_be_owed",
        "generally_for":
            "Patients who were financially eligible for Medicaid at the time "
            "they were treated, even if they did not apply until later. Many "
            "states allow coverage to be backdated to a period before the "
            "application. How far back, and who qualifies, is set by each "
            "state and varies.",
        "why_it_matters":
            "If Medicaid covers the date of service, the provider bills "
            "Medicaid instead of you, and the balance goes away rather than "
            "being disputed.",
        "documents_to_gather": [
            "Dates of service for every bill you are carrying",
            ("Income and household documentation for those months, not for "
            "today"),
            ("The provider's billing contact, so they can rebill if coverage "
            "is granted"),
        ],
        "verify_at": "https://www.medicaid.gov/about-us/where-can-people-get-help-medicaid-chip",
        "cost": "Free to apply through your state agency.",
        "note":
            "Ask your state Medicaid agency specifically about retroactive "
            "coverage and about hospital presumptive eligibility — hospitals "
            "can often start that process for you.",
    },
    "sliding_scale": {
        "name": "Community health centre sliding-fee care",
        "kind": "going_forward",
        "generally_for":
            "Anyone needing ongoing care they cannot afford. Federally "
            "funded health centres are required to offer a sliding fee "
            "schedule based on income, and they see patients regardless of "
            "insurance status.",
        "why_it_matters":
            "This does not retire an old bill. It stops the next one, which "
            "is the difference between clearing a report once and keeping it "
            "clear.",
        "documents_to_gather": [
            "Proof of household income",
            "Your current prescriptions and care needs",
        ],
        "verify_at": "https://findahealthcenter.hrsa.gov",
        "cost": "Sliding scale by income. Free to be seen and assessed.",
    },
    "provider_payment_plan": {
        "name": "Interest-free payment plan with the provider",
        "kind": "consolidation",
        "generally_for":
            "Patients who owe a balance they can pay over time but not at "
            "once. Most hospitals and many practices offer an in-house plan "
            "at no interest.",
        "why_it_matters":
            "This is the consolidation route that does not cost anything. "
            "It is not the same as a debt-consolidation loan or a debt "
            "settlement company — see the caution below.",
        "documents_to_gather": [
            ("The itemised bill and the final balance after any financial "
            "assistance is applied"),
            ("A written copy of the plan terms before you sign, including "
            "whether the provider will recall the account from collections"),
        ],
        "verify_at": "",
        "cost": "Usually free and interest-free. Get the terms in writing.",
        "note":
            "Ask two questions in writing before agreeing: will the account "
            "be recalled from the collection agency, and will the tradeline "
            "be updated or deleted on the credit report. Get the answers "
            "before the first payment, not after.",
    },
    "nonprofit_counseling": {
        "name": "Non-profit credit counselling",
        "kind": "consolidation",
        "generally_for":
            "People carrying debt across several categories who want a "
            "single structured plan. A genuine non-profit counselling agency "
            "gives a free budget review and can set up a debt management "
            "plan.",
        "why_it_matters":
            "It is the honest version of 'consolidation'. It is also not "
            "always the right move — a debt management plan can involve "
            "closing accounts, and it does not remove anything from a credit "
            "report.",
        "documents_to_gather": [
            "A full list of what you owe and to whom",
            "Your monthly income and fixed costs",
        ],
        "verify_at": "https://www.justice.gov/ust/list-credit-counseling-agencies-approved-pursuant-11-usc-111",
        "cost":
            "The initial counselling session should be free. Verify any "
            "agency against the Department of Justice's approved list before "
            "giving them anything.",
        "note":
            "Be careful with the word 'consolidation'. Debt settlement "
            "companies, consolidation loans, and non-profit counselling are "
            "three different things with very different costs. A company "
            "that asks for a fee before it does anything for you is one to "
            "walk away from.",
    },
}


# ── Field access ───────────────────────────────────────────────────────────
# Items arrive from the structured parser, the Claude extractor, or the
# keyword scanner, which disagree on a few field names.

def _first(item: dict, *keys, default=""):
    for k in keys:
        v = item.get(k)
        if v not in (None, ""):
            return v
    return default


def _text_blob(item: dict) -> str:
    return " ".join(str(_first(item, k, default="")) for k in (
        "furnisher", "target", "creditor", "account_name", "name",
        "original_creditor", "type", "account_type", "loan_type", "atype",
        "reason", "description", "status", "narrative",
    )).lower()


def _furnisher(item: dict) -> str:
    return str(_first(item, "furnisher", "creditor", "account_name", "name",
                      "target", default="Unknown"))


def _money(item: dict) -> float | None:
    for k in ("amount", "balance", "current_balance"):
        v = item.get(k)
        if v in (None, ""):
            continue
        try:
            return float(str(v).replace("$", "").replace(",", ""))
        except (TypeError, ValueError):
            continue
    return None


def _date(item: dict, *keys) -> datetime | None:
    for k in keys:
        raw = str(item.get(k) or "")
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(raw[:10], fmt).replace(
                    tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def is_medical(item: dict, consumer_marked: set | None = None) -> bool:
    """
    Does this tradeline look medical?

    Three ways to be true, in descending order of certainty:
      1. the consumer said so — they were there, the report was not
      2. the account type says medical
      3. the furnisher name is a provider or a predominantly medical collector

    A false positive here costs nothing: the consumer is shown a route that
    does not apply and ignores it. A false negative costs them the route
    entirely, so the markers lean inclusive.
    """
    if consumer_marked and (item.get("id") or item.get("item_id")) in consumer_marked:
        return True

    blob = _text_blob(item)
    if any(m in blob for m in MEDICAL_TYPE_MARKERS):
        return True
    if any(m in blob for m in PROVIDER_MARKERS):
        return True
    return any(m in blob for m in MEDICAL_COLLECTOR_MARKERS)


def _detection_basis(item: dict, consumer_marked: set | None) -> str:
    """Why we think this is medical — shown to the consumer so they can correct us."""
    ident = item.get("id") or item.get("item_id")
    if consumer_marked and ident in consumer_marked:
        return "you marked this account as a medical bill"

    blob = _text_blob(item)
    for m in MEDICAL_TYPE_MARKERS:
        if m in blob:
            return f"the report classifies this account as '{m}'"
    for m in PROVIDER_MARKERS:
        if m in blob:
            return (f"the furnisher name contains '{m}', which usually means a "
                    f"healthcare provider")
    for m in MEDICAL_COLLECTOR_MARKERS:
        if m in blob:
            return (f"'{m}' is a collection agency whose accounts are "
                    f"predominantly medical — confirm this one is yours and is "
                    f"medical before relying on it")
    return "unclear"


# ── Analysis ───────────────────────────────────────────────────────────────

def analyze_medical(items: list[dict],
                    consumer_marked: list | None = None) -> dict:
    """
    Which items look medical, and which relief routes are worth raising.

    Routes are surfaced by *situation*, never by eligibility. Every consumer
    with a medical balance sees the itemised-bill step and the charity-care
    route, because those apply to everyone and the report cannot tell us
    whether they will succeed. The situational routes are added when
    something on the file prompts them.
    """
    marked = set(consumer_marked or [])
    med = [it for it in (items or []) if is_medical(it, marked)]

    if not med:
        return {
            "has_medical": False,
            "item_count": 0,
            "items": [],
            "routes": [],
            "grant_reality": GRANT_REALITY,
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    detailed = []
    total = 0.0
    for it in med:
        amt = _money(it)
        if amt:
            total += amt
        detailed.append({
            "id": it.get("id") or it.get("item_id") or "",
            "furnisher": _furnisher(it),
            "amount": amt,
            "opened": str(it.get("opened") or it.get("date_opened") or ""),
            "why_we_think_medical": _detection_basis(it, marked),
            # The consumer can turn this off. Nothing downstream should treat
            # our guess as established.
            "confirm_with_consumer": True,
        })

    def route(key: str, prompted_by: str) -> dict:
        r = RELIEF_ROUTES[key]
        return {
            "route_key": key,
            "name": r["name"],
            "kind": r["kind"],
            "prompted_by": prompted_by,
            "generally_for": r["generally_for"],
            "why_it_matters": r["why_it_matters"],
            "documents_to_gather": r["documents_to_gather"],
            "verify_at": r.get("verify_at", ""),
            "cost": r.get("cost", ""),
            "note": r.get("note", ""),
            # Repeated per route, not once at the top: any surface can render
            # a single route alone and it must carry its own caveat.
            "is_eligibility_determination": False,
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    count = len(med)
    noun = "account" if count == 1 else "accounts"
    seen = f"{count} medical {noun} on this report"
    if total:
        seen += f", totalling ${total:,.0f}"

    routes = [
        route("itemized_bill", f"{seen}. This step applies to every medical "
                               f"balance and costs nothing."),
        route("charity_care", f"{seen}. Whether any provider involved is a "
                              f"non-profit is not on the credit report — ask "
                              f"them."),
    ]

    # Situational. A recent date of service is when the No Surprises Act and
    # retroactive Medicaid are most likely to still be reachable, but neither
    # is asserted to have a deadline here because the applicable windows vary.
    newest = max((d for it in med
                  if (d := _date(it, "opened", "date_opened")) is not None),
                 default=None)
    if newest is not None:
        months = (datetime.now(timezone.utc) - newest).days / 30.44
        if months <= 36:
            when = newest.strftime("%Y-%m-%d")
            routes.append(route(
                "no_surprises",
                f"The most recent medical account here dates from {when}. If "
                f"any of this care was an emergency, or was delivered by an "
                f"out-of-network provider at an in-network facility, federal "
                f"protections may apply to the bill itself."))
            routes.append(route(
                "medicaid_retroactive",
                f"The most recent medical account here dates from {when}. "
                f"Eligibility is judged on your circumstances at the date of "
                f"service, not today — which is why an old bill is still "
                f"worth asking about."))

    routes.append(route("provider_payment_plan",
                        f"{seen}. If a balance survives everything above, "
                        f"this is the way to structure it without paying for "
                        f"the privilege."))
    routes.append(route("sliding_scale",
                        "Ongoing care is what puts the next bill on the "
                        "report. This route is about that, not about the "
                        "balances already here."))
    routes.append(route("nonprofit_counseling",
                        f"{seen}, alongside other debts on this file."))

    return {
        "has_medical": True,
        "item_count": count,
        "total_balance": round(total, 2) if total else None,
        "items": detailed,
        "routes": routes,
        "grant_reality": GRANT_REALITY,
        "disclaimer": MEDICAL_DISCLAIMER,
        "sequence_note":
            "Order matters. Ask for the itemised bill and apply for financial "
            "assistance before you agree to pay anything or sign a plan — a "
            "balance you have already promised to pay is harder to have "
            "reduced. Disputing the tradeline and pursuing the bill itself "
            "are not alternatives; do both.",
    }


def summary_lines(analysis: dict) -> list[str]:
    """One line per route, for the review screen and the print packet."""
    if not analysis.get("has_medical"):
        return []
    out = [f"{analysis['item_count']} medical accounts identified"]
    out.extend(f"{r['name']} — {r['kind'].replace('_', ' ')}"
               for r in analysis.get("routes", []))
    return out
