import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "apikey")
SMTP_PASS = os.environ.get("SMTP_PASS", SENDGRID_API_KEY)
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@ardanedgecapital.com")


def send_letters_email(to_email: str, client_name: str, session_id: str, pdf_path: Path) -> bool:
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

    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
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
    except Exception as e:
        print(f"Email send failed: {e}")
        return False
