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
from experian_parser import looks_like_experian, parse_experian
from experian_parser import report_summary as experian_summary
from money import money_str

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

            # Same bar as the keyword scanner: the model is not allowed to
            # return a dispute it cannot attribute to a tradeline either.
            if not _is_attributable(item.get("target", ""), item.get("account", "")):
                continue

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

# A credit report is mostly furniture: section headings, field labels, the
# bureau's own name. The keyword scanner matches a category word anywhere in
# the text, so it matched these too, and produced "disputes" whose furnisher
# was "Monthly Payment" or "Addresses".
_REPORT_FURNITURE = frozenset({
    "addresses", "other address", "address", "personal information",
    "monthly payment", "payment history", "account closures", "closures",
    "accounts", "account history", "account type", "account status",
    "public records", "inquiries", "credit summary", "score factors",
    "employment", "employment data", "balance", "high balance",
    "credit limit", "date opened", "date closed", "last payment",
    "past due", "responsibility", "terms", "status", "remarks",
    "original creditor", "creditor contact", "summary", "unknown",
    "name", "names", "date of birth", "phone numbers", "file number",
})

_NULLISH = frozenset({"", "unknown", "none", "n/a", "na", "null", "-", "--"})


def _is_attributable(target: str, account: str) -> bool:
    """
    Whether an item names a tradeline a bureau could actually look up.

    A dispute has to identify what it is about. Without this, a keyword hit on
    the report's own heading became an item with account="Unknown" and
    target="Monthly Payment", and those items reached real letters — a demand
    to delete something that was never an account.

    The keyword scanner has no structure to lean on, so it must show an
    account identifier: four or more characters containing a digit. The
    dedicated Experian and Equifax parsers read the account number straight
    off the tradeline and are unaffected by this.

    A bureau name is a legitimate `target` — that field is who the letter is
    addressed to, not who furnishes the debt — so only the report's own field
    labels are refused here.
    """
    acct = (account or "").strip()
    if len(acct) < 4 or acct.lower() in _NULLISH or not any(c.isdigit() for c in acct):
        return False

    name = re.sub(r"[^a-z ]", " ", (target or "").lower()).strip()
    name = re.sub(r"\s+", " ", name)
    if len(name) < 3 or name in _NULLISH:
        return False
    return name not in _REPORT_FURNITURE


def analyze_with_keywords(report_text: str) -> list[dict]:
    """
    Fallback keyword-based scanner when no dedicated parser matched.

    Emits only items it can attribute — see `_is_attributable`. Returning
    nothing is a valid and frequent answer: the upload endpoint turns it into
    an honest "this file could not be read as a credit report" rather than a
    letter full of invented tradelines.
    """
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
                    # The same window the amount uses. A report prints the
                    # account number on its own line and the status a line or
                    # two below, so searching only the matched line found no
                    # account for the very items the keyword had just hit —
                    # and `_is_attributable` then dropped every one of them.
                    context = " ".join(lines[max(0, i - 2):i + 3])

                    # Extract account number
                    acct_match = re.search(
                        r'(?:account|acct)[#:\s]*([A-Za-z0-9\-]+)', context, re.IGNORECASE
                    )
                    account = acct_match.group(1) if acct_match else "Unknown"

                    # Extract dollar amount — exact decimal string, not a
                    # float; see money.py.
                    amt_match = re.search(r'\$[\d,]+\.?\d*', context)
                    amount = money_str(amt_match.group()) if amt_match else ""

                    # Detect target
                    target = _detect_target(lines, i)

                    if not _is_attributable(target, account):
                        break

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

# File-level signals ride on the first item rather than in a second return
# value. They have to be lifted off before the list is reordered or trimmed.
_META_KEYS = ("_report_meta", "_data_quality_flags", "_consumer_profile")


def _finalise(items: list[dict]) -> list[dict]:
    """
    One round's worth, strongest first, with the file-level meta preserved.

    Every parser used to return its full list: the Experian path handed back
    52 items for one envelope while `MAX_ITEMS_PER_ROUND` and the comment
    above it say 20, because more than that "reads as a mail-merge and invites
    a frivolousness finding under § 1681i(a)(3) on the whole letter". The cap
    was only ever applied on the keyword path.

    Trimming has to happen after the severity sort, and the meta has to be
    moved onto whichever item survives as first — sorting alone would strand
    it on an item that is no longer at index 0, or drop it with the tail.
    """
    if not items:
        return []

    meta = {}
    for item in items:
        for key in _META_KEYS:
            if key in item:
                meta.setdefault(key, item.pop(key))

        # Every item has to state why it is disputed. The Equifax parser
        # returned reason="" and the API rejects that with 422, so a case
        # holding a clean Equifax parse could not save its disputes at all.
        # The text comes from the category the parser actually read, in the
        # consumer's voice — the same default the keyword and model paths use.
        if not str(item.get("reason") or "").strip():
            item["reason"] = reason_for(
                item.get("bucket") or "",
                target=item.get("furnisher") or item.get("target") or "",
                account=item.get("account") or "",
            )

    kept = _select_strongest(items)
    if kept and meta:
        kept[0].update(meta)
    return kept


def parse_credit_report_bytes(content: bytes, suffix: str) -> list[dict]:
    """
    Parse a credit report and extract dispute items.

    Order matters. A structured parser that recognises the report's own
    labels beats a model guessing from prose, costs nothing per report, and
    is reproducible — so it runs first. Claude is the fallback for layouts
    we have not written a parser for, and the keyword scanner is the last
    resort for scanned or mangled text.

    Every path returns through `_finalise`, so the per-round cap applies
    whichever parser answered.
    """
    text = extract_text_from_bytes(content, suffix)
    if not text.strip():
        return []

    # 1. Experian — the format we actually ask consumers to bring. Runs first
    #    because it is the common case: on a real 91-page export the keyword
    #    scanner returned twenty items whose creditors were `Individual`,
    #    `Signer` and `Hays Mt`, while this parser returns the 36 tradelines
    #    the report's own header counts, with account numbers and dates.
    #    Handles both the annual PDF and the fuller detailed record.
    if looks_like_experian(text):
        items = parse_experian(text)
        if items:
            items[0]["_report_meta"] = experian_summary(text)
            return _finalise(items)

    # 2. Structured parser — Equifax.
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
            return _finalise(items)

    # 3. Claude, for formats without a dedicated parser.
    if ANTHROPIC_API_KEY and HAS_ANTHROPIC:
        items = analyze_with_claude(text)
        if items:
            return _finalise(items)

    # 4. Keyword scanner — scanned images, unusual layouts, damaged text.
    #    Already selects internally; _finalise is idempotent under the cap.
    return _finalise(analyze_with_keywords(text))


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
