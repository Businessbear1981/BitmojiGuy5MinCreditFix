# 5 Minutes to Credit Wellness — Credit Report Parser
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# Parses uploaded credit reports (PDF, TXT, CSV, DOCX, HTML, images).
# Extracts structured account data and dispute-eligible items.
# Supports AnnualCreditReport.com PDFs from all 3 bureaus.

import os
import re
import tempfile

import pdfplumber
from PIL import Image
from docx import Document as DocxDocument
from bs4 import BeautifulSoup

# Tesseract — use env var, fall back to system PATH
TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "")
if TESSERACT_CMD:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
else:
    try:
        import pytesseract
    except ImportError:
        pytesseract = None


# ═════════════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION — by file type
# ═════════════════════════════════════════════════════════════════════════════

def extract_text_from_pdf(filepath: str) -> str:
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages[:30]:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"[PDF ERROR] {e}")
    return text


def extract_text_from_image(filepath: str) -> str:
    if not pytesseract:
        return ""
    try:
        img = Image.open(filepath)
        return pytesseract.image_to_string(img)
    except Exception as e:
        print(f"[OCR ERROR] {e}")
        return ""


def extract_text_from_docx(filepath: str) -> str:
    try:
        doc = DocxDocument(filepath)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        print(f"[DOCX ERROR] {e}")
        return ""


def extract_text_from_html(filepath: str) -> str:
    try:
        with open(filepath, "r", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"[HTML ERROR] {e}")
        return ""


