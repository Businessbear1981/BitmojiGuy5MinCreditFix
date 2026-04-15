# BitmojiGuy 5-Min Credit Fix — Follow-Up Engine
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001

from datetime import datetime
import database

# ���════════════════════════════��═══════════════════════════════════════════════
# FOLLOW-UP LETTER TEMPLATES — 30/60/90 day escalation
# ═════════════════════════════════════════════════════════════════════════════

BUREAUS = [
    {'name': 'Equifax', 'address': 'P.O. Box 740256, Atlanta, GA 30374-0256'},
    {'name': 'Experian', 'address': 'P.O. Box 4500, Allen, TX 75013'},
    {'name': 'TransUnion', 'address': 'P.O. Box 2000, Chester, PA 19016'},
]

FOLLOWUP_TEMPLATES = {
    30: {
        'title': '30-Day Follow-Up — Failure to Respond',
        'body': """Dear {bureau},

On {original_date}, I submitted a formal dispute regarding the item(s) listed below. More than 30 days have passed and I have not received a response.

Original Dispute Reference: {confirmation}

Disputed Item(s):
{items}

Consumer: {name}

Under the Fair Credit Reporting Act Section 611(a)(1), you are required to conduct a reasonable reinvestigation and notify me of the results within 30 days of receiving my dispute. Your failure to respond within this timeframe is a violation of federal law.

I demand that you:
1. Immediately complete the reinvestigation of the disputed items
2. Provide me with written results within 5 business days of this letter
3. Delete any items you cannot verify, as required by FCRA Section 611(a)(5)(A)

If I do not receive a satisfactory response within 15 days of this letter, I will file complaints with:
- The Consumer Financial Protection Bureau (CFPB)
- The Federal Trade Commission (FTC)
- My state Attorney General's office

Under FCRA Section 616, I may be entitled to actual damages, statutory damages of $100 to $1,000, punitive damages, and attorney's fees for your willful noncompliance.

{state_law}

Sincerely,
{name}
Date: {date}""",
    },
    60: {
        'title': '60-Day Follow-Up — Partial Compliance / Inadequate Response',
        'body': """Dear {bureau},

This letter is a follow-up to my original dispute ({confirmation}) submitted on {original_date} and my 30-day follow-up. Your response, if any, has been inadequate and does not satisfy the requirements of the FCRA.

Disputed Item(s):
{items}

Consumer: {name}

Your investigation appears to have been conducted using an automated system (e-OSCAR) without a genuine reinvestigation as required by FCRA Section 611(a)(1). Courts have consistently held that a "parroting" of furnisher information without independent verification does not constitute a reasonable reinvestigation. See Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997).

Additionally, under FCRA Section 611(a)(6)(B)(iii), you were required to provide me with:
1. A description of the procedure used to determine accuracy
2. The business name, address, and phone number of the furnisher contacted
3. A notice that I may add a statement of dispute to my file

I have not received adequate information on any of these points.

I now demand:
1. A genuine reinvestigation — not an automated rubber stamp
2. Full method of verification details as required by law
3. Deletion of all items that cannot be properly verified
4. An updated copy of my credit report

I am preparing formal complaints to the CFPB and my state Attorney General. This letter constitutes your final opportunity to resolve this matter before escalation.

{state_law}

Sincerely,
{name}
Date: {date}""",
    },
    90: {
        'title': '90-Day Escalation — CFPB and Attorney General Notice',
        'body': """Dear {bureau},

This is my final communication regarding dispute {confirmation}, originally submitted on {original_date}. Despite two prior written demands (30-day and 60-day follow-ups), you have failed to conduct a lawful reinvestigation or provide adequate verification of the disputed items.

Disputed Item(s):
{items}

Consumer: {name}

NOTICE OF REGULATORY ACTION:

I am simultaneously filing the following complaints:

1. CONSUMER FINANCIAL PROTECTION BUREAU (CFPB)
   Complaint filed at consumerfinance.gov/complaint
   Regarding your failure to comply with FCRA Sections 611(a)(1), 611(a)(5)(A), and 611(a)(6)(B)(iii)

2. FEDERAL TRADE COMMISSION (FTC)
   Complaint filed at reportfraud.ftc.gov
   Regarding willful noncompliance with the Fair Credit Reporting Act

3. STATE ATTORNEY GENERAL — {state_name}
   Complaint filed regarding violations of both federal law and {consumer_act}

LEGAL NOTICE:

Under FCRA Section 616 (Civil liability for willful noncompliance), I may pursue:
- Actual damages sustained
- Statutory damages of $100 to $1,000 per violation
- Punitive damages as the court may allow
- Costs of the action and reasonable attorney's fees

Under FCRA Section 617 (Civil liability for negligent noncompliance), I may also pursue actual damages and attorney's fees.

Your continued failure to delete unverifiable information from my credit report constitutes ongoing harm. All disputed items that remain unverified must be deleted immediately.

This letter and all prior correspondence are being preserved as evidence.

{state_law}

Sincerely,
{name}
Date: {date}""",
    },
}


