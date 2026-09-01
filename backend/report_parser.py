"""
AI-Powered Credit Report Analyzer.

Uses Claude API to intelligently parse credit reports and extract
dispute items, classifying each into the correct bucket.

Fallback: keyword-based scanner if Claude API is not configured.
"""
import json
import os
import re

from dispute_engine.categories import (
    DISPUTE_CATEGORIES,
    guess_category,
    prompt_taxonomy,
    reason_for,
)
from equifax_parser import looks_like_equifax, parse_equifax

# --- PDF text extraction ---
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# --- Claude API ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# Overridable so a model retirement never requires a code change again.
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def extract_text_from_pdf_bytes(content: bytes) -> str:
    if not HAS_PYMUPDF:
        return ""
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:  # noqa: BLE001 - boundary must degrade, not crash; type logged
        print(f"PDF extraction error: {type(e).__name__}")
        return ""


def extract_text_from_bytes(content: bytes, suffix: str) -> str:
    """Extract text fully in memory — plaintext never touches disk."""
    suffix = suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf_bytes(content)
    elif suffix in (".txt", ".csv", ".text"):
        return content.decode("utf-8", errors="replace")
    return ""


# ======================================================================
# AI-Powered Analyzer (Claude API)
# ======================================================================

SYSTEM_PROMPT = """You are a credit report analysis engine for a consumer credit dispute platform.

Extract every negative, inaccurate, incomplete or otherwise disputable item from the report and classify each into exactly one dispute category.

Available dispute categories:
{taxonomy}

For each item found, return a JSON object with:
- bucket: one of the category IDs above, exactly as written
- type: "bureau" for items disputed with a credit bureau, "creditor" for items best disputed directly with the furnisher under FCRA 623
- target: the bureau name (Experian/Equifax/TransUnion) when the item is bureau-side, otherwise the creditor, collector or inquiring entity
- account: account number or identifier as printed, or "Unknown"
- amount: dollar amount if found (number or null)
- opened: date opened, in YYYY-MM-DD when the report gives one, else null
- dofd: date of first delinquency if the report states one separately, else null
- original_creditor: named original creditor when the furnisher is a collector or debt buyer, else ""
- reason: a specific, factual dispute reason written in the consumer's first-person voice
- confidence: "high", "medium", or "low"

Rules:
- One item per tradeline, inquiry or public record. Do not merge two accounts into one item.
- Report what the document says. Do not infer fraud, and never assert identity theft unless the report itself flags it — that claim carries legal weight the consumer has to make personally.
- Where a debt appears both as a charge-off from the original creditor and as a collection from a buyer, return both, and mark the second as duplicate only if the balances match.
- Prefer the more specific category: a hospital collection is medical_debt, not collection.
- Skip positive tradelines that are current and accurately reported.

Return ONLY a JSON array of items. No commentary. If nothing is disputable, return []."""

SYSTEM_PROMPT = SYSTEM_PROMPT.format(taxonomy=prompt_taxonomy())


def analyze_with_claude(report_text: str) -> list[dict]:
    """Use Claude API to analyze credit report text and extract dispute items."""
    if not HAS_ANTHROPIC or not ANTHROPIC_API_KEY:
        return []

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Truncate to ~50k chars to stay within context
    text = report_text[:50000]

    try:
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
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
            if bucket_id not in DISPUTE_CATEGORIES:
                bucket_id = _guess_bucket(item.get("reason", ""))

            cleaned.append({
                "bucket": bucket_id,
                "type": item.get("type", DISPUTE_CATEGORIES.get(bucket_id, {}).get("type", "bureau")),
                "target": item.get("target", "Unknown"),
                "account": item.get("account", "Unknown"),
                "amount": item.get("amount"),
                "opened": item.get("opened"),
                # Reported separately from date-opened when the report gives
                # it. The re-aging and obsolescence matchers both key off it.
                "dofd": item.get("dofd") or None,
                "original_creditor": item.get("original_creditor") or "",
                "reason": item.get("reason") or reason_for(
                    bucket_id,
                    target=item.get("target", ""),
                    account=item.get("account", ""),
                ),
                "confidence": item.get("confidence", "medium"),
            })
        return cleaned[:25]

    except Exception as e:  # noqa: BLE001 - boundary must degrade, not crash; type logged
        print(f"Claude API analysis error: {e}")
        return []


# ======================================================================
# Keyword Fallback Scanner
# ======================================================================