def extract_text_from_file(filepath: str, filename: str) -> tuple[str, bool]:
    """Extract text from a file. Returns (text, ocr_failed)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        return extract_text_from_pdf(filepath), False
    elif ext in ("txt", "csv"):
        try:
            with open(filepath, "r", errors="ignore") as f:
                return f.read(), False
        except Exception:
            return "", False
    elif ext in ("png", "jpg", "jpeg"):
        text = extract_text_from_image(filepath)
        return text, not text.strip()
    elif ext == "docx":
        return extract_text_from_docx(filepath), False
    elif ext in ("html", "htm"):
        return extract_text_from_html(filepath), False
    return "", False


# ═════════════════════════════════════════════════════════════════════════════
# DISPUTE PATTERN DETECTION — regex-based scanner
# ═════════════════════════════════════════════════════════════════════════════

DISPUTE_PATTERNS = {
    "collections": {
        "label": "Collection Account",
        "patterns": [
            r"(?i)collect(?:ion|ions)\s+(?:account|agency|balance)",
            r"(?i)(?:placed|sent|sold)\s+(?:for|to)\s+collect",
            r"(?i)charged?\s*off.*collect",
            r"(?i)(?:portfolio|midland|lvnv|encore|cavalry|ic system)",
        ],
        "extract": r"(?i)((?:collection|collect\w+).{0,80}(?:\$[\d,.]+|\d{4,}))",
    },
    "late_payments": {
        "label": "Late Payment",
        "patterns": [
            r"(?i)(?:30|60|90|120)\s*days?\s*(?:late|past\s*due|delinq)",
            r"(?i)late\s+payment",
            r"(?i)past\s+due\s+(?:amount|balance)",
            r"(?i)delinquen(?:t|cy)",
        ],
        "extract": r"(?i)((?:late|past due|delinq)\w*.{0,80}(?:\$[\d,.]+|\d{2}/\d{2,4}))",
    },
    "wrong_addresses": {
        "label": "Incorrect Address",
        "patterns": [
            r"(?i)address(?:es)?\s+(?:reported|on file|listed)",
            r"(?i)(?:previous|former|old|prior)\s+address",
            r"(?i)(?:po box|p\.o\.\s*box)\s*\d+",
        ],
        "extract": r"(?i)((?:address|addr).{0,120})",
    },
    "unknown_accounts": {
        "label": "Unknown / Unrecognized Account",
        "patterns": [
            r"(?i)(?:authorized\s+user|au\s+account)",
            r"(?i)inquir(?:y|ies)",
            r"(?i)(?:hard|soft)\s+(?:pull|inquiry)",
            r"(?i)account\s+(?:number|#|no)[\s.:]*\w{4,}",
        ],
        "extract": r"(?i)((?:account|acct)[\s#.:]*\w*.{0,80})",
    },
    "aged_debt": {
        "label": "Aged / Time-Barred Debt",
        "patterns": [
            r"(?i)(?:date\s+)?open(?:ed)?[\s:]+\d{1,2}/\d{2,4}",
            r"(?i)(?:original|first)\s+delinquency",
            r"(?i)statute\s+of\s+limitation",
            r"(?i)charge[\s-]*off\s+(?:date|since)",
        ],
        "extract": r"(?i)((?:charge.?off|delinquen|open(?:ed)?).{0,100}(?:\d{1,2}/\d{2,4}|\$[\d,.]+))",
    },
}


def parse_text_for_disputes(text: str) -> dict:
    """Scan text for dispute-eligible patterns. Returns {type: {label, items}}."""
    results = {}
    for dtype, cfg in DISPUTE_PATTERNS.items():
        if any(re.search(p, text) for p in cfg["patterns"]):
            hits = [
                re.sub(r"\s+", " ", m.strip())[:120]
                for m in re.findall(cfg["extract"], text)[:5]
                if len(m.strip()) > 15
            ]
            if not hits:
                hits = [f"{cfg['label']} detected in report"]
            results[dtype] = {"label": cfg["label"], "items": hits}
    return results


# ═════════════════════════════════════════════════════════════════════════════
# STRUCTURED ACCOUNT EXTRACTION — creditor + account number + marks
# ═════════════════════════════════════════════════════════════════════════════

KNOWN_CREDITORS = [
    "CAPITAL ONE", "CHASE", "JPMORGAN", "BANK OF AMERICA", "WELLS FARGO",
    "CITIBANK", "CITI", "DISCOVER", "AMERICAN EXPRESS", "AMEX", "SYNCHRONY",
    "BARCLAYS", "US BANK", "PNC", "TD BANK", "ALLY", "NAVIENT", "SALLIE MAE",
    "PORTFOLIO RECOVERY", "MIDLAND CREDIT", "LVNV FUNDING", "ENCORE CAPITAL",
    "CAVALRY", "IC SYSTEM", "CONVERGENT", "TRANSWORLD", "ERC", "ENHANCED RECOVERY",
    "UNIFIN", "AFNI", "CREDIT ACCEPTANCE", "WESTLAKE", "SANTANDER",
    "REGIONAL ACCEPTANCE", "SPRINGLEAF", "ONEMAIN", "LENDING CLUB", "PROSPER",
    "UPSTART", "SOFI", "AVANT", "BEST BUY", "TARGET", "WALMART", "AMAZON",
    "PAYPAL", "KLARNA", "AFFIRM", "AFTERPAY", "CARE CREDIT",
]

NEGATIVE_MARKS = {
    "collection": r"(?i)collect(?:ion|ions|ed)",
    "charge_off": r"(?i)charge[\s-]*off",
    "late_payment": r"(?i)(?:30|60|90|120)\s*days?\s*(?:late|past\s*due)|late\s+payment|delinquen",
    "repossession": r"(?i)repos(?:s)?ess",
    "foreclosure": r"(?i)foreclos",
    "bankruptcy": r"(?i)bankrupt",
    "judgment": r"(?i)judg(?:e)?ment",
    "settled": r"(?i)settled?\s+(?:for\s+)?less",
}


def extract_structured_accounts(text: str) -> list[dict]:
    """Extract structured account entries from credit report text."""
    accounts = []
    creditor_pattern = "|".join(re.escape(c) for c in KNOWN_CREDITORS)
    acct_num_re = re.compile(r"(?i)(?:account|acct|#|no)[\s#.:]*([A-Z0-9*x]{4,20})")
    amount_re = re.compile(r"\$[\d,]+(?:\.\d{2})?")
    date_re = re.compile(r"\b(\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\d{4}-\d{2}-\d{2})\b")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        context = line + " " + (lines[i + 1] if i + 1 < len(lines) else "")
        creditor_match = re.search(creditor_pattern, line, re.IGNORECASE)
        if not creditor_match:
            continue
        creditor = creditor_match.group(0).strip().title()
        acct_match = acct_num_re.search(context)
        account_number = acct_match.group(1) if acct_match else ""
        mark_type = "negative_item"
        for mtype, mpat in NEGATIVE_MARKS.items():
            if re.search(mpat, context):
                mark_type = mtype
                break
        amt_match = amount_re.search(context)
        amount = amt_match.group(0) if amt_match else ""
        dt_match = date_re.search(context)
        date = dt_match.group(1) if dt_match else ""
        entry = {
            "creditor": creditor,
            "account_number": account_number,
            "type": mark_type,
            "amount": amount,
            "date": date,
        }
        if not any(a["creditor"] == creditor and a["account_number"] == account_number for a in accounts):
            accounts.append(entry)
    return accounts


def parse_uploaded_files(filepaths: list[tuple[str, str]]) -> tuple[dict, str]:
    """Parse multiple uploaded files. Returns (parsed_disputes, combined_text)."""
    combined = ""
    ocr_failed = False
    for fp, fn in filepaths:
        text, failed = extract_text_from_file(fp, fn)
        combined += text + "\n"
        if failed:
            ocr_failed = True
    results = parse_text_for_disputes(combined)
    if ocr_failed and not results:
        results["unknown_accounts"] = {
            "label": "Manual Review Needed",
            "items": ["Image uploaded but OCR could not extract text — select dispute types manually below"],
        }
    return results, combined
