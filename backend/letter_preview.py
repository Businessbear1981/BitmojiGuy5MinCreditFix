"""
Pre-payment letter preview.

The letters are the product. Before this module existed, `GET /letters`
returned every letter in full to anyone holding a session id — all seven
sections, the violation theories, the verified case law, the state-law
block. A customer could run the flow, read everything, close the tab, and
mail the letters themselves for the price of a stamp.

The preview has to do two jobs at once:

  * Prove the work is real. A blurred rectangle proves nothing and reads as
    a trick. The customer should see their own name, their own accounts, the
    actual statutes being cited, and the shape of the argument.
  * Withhold enough that it cannot be mailed. What is expensive here is the
    reasoning: which theory applies to which tradeline, the case law behind
    it, and the specific demands. That is what stays behind the toll.

So: headers, the audit of what their file says, and the statutory basis are
shown in full. The theory arguments, the specific requests, the demand and
the escalation paths are summarised and withheld.
"""
from __future__ import annotations

import re

# Sections that are safe to show before payment. These establish credibility
# without carrying the argument.
_OPEN_SECTIONS = (
    "SECTION 1",  # audit — it's their own credit file, they already have it
    "SECTION 2",  # statutory basis — public law, and it builds trust
)

# Everything from here down is the product.
_GATED_SECTIONS = (
    "SECTION 3",   # consumer position
    "SECTION 4",   # theory blocks — the crown jewel
    "SECTION 4B",  # additional disputed items
    "SECTION 5",   # specific requests
    "SECTION 6",   # demand + escalation
    "SECTION 7",   # disclaimers
    "SECTION 8",   # tier escalation (MOV / pre-litigation / regulatory)
)

_SECTION_RE = re.compile(r"^SECTION [0-9]+[A-Z]?\s*—\s*(.+)$", re.MULTILINE)

_TOLL_NOTICE = """
────────────────────────────────────────────────────────────
  The rest of this letter is ready and waiting.

  What is withheld below: the violation theories matched to
  your specific accounts, the federal case law supporting
  each one, your state's authorities, and the itemised
  demands with deadlines.

  {n_sections} more sections · {n_words:,} more words · unlocked at checkout
────────────────────────────────────────────────────────────
"""


def _split_sections(body: str) -> list[tuple[str, str]]:
    """
    Break a letter into (heading, text) pairs.

    The first chunk has no heading — it's the address block and salutation,
    which always stays visible.
    """
    marks = list(_SECTION_RE.finditer(body))
    if not marks:
        return [("", body)]

    out = [("", body[: marks[0].start()])]
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        out.append((m.group(0).strip(), body[m.start(): end]))
    return out


def redact_letter(letter: dict) -> dict:
    """
    Return a preview-safe copy of one letter.

    The original is not mutated — the full text stays in the encrypted column
    and is what actually gets mailed and PDF'd after payment.
    """
    body = letter.get("text") or letter.get("body") or ""
    if not body:
        return {**letter, "locked": True}

    kept: list[str] = []
    withheld_words = 0
    withheld_sections = 0

    for heading, chunk in _split_sections(body):
        if not heading:
            kept.append(chunk)
            continue

        if heading.startswith(_OPEN_SECTIONS):
            kept.append(chunk)
            continue

        if heading.startswith(_GATED_SECTIONS):
            withheld_sections += 1
            withheld_words += len(chunk.split())
            # Show the heading so the customer can see what they're buying,
            # but nothing underneath it.
            if withheld_sections == 1:
                kept.append(heading + "\n")
            continue

        # Unrecognised section — withhold by default. Failing closed here
        # means a new section added to the engine is never leaked by accident.
        withheld_sections += 1
        withheld_words += len(chunk.split())

    preview = "".join(kept).rstrip()
    preview += "\n" + _TOLL_NOTICE.format(
        n_sections=withheld_sections, n_words=withheld_words
    )

    return {
        **letter,
        "text": preview,
        "body": preview,
        "locked": True,
        "preview": True,
        "withheld_sections": withheld_sections,
        "withheld_words": withheld_words,
        "full_length": len(body),
        "preview_length": len(preview),
    }


def redact_letters(letters: list[dict], paid: bool) -> list[dict]:
    """
    Gate a whole case's letters.

    Paid cases pass straight through untouched. This is the only place that
    decision is made, so there is one line to audit rather than one per
    endpoint.
    """
    if paid:
        return letters
    return [redact_letter(ltr) for ltr in (letters or [])]


def preview_summary(letters: list[dict]) -> dict:
    """
    Headline numbers for the preview screen — real counts from the real
    letters, so the value on offer is concrete rather than a marketing claim.
    """
    if not letters:
        return {"letters": 0, "words": 0, "theories": 0, "targets": []}

    return {
        "letters": len(letters),
        "words": sum(len((ltr.get("text") or "").split()) for ltr in letters),
        "theories": sum(ltr.get("theory_count", 0) for ltr in letters),
        "targets": [ltr.get("target", "") for ltr in letters],
    }
