"""
Money, in one representation.

A dispute letter's whole subject is money, and every figure in it is quoted
back to a bureau or a furnisher. Binary floats cannot hold the decimal values
a credit report prints, so money is never a float here:

  * on the wire and in storage — a decimal **string**, "527.00", exact and
    JSON-safe. `Decimal` serialises to a JSON number by default, which is a
    float again by the time it reaches a browser.
  * in Python — `Decimal`, for anything that parses, compares or formats.

Amounts are quantised to cents. A credit report never prints a fraction of a
cent, and rounding at the boundary means two figures that display the same
also compare the same.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

CENTS = Decimal("0.01")

# "$1,284.00", "1284", "-31,354.29", "(527.00)" as a negative.
_AMOUNT = re.compile(r"(?P<paren>\()?\s*(?P<sign>-)?\s*\$?\s*(?P<num>[\d,]+(?:\.\d+)?)")

_NOT_AN_AMOUNT = frozenset({"", "-", "--", "n/a", "na", "none", "unknown", "null"})


def parse_money(raw: object) -> Decimal | None:
    """
    A money value from whatever the report printed, or None.

    Returns None rather than zero when there is nothing to read: a missing
    balance and a zero balance are different claims to make in a letter.
    """
    if raw is None:
        return None
    if isinstance(raw, Decimal):
        return raw.quantize(CENTS)
    if isinstance(raw, int) and not isinstance(raw, bool):
        return Decimal(raw).quantize(CENTS)
    if isinstance(raw, float):
        # Only reachable from data written before this module existed. Going
        # through str() keeps the shortest representation that round-trips,
        # so 527.0 quantises to 527.00 rather than 526.99999…
        return Decimal(str(raw)).quantize(CENTS)

    text = str(raw).strip()
    if text.lower() in _NOT_AN_AMOUNT:
        return None

    match = _AMOUNT.search(text)
    if not match:
        return None
    try:
        value = Decimal(match.group("num").replace(",", ""))
    except InvalidOperation:
        return None
    if match.group("sign") or match.group("paren"):
        value = -value
    return value.quantize(CENTS)


def money_str(value: object) -> str:
    """
    The storage and transport form: "527.00", or "" for nothing.

    Deliberately unformatted — no currency symbol, no thousands separator.
    `_fmt_money` in the letter generator owns presentation; mixing the two is
    how the same balance reached one letter three different ways.
    """
    amount = parse_money(value)
    return "" if amount is None else f"{amount:f}"


def fmt_money(value: object) -> str:
    """
    Presentation form for a document: `$1,284.00`, or "" for nothing.

    The sign goes outside the currency symbol — `-$31,354.29`, not
    `$-31,354.29`.
    """
    amount = parse_money(value)
    if amount is None:
        return ""
    if amount < 0:
        return f"-${-amount:,.2f}"
    return f"${amount:,.2f}"
