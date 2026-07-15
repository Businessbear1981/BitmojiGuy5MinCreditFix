"""
PDF Renderer — generates sanitized PDF letters for Click2Mail dispatch.

Rules:
- No metadata identifying the tool (Author, Producer, Creator, Company)
- .25" safe area margins
- Clean, professional formatting
- Letter-size 8.5 x 11
"""

import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import black


# Branding patterns to scan for before output
_BRANDING_PATTERNS = [
    re.compile(r'AE[\s.-]*CC[\s.-]*\d+', re.IGNORECASE),
    re.compile(r'AE[\s.-]*Labs', re.IGNORECASE),
    re.compile(r'Arden\s*Edge', re.IGNORECASE),
    re.compile(r'BitmojiGuy', re.IGNORECASE),
    re.compile(r'CreditFix', re.IGNORECASE),
    re.compile(r'Credit\s*Tool', re.IGNORECASE),
    re.compile(r'AE-\d{8}-\w+'),
]


def _sanitize_text(text: str) -> str:
    """Scan text for branding leaks. Raise if found."""
    for pattern in _BRANDING_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            raise ValueError(f'SANITIZATION FAILURE: Text contains branding: {matches}')
    return text


def render_letter_pdf(letter_body: str, consumer_name: str = '', recipient_name: str = '') -> bytes:
    """
    Render a dispute letter as a sanitized PDF.

    Returns PDF bytes ready for Click2Mail upload or consumer download.
    """
    # Sanitize before rendering
    _sanitize_text(letter_body)

    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        title='',
        author='',
        subject='',
        creator='',
    )

    # Styles
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        'LetterBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=11,
        leading=15,
        spaceAfter=6,
        textColor=black,
    )
    heading_style = ParagraphStyle(
        'LetterHeading',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=11,
        leading=15,
        spaceAfter=4,
        spaceBefore=12,
        textColor=black,
    )
    small_style = ParagraphStyle(
        'LetterSmall',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=13,
        spaceAfter=3,
        textColor=black,
    )

    # Build flowables from letter body
    flowables = []
    lines = letter_body.split('\n')

    for line in lines:
        stripped = line.strip()

        if not stripped:
            flowables.append(Spacer(1, 6))
            continue

        # Section headers (all caps lines or lines starting with "SECTION")
        if (stripped.isupper() and len(stripped) > 5) or stripped.startswith('SECTION ') or stripped.startswith('4.'):
            # Escape HTML special chars for reportlab
            safe = stripped.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            flowables.append(Paragraph(safe, heading_style))
        elif stripped.startswith('  ') or stripped.startswith('- ') or stripped.startswith('  -'):
            safe = stripped.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            flowables.append(Paragraph(safe, small_style))
        else:
            safe = stripped.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            flowables.append(Paragraph(safe, body_style))

    doc.build(flowables)

    pdf_bytes = buf.getvalue()
    buf.close()

    return pdf_bytes


def render_letter_to_file(letter_body: str, filepath: str, consumer_name: str = '', recipient_name: str = ''):
    """Render and save to disk."""
    pdf_bytes = render_letter_pdf(letter_body, consumer_name, recipient_name)
    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)
    return filepath


def generate_sanitized_filename(recipient_short: str, consumer_lastname: str) -> str:
    """Generate neutral filename per spec: {YYYYMMDD}_{recipient_short}_{consumer_lastname}.pdf"""
    date_str = datetime.now().strftime('%Y%m%d')
    # Clean recipient name
    r = re.sub(r'[^a-zA-Z0-9]', '', recipient_short)[:20]
    c = re.sub(r'[^a-zA-Z0-9]', '', consumer_lastname)[:20]
    return f'{date_str}_{r}_{c}.pdf'


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import os
    import sys

    # Load sample letter
    samples_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'samples')
    letter_path = os.path.join(samples_dir, 'experian_letter.txt')

    if os.path.exists(letter_path):
        with open(letter_path, 'r') as f:
            letter_body = f.read()

        # Render PDF
        pdf_path = os.path.join(samples_dir, generate_sanitized_filename('Experian', 'Gilmore'))
        render_letter_to_file(letter_body, pdf_path, 'Sean Gilmore', 'Experian')
        print(f'PDF generated: {pdf_path}')
        print(f'Size: {os.path.getsize(pdf_path)} bytes')
    else:
        print(f'Sample letter not found at {letter_path}')
        print('Run letter_generator.py first to create the sample.')
