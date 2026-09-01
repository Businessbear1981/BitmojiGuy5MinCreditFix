"""
Pre-payment letter gating.

The letters are the product. Before this module existed, `GET /letters`
returned every letter in full to anyone holding a session id — a customer
could run the flow, read everything, close the tab, and mail the letters
themselves for the price of a stamp.

── Why there is no partial preview ─────────────────────────────────────────

The first version of this module tried to show *part* of each letter: the
audit and the statutory basis in full, the argument withheld. That is the
nicer product, and it was quietly broken the whole time it shipped:

  * it split on section headings, so any letter whose headings did not match
    the expected shape came back whole. The collector letters use plain
    headings ("VALIDATION REQUESTS:"), matched nothing, and were served
    complete to unpaid callers — the preview was longer than the letter.
  * the heading pattern required one exact character, U+2014. A hyphen or an
    en-dash leaked the section under it.
  * open sections were matched by string prefix, so "SECTION 10" would have
    been treated as "SECTION 1" and shown free the day a tenth was added.

Each of those is the same failure: a redaction gate is a permanent obligation
to keep getting a parser right, and every miss gives the product away. So the
gate no longer parses anything. Unpaid callers get metadata about their
letters and no letter text at all. There is nothing left to leak.

What the customer still sees before paying: how many letters, addressed to
whom, at what escalation tier, how many items each covers, and how long they
are. That is enough to show the work is real. The words are the product.
"""
from __future__ import annotations

_LOCKED_NOTICE = """
────────────────────────────────────────────────────────────
  Your letters are written and waiting.

  {n_letters} letter(s) · {n_words:,} words · {n_items} disputed item(s)

  The full text, the violation theories matched to your
  accounts, the federal case law behind each one, your
  state's authorities and the itemised demands are
  unlocked at checkout.
────────────────────────────────────────────────────────────
"""


def redact_letter(letter: dict) -> dict:
    """
    Return a metadata-only stand-in for one letter.

    The original is untouched — the full text stays in the encrypted column
    and is what actually gets mailed and PDF'd after payment. `text` and
    `body` carry the locked notice rather than an empty string so any caller
    rendering them shows the paywall instead of a blank page.
    """
    body = letter.get("text") or letter.get("body") or ""
    words = len(body.split())

    notice = _LOCKED_NOTICE.format(
        n_letters=1, n_words=words, n_items=letter.get("item_count", 0)
    )

    return {
        # Identity and proof of work — safe to show, carries no argument.
        "target": letter.get("target", ""),
        "type": letter.get("type", "bureau"),
        "tier": letter.get("tier", 1),
        "tier_name": letter.get("tier_name", ""),
        "item_count": letter.get("item_count", 0),
        "theory_count": letter.get("theory_count", 0),
        "date": letter.get("date", ""),
        "id": letter.get("id", ""),
        # The product itself, withheld.
        "text": notice,
        "body": notice,
        "locked": True,
        "preview": True,
        "full_length": len(body),
        "word_count": words,
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
