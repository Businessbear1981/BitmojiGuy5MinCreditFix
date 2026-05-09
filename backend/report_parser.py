"""
AI-Powered Credit Report Analyzer.

Uses Claude API to intelligently parse credit reports and extract
dispute items, classifying each into the correct bucket.

Fallback: keyword-based scanner if Claude API is not configured.
"""
import os
import re
import json
from pathlib import Path
from typing import List
from dotenv import load_dotenv
load_dotenv()

from buckets import DISPUTE_BUCKETS, FCRA_CITATIONS

# --- PDF text extraction ---
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# --- Claude API ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def extract_text_from_pdf(file_path: Path) -> str:
    if not HAS_PYMUPDF:
        return ""
    try:
        doc = fitz.open(str(file_path))
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in (".txt", ".csv", ".text"):
        return file_path.read_text(encoding="utf-8", errors="replace")
    return ""


# ======================================================================
# AI-Powered Analyzer (Claude API)
# ======================================================================

SYSTEM_PROMPT = """You are a credit report analysis engine for a consumer credit dispute platform.

Your job is to extract every negative, inaccurate, or disputable item from a credit report and classify each into the correct dispute bucket.

Available dispute buckets:
- collection: Collection accounts, debts sold/transferred to collectors
- late_payment: Late payment notations (30/60/90/120 days)
- charge_off: Charged-off accounts, profit/loss write-offs
- identity_error: Accounts that don't belong to the consumer, mixed files
- inquiry: Unauthorized hard inquiries
- medical_debt: Medical collections or medical-related debt
- creditor_direct: Items best disputed directly with the creditor under §623
- obsolete: Items older than 7 years that should have aged off

For each item found, return a JSON object with:
- bucket: one of the bucket IDs above
- type: "bureau" or "creditor"
- target: the bureau name (Experian/Equifax/TransUnion) or creditor/collector name
- account: account number or identifier
- amount: dollar amount if found (number or null)
- opened: date opened or date of first delinquency if found (string or null)
- reason: a specific, actionable dispute reason for this item
- confidence: "high", "medium", or "low"

Return ONLY a JSON array of items. No commentary. If no disputable items found, return [].
Focus on items that are genuinely negative or inaccurate — don't flag normal positive tradelines."""


def analyze_with_claude(report_text: str) -> List[dict]:
    """Use Claude API to analyze credit report text and extract dispute items."""
    if not HAS_ANTHROPIC or not ANTHROPIC_API_KEY:
        return []

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Truncate to ~50k chars to stay within context
    text = report_text[:50000]

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this credit report and extract all disputable items:\n\n{text}",
                }
            ],
        )

        response_text = message.content[0].text.strip()

        # Parse JSON from response (handle markdown code blocks)
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        items = json.loads(response_text)
        if not isinstance(items, list):
            return []

        # Validate and clean items
        cleaned = []
        for item in items:
            bucket_id = item.get("bucket", "")
            if bucket_id not in DISPUTE_BUCKETS:
                bucket_id = _guess_bucket(item.get("reason", ""))

            cleaned.append({
                "bucket": bucket_id,
                "type": item.get("type", DISPUTE_BUCKETS.get(bucket_id, {}).get("type", "bureau")),
                "target": item.get("target", "Unknown"),
                "account": item.get("account", "Unknown"),
                "amount": item.get("amount"),
                "opened": item.get("opened"),
                "reason": item.get("reason", "Disputed — verify accuracy"),
                "confidence": item.get("confidence", "medium"),
            })
        return cleaned[:25]

    except Exception as e:
        print(f"Claude API analysis error: {e}")
        return []


# ======================================================================
# Keyword Fallback Scanner
# ======================================================================

def analyze_with_keywords(report_text: str) -> List[dict]:
    """Fallback keyword-based scanner when Claude API is not available."""
    items = []
    lines = report_text.split("\n")
    seen = set()

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if not line_lower:
            continue

        for bucket_id, bucket in DISPUTE_BUCKETS.items():
            for keyword in bucket["keywords"]:
                if keyword in line_lower:
                    # Extract account number
                    acct_match = re.search(
                        r'(?:account|acct)[#:\s]*([A-Za-z0-9\-]+)', line, re.IGNORECASE
                    )
                    account = acct_match.group(1) if acct_match else "Unknown"

                    # Extract dollar amount
                    amount = None
                    context = " ".join(lines[max(0, i - 2):i + 3])
                    amt_match = re.search(r'\$[\d,]+\.?\d*', context)
                    if amt_match:
                        try:
                            amount = float(amt_match.group().replace("$", "").replace(",", ""))
                        except ValueError:
                            pass

                    # Detect target
                    target = _detect_target(lines, i)

                    key = (bucket_id, target, account)
                    if key not in seen:
                        seen.add(key)
                        items.append({
                            "bucket": bucket_id,
                            "type": bucket["type"],
                            "target": target,
                            "account": account,
                            "amount": amount,
                            "opened": None,
                            "reason": bucket["reason_template"].format(
                                account=account, target=target
                            ),
                            "confidence": "low",
                        })
                    break  # one bucket match per line

    return items[:20]


def _detect_target(lines: list, idx: int) -> str:
    """Try to detect the bureau or creditor name near a given line."""
    context = " ".join(lines[max(0, idx - 5):idx + 5]).lower()
    for bureau in ["experian", "equifax", "transunion"]:
        if bureau in context:
            return bureau.title()
    # Check for creditor name (capitalized line above)
    for j in range(max(0, idx - 3), idx):
        if lines[j].strip() and lines[j].strip()[0].isupper():
            candidate = lines[j].strip()
            if len(candidate) > 3 and len(candidate) < 50:
                return candidate.title()
    return "Experian"


def _guess_bucket(reason: str) -> str:
    """Guess the best bucket from a reason string."""
    reason_lower = reason.lower()
    for bucket_id, bucket in DISPUTE_BUCKETS.items():
        for kw in bucket["keywords"]:
            if kw in reason_lower:
                return bucket_id
    return "collection"  # default


# ======================================================================
# Main entry point
# ======================================================================

def parse_credit_report(file_path: Path) -> List[dict]:
    """
    Parse a credit report file and extract dispute items.
    Uses Claude API if configured, falls back to keyword scanning.
    """
    text = extract_text(file_path)
    if not text.strip():
        return []

    # Try AI-powered analysis first
    if ANTHROPIC_API_KEY and HAS_ANTHROPIC:
        items = analyze_with_claude(text)
        if items:
            return items

    # Fall back to keyword scanner
    return analyze_with_keywords(text)
