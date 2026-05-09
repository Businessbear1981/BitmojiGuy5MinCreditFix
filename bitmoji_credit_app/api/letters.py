# 5 Minutes to Credit Wellness — Dispute Letter Generator
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# 18 letter templates: 3 variants x 6 dispute types (including MOV).
# Each letter sent to all 3 bureaus = up to 54 letters per client.

from datetime import datetime

from api.state_laws import build_state_law_block
from api.classifier import GILMORE_ORDER
from api.parser import DISPUTE_PATTERNS

BUREAUS = [
    {"name": "Equifax", "address": "P.O. Box 740256, Atlanta, GA 30374-0256"},
    {"name": "Experian", "address": "P.O. Box 4500, Allen, TX 75013"},
    {"name": "TransUnion", "address": "P.O. Box 2000, Chester, PA 19016"},
]

BUREAU_ADDRESSES = {
    "Equifax": {"name": "Equifax Information Services", "address": "PO Box 740256", "city": "Atlanta", "state": "GA", "zip": "30374"},
    "TransUnion": {"name": "TransUnion Consumer Solutions", "address": "PO Box 2000", "city": "Chester", "state": "PA", "zip": "19016"},
    "Experian": {"name": "Experian Disputes", "address": "PO Box 4500", "city": "Allen", "state": "TX", "zip": "75013"},
}

# All letter templates are identical to the originals in app.py.
# Abbreviated here for the key structure — full bodies carried over from production.

