# 5 Minutes to Credit Wellness — Follow-Up Letter Engine
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# Generates 30/60/90-day follow-up letters.
# No circular imports — uses state_laws module directly.

from datetime import datetime

from api.state_laws import STATE_LAWS, build_state_law_block

BUREAUS = [
    {"name": "Equifax", "address": "P.O. Box 740256, Atlanta, GA 30374-0256"},
    {"name": "Experian", "address": "P.O. Box 4500, Allen, TX 75013"},
    {"name": "TransUnion", "address": "P.O. Box 2000, Chester, PA 19016"},
]

FOLLOWUP_TEMPLATES = {
    30: {
        "title": "30-Day Follow-Up — Failure to Respond",
        "body": """Dear {bureau},

On {original_date}, I submitted a formal dispute regarding the item(s) listed below. More than 30 days have passed and I have not received a response.

Original Dispute Reference: {confirmation}

Disputed Item(s):
{items}

Consumer: {name}

Under the Fair Credit Reporting Act Section 611(a)(1), you are required to conduct a reasonable reinvestigation and notify me of the results within 30 days. Your failure to respond is a violation of federal law.

I demand that you:
1. Immediately complete the reinvestigation
2. Provide written results within 5 business days
3. Delete any items you cannot verify per FCRA Section 611(a)(5)(A)

If I do not receive a satisfactory response within 15 days, I will file complaints with the CFPB, FTC, and my state Attorney General.

Under FCRA Section 616, I may be entitled to actual damages, statutory damages of $100 to $1,000, punitive damages, and attorney's fees.

{state_law}

Sincerely,
{name}
Date: {date}""",
    },
    60: {
        "title": "60-Day Escalation — Inadequate Response",
        "body": """Dear {bureau},

This is a follow-up to my original dispute ({confirmation}) submitted on {original_date} and my 30-day follow-up. Your response has been inadequate.

Disputed Item(s):
{items}

Consumer: {name}

Your investigation appears to have used an automated system (e-OSCAR) without genuine reinvestigation as required by FCRA Section 611(a)(1). See Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997).

Under FCRA Section 611(a)(6)(B)(iii), you must provide:
1. Description of the procedure used to determine accuracy
2. Business name, address, and phone of the furnisher contacted
3. Notice that I may add a statement of dispute

I now demand:
1. A genuine reinvestigation
2. Full method of verification details
3. Deletion of all unverifiable items
4. Updated copy of my credit report

I am preparing CFPB and state Attorney General complaints.

{state_law}

Sincerely,
{name}
Date: {date}""",
    },
    90: {
        "title": "90-Day Final Demand — Regulatory Action Notice",
        "body": """Dear {bureau},

This is my final communication regarding dispute {confirmation}, originally submitted on {original_date}. Despite two prior written demands, you have failed to conduct a lawful reinvestigation.

Disputed Item(s):
{items}

Consumer: {name}

NOTICE OF REGULATORY ACTION:

I am simultaneously filing complaints with:

1. CONSUMER FINANCIAL PROTECTION BUREAU (CFPB) at consumerfinance.gov/complaint
2. FEDERAL TRADE COMMISSION (FTC) at reportfraud.ftc.gov
3. STATE ATTORNEY GENERAL — {state_name}

LEGAL NOTICE:

Under FCRA Section 616 (willful noncompliance):
- Actual damages sustained
- Statutory damages of $100 to $1,000 per violation
- Punitive damages as the court may allow
- Attorney's fees and costs

All disputed items that remain unverified must be deleted immediately. This letter and all prior correspondence are preserved as evidence.

{state_law}

Sincerely,
{name}
Date: {date}""",
    },
}


def generate_followup_letters(profile: dict, day: int) -> list[dict]:
    """Generate follow-up letters for a specific day mark (30, 60, or 90)."""
    template = FOLLOWUP_TEMPLATES.get(day)
    if not template:
        return []

    date_str = datetime.utcnow().strftime("%B %d, %Y")
    original_date = profile.get("paid_at", profile.get("created_at", ""))
    if original_date:
        try:
            if isinstance(original_date, str):
                original_date = datetime.fromisoformat(original_date).strftime("%B %d, %Y")
            elif isinstance(original_date, datetime):
                original_date = original_date.strftime("%B %d, %Y")
        except (ValueError, TypeError):
            original_date = "a prior date"

    items = profile.get("dispute_items", [])
    items_text = []
    for item in items:
        if isinstance(item, dict):
            items_text.append(f"  - {item.get('text', str(item))}")
        else:
            items_text.append(f"  - {item}")
    items_fmt = "\n".join(items_text) if items_text else "  - See original dispute letter"

    state_code = profile.get("state", "")
    state_law = ""
    state_name = ""
    consumer_act = ""
    if state_code:
        law = STATE_LAWS.get(state_code)
        if law:
            state_name = law["name"]
            consumer_act = law["consumer_act"]
            state_law = build_state_law_block(state_code, "collections")

    letters = []
    for bureau in BUREAUS:
        body = template["body"].format(
            bureau=bureau["name"],
            confirmation=profile.get("confirmation", "N/A"),
            original_date=original_date,
            items=items_fmt,
            name=profile.get("name", "[YOUR NAME]"),
            date=date_str,
            state_law=state_law,
            state_name=state_name or "my state",
            consumer_act=consumer_act or "applicable state consumer protection laws",
        )
        letters.append({
            "bureau": bureau["name"],
            "bureau_address": bureau["address"],
            "type": f"follow_up_{day}",
            "type_label": template["title"],
            "variant": str(day),
            "title": template["title"],
            "body": body,
        })
    return letters
