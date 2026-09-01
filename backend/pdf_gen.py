from datetime import datetime
from io import BytesIO

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

import signature as sig


def build_letter_pdf(session_id: str, client: dict, letters: list,
                     signature_record: dict | None = None) -> bytes:
    """
    Generate the dispute-letter packet PDF fully in memory.
    Returns raw PDF bytes — never written to disk (contains PII).
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "LetterHeader",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "LetterBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "LetterSubject",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=12,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "CoverInfo",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor="grey",
        alignment=TA_CENTER,
    ))

    story = []

    # --- Cover page ---
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("AE 5-Min Credit Fix", styles["CoverTitle"]))
    story.append(Paragraph("Dispute Letter Packet", styles["CoverTitle"]))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"Prepared for: <b>{_esc(client['name'])}</b>", styles["CoverInfo"]))
    story.append(Paragraph(f"Address: {_esc(client['address'])}", styles["CoverInfo"]))
    story.append(Paragraph(f"Phone: {_esc(client['phone'])} | Email: {_esc(client['email'])}", styles["CoverInfo"]))
    story.append(Paragraph(f"DOB: {_esc(client['dob'])} | SSN last 4: {_esc(client['ssn_last4'])}", styles["CoverInfo"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}", styles["CoverInfo"]))
    story.append(Paragraph(f"Letters included: {len(letters)}", styles["CoverInfo"]))
    story.append(Spacer(1, 1 * inch))
    if signature_record:
        story.append(Paragraph(
            "This packet contains FCRA-compliant dispute letters referencing "
            "15 U.S.C. §1681g (§609), §1681i (§611), and §1681s-2 (§623). "
            "Each letter is already signed — print and mail via USPS Certified "
            "Mail with Return Receipt Requested. Include a copy of your photo ID "
            "and proof of address with each one.",
            styles["CoverInfo"],
        ))
    else:
        story.append(Paragraph(
            "This packet contains FCRA-compliant dispute letters referencing "
            "15 U.S.C. §1681g (§609), §1681i (§611), and §1681s-2 (§623). "
            "Print each letter, sign in blue ink, and mail via USPS Certified Mail "
            "with Return Receipt Requested.",
            styles["CoverInfo"],
        ))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("© Arden Edge Labs — AE 5-Min Credit Fix", styles["Footer"]))
    story.append(PageBreak())

    # --- Individual letters ---
    for i, ltr in enumerate(letters):
        text = ltr.get("text", "")
        paragraphs = text.split("\n")

        for j, line in enumerate(paragraphs):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            if j < 6:
                story.append(Paragraph(_esc(line), styles["LetterHeader"]))
            elif line.startswith("Re:"):
                story.append(Paragraph(_esc(line), styles["LetterSubject"]))
            elif line.startswith(("•", "-")):
                story.append(Paragraph(f"&bull; {_esc(line.lstrip('•- '))}", styles["LetterBody"]))
            else:
                story.append(Paragraph(_esc(line), styles["LetterBody"]))

        # Signature block — the consumer's captured mark when they signed in
        # the app, otherwise a ruled line for a wet signature.
        story.append(Spacer(1, 0.35 * inch))
        stream = sig.signature_bytes(signature_record)
        if stream is not None:
            try:
                story.append(RLImage(stream, width=2.4 * inch, height=0.75 * inch,
                                     kind="proportional"))
            except Exception:  # noqa: BLE001 - boundary must degrade, not crash; type logged
                story.append(Paragraph("_" * 40, styles["LetterBody"]))
            story.append(Paragraph(_esc(client["name"]), styles["LetterBody"]))
            signed_on = (signature_record.get("signed_at") or "")[:10]
            story.append(Paragraph(f"Date: {_esc(signed_on)}", styles["LetterBody"]))
            story.append(Spacer(1, 4))
            story.append(Paragraph(
                f"<font size=7 color='#555555'>{_esc(sig.attestation_line(signature_record))}</font>",
                styles["LetterBody"],
            ))
        else:
            story.append(Paragraph("_" * 40, styles["LetterBody"]))
            story.append(Paragraph(f"{_esc(client['name'])} (sign above)", styles["LetterBody"]))
            story.append(Paragraph("Date: _______________", styles["LetterBody"]))

        if i < len(letters) - 1:
            story.append(PageBreak())

    doc.build(story)
    return buffer.getvalue()


def _esc(text: str) -> str:
    """Escape XML special chars for ReportLab Paragraph."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