LETTER_TEMPLATES = {
    "collections": [
        {"variant": "A", "title": "Debt Validation Demand",
         "body": """Dear {bureau},

I am writing to formally dispute the following collection account on my credit report under the FDCPA Section 809(b) and FCRA Section 611.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I do not recognize this debt. Please provide:
1. Original creditor name and address
2. Original account number
3. Amount at time of default
4. Complete payment history from original creditor
5. Copy of original signed agreement bearing my signature

You have 30 days to investigate under the FCRA. If unverifiable, delete this account permanently.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "B", "title": "Collection Statute of Limitations Challenge",
         "body": """Dear {bureau},

I dispute the collection account below under the FCRA. I believe it exceeds the statute of limitations for reporting.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

Under FCRA Section 605, negative information must be removed after 7 years from the date of first delinquency. I request:
1. Verify the date of first delinquency with the original creditor
2. Confirm the account has not been re-aged
3. Provide documentation proving it is within the legal reporting window
4. Remove immediately if verification cannot be completed in 30 days

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "C", "title": "Cease Collection and Remove",
         "body": """Dear {bureau},

This is a formal dispute and demand for removal of the following collection account(s).

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I dispute this debt in its entirety. Under FCRA Section 611(a)(5)(A), if unverifiable, you must delete it. I request:
1. Immediate investigation
2. Deletion if the furnisher cannot verify in 30 days
3. Written confirmation of results
4. Updated credit report showing deletion

Failure to respond within 30 days will result in a CFPB complaint.

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
    "late_payments": [
        {"variant": "A", "title": "Goodwill Late Payment Removal",
         "body": """Dear {bureau},

I am requesting a goodwill adjustment for the late payment(s) reported on my account.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I have been a responsible borrower. This late payment does not reflect my usual behavior. My account is now current and in good standing. I respectfully request removal as a goodwill gesture.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "B", "title": "Late Payment Accuracy Dispute",
         "body": """Dear {bureau},

Under FCRA Section 611, I formally dispute the late payment(s) below as inaccurate.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I dispute accuracy because my records show payment was made on time. I request:
1. Contact the furnisher to verify exact date payment was received
2. Provide proof of the exact posting date
3. Remove the late notation if it cannot be verified
4. Written results within 30 days

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "C", "title": "Late Payment Dispute — Accommodation Period",
         "body": """Dear {bureau},

I dispute the late payment(s) below, reported during a hardship accommodation with the creditor.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

Under the CARES Act and FCRA Section 623(a)(1)(F), if a consumer has a payment accommodation, the account must be reported as current. I request correction to reflect "current" or "paid as agreed."

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
    "wrong_addresses": [
        {"variant": "A", "title": "Incorrect Address — Possible Fraud",
         "body": """Dear {bureau},

I dispute incorrect address information on my credit report. This may indicate identity fraud or mixed files.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

These addresses have never been associated with me. Under FCRA Section 611, you must maintain accurate consumer information. I request immediate removal and written confirmation.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "B", "title": "Address Correction — Mixed File",
         "body": """Dear {bureau},

I dispute inaccurate address information. I believe my file contains info belonging to another consumer. Mixed files violate FCRA Section 607(b).

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I request removal of all incorrect addresses, review of associated tradelines, and written confirmation.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "C", "title": "Address Correction Request",
         "body": """Dear {bureau},

I request correction of address information on my credit report. The following addresses are inaccurate.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I have never resided at the listed addresses. Please remove all inaccurate entries and send written confirmation within 30 days.

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
    "unknown_accounts": [
        {"variant": "A", "title": "Unknown Account — Potential Identity Theft",
         "body": """Dear {bureau},

I dispute the following account(s) I do not recognize. I may be a victim of identity theft. Under FCRA Section 605B, I request blocking of fraudulent information.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I request immediate investigation, removal of fraudulent accounts, and written confirmation within 30 days.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "B", "title": "Unknown Account Verification Demand",
         "body": """Dear {bureau},

Under FCRA Section 611, I formally dispute the following accounts. These are not mine.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I demand verification of the original application bearing my signature. If you cannot verify within 30 days, delete per FCRA Section 611(a)(5)(A).

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "C", "title": "Unauthorized Account / Inquiry Dispute",
         "body": """Dear {bureau},

I dispute the following unauthorized accounts and/or hard inquiries made without my permission. This violates FCRA Section 604.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I request removal of all unauthorized inquiries and accounts, and written confirmation within 30 days.

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
    "aged_debt": [
        {"variant": "A", "title": "Time-Barred Debt Removal Demand",
         "body": """Dear {bureau},

I dispute the following account(s) that have exceeded the maximum FCRA reporting period.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

Under FCRA Section 605(a), most negative information must be removed after 7 years. If unverifiable, it must be deleted.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "B", "title": "Aged Debt — Re-Aging Violation",
         "body": """Dear {bureau},

I dispute the following account(s) which have been illegally re-aged. FCRA Section 605(c) prohibits re-aging.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I demand documentation of the original delinquency date and immediate correction or removal. Re-aging is a federal violation.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "C", "title": "Obsolete Information Removal",
         "body": """Dear {bureau},

I dispute outdated information that should have been removed per FCRA Section 605.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I request verification of original delinquency date, immediate removal if past the reporting period, and written notification within 30 days.

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
    "mov_demand": [
        {"variant": "A", "title": "Method of Verification Demand — Initial",
         "body": """Dear {bureau},

You responded to my dispute (Ref: {confirmation}) claiming verification but failed to provide the method of verification as required by FCRA Section 611(a)(6)(B)(iii).

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I demand the specific method used to verify, furnisher contact information, and all documentation reviewed. Your failure violates the FCRA.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "B", "title": "MOV Demand — Procedural Challenge",
         "body": """Dear {bureau},

Your verification of dispute {confirmation} appears to have been automated (e-OSCAR) without genuine reinvestigation. See Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997).

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I demand full method of verification within 15 days. If you cannot substantiate, the items must be deleted per FCRA Section 611(a)(5)(A).

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {"variant": "C", "title": "MOV Demand — Pre-Litigation Final Notice",
         "body": """Dear {bureau},

This is my final demand for method of verification regarding dispute {confirmation}. You have 15 days to provide complete documentation.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

NOTICE OF INTENT TO PURSUE LEGAL REMEDIES:
If not provided within 15 days, I will file CFPB and state AG complaints and pursue FCRA Section 616 damages ($100-$1,000 per violation plus punitive damages and attorney's fees).

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
}

# Display labels for dispute types
DISPUTE_TYPE_LABELS = {
    "collections": "Collection Account",
    "late_payments": "Late Payment",
    "wrong_addresses": "Incorrect Address",
    "unknown_accounts": "Unknown / Unrecognized Account",
    "aged_debt": "Aged / Time-Barred Debt",
    "mov_demand": "Method of Verification Demand",
}


def generate_letters(dispute_types: list[str], items_by_type: dict, client_data: dict) -> list[dict]:
    """
    Generate dispute letters. ONE letter per dispute type per bureau.

    No variant stacking — picks the single strongest template per type.
    This avoids the bureau pattern-match for credit-repair-organization spam.
    """
    letters = []
    date_str = datetime.utcnow().strftime("%B %d, %Y")
    state_code = client_data.get("state", "")
    ordered_types = sorted(dispute_types, key=lambda t: GILMORE_ORDER.index(t) if t in GILMORE_ORDER else 99)

    for dtype in ordered_types:
        templates = LETTER_TEMPLATES.get(dtype, [])
        if not templates:
            continue
        # One letter per type per bureau — use the first (strongest) template only
        tmpl = templates[0]
        items_list = items_by_type.get(dtype, [])
        if isinstance(items_list, dict):
            items_list = items_list.get("items", [])
        items_fmt = "\n".join(f"  - {i}" for i in items_list) if items_list else "  - See attached documentation"
        state_law = build_state_law_block(state_code, dtype)

        for bureau in BUREAUS:
            letters.append({
                "bureau": bureau["name"],
                "bureau_address": bureau["address"],
                "type": dtype,
                "type_label": DISPUTE_TYPE_LABELS.get(dtype, dtype),
                "variant": tmpl["variant"],
                "title": tmpl["title"],
                "body": tmpl["body"].format(
                    bureau=bureau["name"],
                    items=items_fmt,
                    name=client_data.get("name", "[YOUR NAME]"),
                    confirmation=client_data.get("confirmation", "N/A"),
                    date=date_str,
                    state_law=state_law,
                ),
            })
    return letters