def generate_followup_letters(profile, day):
    """Generate follow-up letters for a specific day mark (30, 60, or 90)."""
    template = FOLLOWUP_TEMPLATES.get(day)
    if not template:
        return []

    date_str = datetime.utcnow().strftime('%B %d, %Y')
    original_date = profile.get('paid_at', profile.get('created_at', ''))
    if original_date:
        try:
            original_date = datetime.fromisoformat(original_date).strftime('%B %d, %Y')
        except (ValueError, TypeError):
            original_date = 'a prior date'

    # Build items text from all dispute items
    items = profile.get('dispute_items', [])
    items_text = []
    for item in items:
        if isinstance(item, dict):
            items_text.append(f"  - {item.get('text', str(item))}")
        else:
            items_text.append(f"  - {item}")
    items_fmt = '\n'.join(items_text) if items_text else '  - See original dispute letter'

    # State law block
    state_code = profile.get('state', '')
    state_law = ''
    state_name = ''
    consumer_act = ''
    if state_code:
        from app import STATE_LAWS, build_state_law_block
        law = STATE_LAWS.get(state_code)
        if law:
            state_name = law['name']
            consumer_act = law['consumer_act']
            state_law = build_state_law_block(state_code, 'collections')

    letters = []
    for bureau in BUREAUS:
        body = template['body'].format(
            bureau=bureau['name'],
            confirmation=profile.get('confirmation', 'N/A'),
            original_date=original_date,
            items=items_fmt,
            name=profile.get('name', '[YOUR NAME]'),
            date=date_str,
            state_law=state_law,
            state_name=state_name or 'my state',
            consumer_act=consumer_act or 'applicable state consumer protection laws',
        )
        letters.append({
            'bureau': bureau['name'],
            'bureau_address': bureau['address'],
            'type': f'follow_up_{day}',
            'type_label': template['title'],
            'variant': str(day),
            'title': template['title'],
            'body': body,
        })
    return letters


def check_and_send_followups():
    """Main follow-up job — check all 3 tiers and generate/email letters."""
    total_sent = 0
    for day in [30, 60, 90]:
        clients = database.get_due_followups(day)
        for profile in clients:
            letters = generate_followup_letters(profile, day)
            if letters:
                # Store follow-up letters in profile
                if 'follow_up_letters' not in profile:
                    profile['follow_up_letters'] = {}
                profile['follow_up_letters'][str(day)] = letters

                # Update profile in DB
                history_entry = {
                    'date': datetime.utcnow().isoformat(),
                    'type': f'follow_up_{day}',
                    'letter_count': len(letters),
                }
                if 'follow_up_history' not in profile:
                    profile['follow_up_history'] = []
                profile['follow_up_history'].append(history_entry)

                database.save_client(profile)
                database.mark_followup_sent(profile['id'], day)

                # Send email notification
                try:
                    from app import send_confirmation_email
                    subject_map = {
                        30: 'Action Required: Bureau has not responded to your dispute',
                        60: 'Escalation Notice: Your dispute requires follow-up',
                        90: 'Final Notice: Filing regulatory complaints on your behalf',
                    }
                    items_flat = [i.get('text', str(i)) if isinstance(i, dict) else str(i)
                                  for i in profile.get('dispute_items', [])]
                    send_confirmation_email(
                        profile.get('email', ''),
                        profile.get('name', ''),
                        profile.get('confirmation', ''),
                        [f"[{day}-DAY FOLLOW-UP] {subject_map.get(day, '')}"] + items_flat
                    )
                except Exception as e:
                    print(f"[FOLLOWUP EMAIL ERROR] {e}")

                total_sent += 1
                print(f"[FOLLOWUP] {day}-day letters generated for {profile.get('confirmation', 'unknown')}")

    if total_sent:
        print(f"[FOLLOWUP] Total follow-ups processed: {total_sent}")
    return total_sent
