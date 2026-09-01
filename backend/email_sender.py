import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "apikey")
SMTP_PASS = os.environ.get("SMTP_PASS", SENDGRID_API_KEY)
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@ardanedgecapital.com")


def send_letters_email(to_email: str, client_name: str, session_id: str, pdf_bytes: bytes) -> bool:
    """Send the dispute letters PDF to the user via email."""
    if not SMTP_PASS:
        print("WARN: No SMTP credentials configured, skipping email")
        return False

    msg = MIMEMultipart()
    msg["From"] = f"AE 5-Min Credit Fix <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = f"Your Credit Dispute Letters — {session_id[:8]}"

    body = f"""Hi {client_name},

Your FCRA dispute letters are attached as a PDF. Here's what to do next:

1. Print each letter on white paper
2. Sign each letter in blue ink
3. Include copies of your government-issued ID and one proof of address
4. Mail each letter via USPS Certified Mail with Return Receipt Requested
5. Keep your green receipt cards and tracking numbers

The bureaus have 30 days from receipt to investigate and respond.

Mailing Addresses:
  Experian — P.O. Box 4500, Allen, TX 75013
  Equifax — P.O. Box 740241, Atlanta, GA 30374-0241
  TransUnion — P.O. Box 2000, Chester, PA 19016-2000

Your session ID is {session_id} — save this to re-download your letters anytime.

— AE 5-Min Credit Fix | Arden Edge Labs
"""
    msg.attach(MIMEText(body, "plain"))

    if pdf_bytes:
        part = MIMEBase("application", "pdf")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="AE_CreditFix_Letters_{session_id}.pdf"',
        )
        msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:  # noqa: BLE001 - boundary must degrade, not crash; type logged
        # Log the error type only — the exception could echo message content
        print(f"Email send failed: {type(e).__name__}")
        return False


def send_watcher_reminder(to_email: str, client_name: str, session_id: str,
                          milestone: dict, frontend_url: str) -> bool:
    """
    A milestone reminder. Plain text, no attachment, no marketing.

    Written to state what has become *available*, never what the consumer is
    owed. "Day 30 has passed, the method-of-verification round can be sent"
    is a fact about the calendar. "The bureau failed and you're owed a
    deletion" would be a prediction, and this platform does not make those.
    """
    if not SMTP_PASS:
        print("WARN: No SMTP credentials configured, skipping watcher reminder")
        return False

    day = milestone.get("day", 0)
    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = f"Day {day}: {milestone.get('title', 'Milestone reached')}"

    body = f"""{client_name},

Day {day} of your dispute has passed.

{milestone.get('title', '')}
{milestone.get('statute', '')}

{milestone.get('body', '')}

{milestone.get('on_reach', '')}

Open your tracker to generate them:
{frontend_url}/watcher

A note on what this email means: it is a calendar reminder, not a result. We
track the dates, not the bureau's decision. We do not know what came back in
your mail, whether anything was removed, or whether you have a claim worth
bringing — that last question is one for an attorney.

If nothing arrived from the bureau at all, that absence is itself worth
raising in the next round, and the letter is written to do that.

Session ID: {session_id}

— AE 5-Min Credit Fix | Arden Edge Labs
You are receiving this because you turned on the Watcher. Reply STOP or open
your tracker to cancel; cancelling also deletes your case.
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:  # noqa: BLE001 - boundary must degrade, not crash; type logged
        print(f"Watcher reminder failed: {type(e).__name__}")
        return False
