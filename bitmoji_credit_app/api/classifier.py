# 5 Minutes to Credit Wellness — Dispute Classifier
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# Classifies extracted accounts into dispute boxes by type.
# Applies state statute-of-limitations logic to upgrade aged debts.
# Enforces the Gilmore dispute order for maximum legal impact.

from datetime import datetime

from api.state_laws import STATE_LAWS


# ═════════════════════════════════════════════════════════════════════════════
# DISPUTE BOX MAPPING — every negative mark type → dispute category
# ═════════════════════════════════════════════════════════════════════════════

MARK_TO_DISPUTE_BOX = {
    "collection":    "collections",
    "charge_off":    "collections",
    "repossession":  "collections",
    "foreclosure":   "collections",
    "judgment":      "collections",
    "late_payment":  "late_payments",
    "bankruptcy":    "unknown_accounts",
    "settled":       "aged_debt",
    "negative_item": "unknown_accounts",
}

DISPUTE_BOX_LABELS = {
    "collections":     "Collection Account",
    "late_payments":   "Late Payment",
    "wrong_addresses": "Incorrect Address",
    "unknown_accounts": "Unknown / Unrecognized Account",
    "aged_debt":       "Aged / Time-Barred Debt",
}

# Gilmore dispute order — enforced sequence for maximum impact
GILMORE_ORDER = [
    "wrong_addresses",
    "unknown_accounts",
    "collections",
    "aged_debt",
    "late_payments",
    "mov_demand",
]

GILMORE_LABELS = {
    "wrong_addresses":  "Phase 1: Personal Info",
    "unknown_accounts": "Phase 2: Inquiries & Unknown Accounts",
    "collections":      "Phase 3: Collections",
    "aged_debt":        "Phase 4: Charge-Offs & Aged Debt",
    "late_payments":    "Phase 5: Late Payments",
    "mov_demand":       "Follow-Up: Method of Verification",
}


def _parse_account_date(date_str: str) -> datetime | None:
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def classify_dispute_items(accounts: list[dict], state_code: str = "") -> list[dict]:
    """Classify each account into a dispute box. Applies state SOL logic."""
    state_sol_years = None
    if state_code and state_code in STATE_LAWS:
        state_sol_years = STATE_LAWS[state_code].get("sol_written")

    for acct in accounts:
        acct["dispute"] = True
        box = MARK_TO_DISPUTE_BOX.get(acct.get("type", ""), "unknown_accounts")

        if state_sol_years and acct.get("date"):
            acct_date = _parse_account_date(acct["date"])
            if acct_date:
                age_years = (datetime.utcnow() - acct_date).days / 365.25
                if age_years >= state_sol_years:
                    box = "aged_debt"
                    acct["sol_expired"] = True
                    acct["sol_years"] = state_sol_years
                    acct["account_age_years"] = round(age_years, 1)

        acct["dispute_box"] = box
        acct["dispute_label"] = DISPUTE_BOX_LABELS.get(box, "Unknown")

    return accounts


def sort_by_gilmore_order(dispute_types: list[str]) -> list[str]:
    """Sort dispute types by the Gilmore dispute order."""
    return sorted(dispute_types, key=lambda t: GILMORE_ORDER.index(t) if t in GILMORE_ORDER else 99)


def group_items_by_box(items: list[dict]) -> dict:
    """Group classified dispute items into boxes for frontend display."""
    boxes = {}
    for item in items:
        box = item.get("dispute_box", "unknown_accounts")
        if box not in boxes:
            boxes[box] = {"label": DISPUTE_BOX_LABELS.get(box, "Unknown"), "items": []}
        boxes[box]["items"].append(item)
    return boxes