def analyze_with_keywords(report_text: str) -> list[dict]:
    """Fallback keyword-based scanner when Claude API is not available."""
    items = []
    lines = report_text.split("\n")
    seen = set()

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if not line_lower:
            continue

        for bucket_id, bucket in DISPUTE_CATEGORIES.items():
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
                            "reason": reason_for(bucket_id, target=target, account=account),
                            "confidence": "low",
                        })
                    break  # one bucket match per line

    return _select_strongest(items)


# How many disputes one round may carry. A letter is read by a human at the
# bureau; forty items in one envelope reads as a mail-merge and invites a
# frivolousness finding under § 1681i(a)(3) on the whole letter.
MAX_ITEMS_PER_ROUND = 20

# Severity ranking used when a report yields more than one round's worth.
# Higher is stronger: a closed statutory window is arithmetic, a "please
# verify this" is an opinion.
_ITEM_PRIORITY = {
    "obsolete": 100,
    "identity_theft": 95,
    "identity_error": 95,
    "deceased_indicator": 92,
    "re_aging": 90,
    "mixed_file": 88,
    "duplicate": 85,
    "bankruptcy": 82,
    "judgment_lien": 80,
    "debt_buyer": 78,
    "foreclosure": 74,
    "repossession": 72,
    "collection": 70,
    "medical_debt": 68,
    "child_support": 66,
    "rental_eviction": 64,
    "student_loan": 60,
    "charge_off": 55,
    "inquiry": 50,
    "status_inaccuracy": 45,
    "balance_inaccuracy": 40,
    "late_payment": 35,
    "personal_info": 30,
    "creditor_direct": 25,
}


def _select_strongest(items: list[dict]) -> list[dict]:
    """
    Trim to one round's worth, strongest first.

    This used to be `items[:20]` — the first twenty matches in DOCUMENT ORDER.
    Every bureau report prints personal information first and public records
    and inquiries last, so the budget was spent on header noise and a
    bankruptcy or a judgment sitting in the text was never reached. Measured
    on a synthetic Experian file: a Chapter 7 and a hard inquiry were both
    present and both missed.

    Ordering by severity instead means the twenty that survive are the twenty
    worth arguing, wherever they appeared in the file.
    """
    if len(items) <= MAX_ITEMS_PER_ROUND:
        return items
    ranked = sorted(
        items,
        key=lambda it: -_ITEM_PRIORITY.get(it.get("bucket", ""), 0),
    )
    return ranked[:MAX_ITEMS_PER_ROUND]


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
    """Deprecated alias — the taxonomy owns this now."""
    return guess_category(reason)



# ======================================================================
# Main entry point
# ======================================================================

def parse_credit_report_bytes(content: bytes, suffix: str) -> list[dict]:
    """
    Parse a credit report and extract dispute items.

    Order matters. A structured parser that recognises the report's own
    labels beats a model guessing from prose, costs nothing per report, and
    is reproducible — so it runs first. Claude is the fallback for layouts
    we have not written a parser for, and the keyword scanner is the last
    resort for scanned or mangled text.
    """
    text = extract_text_from_bytes(content, suffix)
    if not text.strip():
        return []

    # 1. Structured parser — Equifax is the format we ask consumers to pull.
    if looks_like_equifax(text):
        parsed = parse_equifax(text)
        items = parsed.get("accounts", [])
        if items:
            # Carry the file-level signals through on the first item so the
            # analyst can see address variance, repeat furnishers and
            # transferred-debt flags without re-reading the PDF.
            items[0]["_report_meta"] = parsed.get("report_meta", {})
            items[0]["_data_quality_flags"] = parsed.get("data_quality_flags", [])
            items[0]["_consumer_profile"] = parsed.get("consumer_profile", {})
            return items

    # 2. Claude, for formats without a dedicated parser.
    if ANTHROPIC_API_KEY and HAS_ANTHROPIC:
        items = analyze_with_claude(text)
        if items:
            return items

    # 3. Keyword scanner — scanned images, unusual layouts, damaged text.
    return analyze_with_keywords(text)


def parse_report_full(content: bytes, suffix: str) -> dict:
    """
    Full structured parse, for callers that want the whole picture rather
    than just the dispute items — the client dashboard, the analyst, and
    the outcome ledger all want the file-level context.
    """
    text = extract_text_from_bytes(content, suffix)
    if not text.strip():
        return {"accounts": [], "report_meta": {}, "data_quality_flags": []}

    if looks_like_equifax(text):
        return parse_equifax(text)

    return {
        "file_metadata": {"bureau": "unknown", "parser": "fallback"},
        "consumer_profile": {},
        "accounts": parse_credit_report_bytes(content, suffix),
        "report_meta": {},
        "data_quality_flags": ["unrecognised_format: no structured parser matched"],
    }
