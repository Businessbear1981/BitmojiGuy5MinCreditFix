"""
Letter provenance — watermarking, timestamps, and a tamper-evident audit trail.

Three jobs, all about proving where a letter came from:

  1. A **visible footer** on every letter: case reference, generation
     timestamp, tier. This is not a deterrent, it is good practice — a
     dispute letter should carry a reference the consumer can quote when
     the bureau writes back, and it dates the letter for the § 611 clock.

  2. An **invisible fingerprint** woven into the body using zero-width
     characters. Survives copy-paste and most text processing. If your
     letters turn up on a competitor's site, you can extract the session
     they were generated for. It does not prevent copying — nothing does —
     but it makes copying attributable.

  3. A **hash-chained audit log**. Every generation, preview, release and
     download is recorded with a timestamp and the hash of the previous
     entry. Altering or removing an entry breaks the chain and
     `verify_chain()` will say where.

The watermark is not a security control. The paywall in letter_preview.py
is the security control. This is forensics for after the fact.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone

import config

# ── Zero-width alphabet ─────────────────────────────────────────────────────
# Three invisible codepoints give us base-3; we use two for a clean base-2.
# ZWSP and ZWNJ render as nothing in every mail client, browser and word
# processor, and survive a copy-paste into a plain text field.
_ZERO = "\u200b"   # ZERO WIDTH SPACE          -> bit 0
_ONE = "‌"    # ZERO WIDTH NON-JOINER     -> bit 1
_MARK = "‍"   # ZERO WIDTH JOINER         -> start/end sentinel

_ZW_ALL = (_ZERO, _ONE, _MARK)

FINGERPRINT_BITS = 48  # 6 bytes — enough to identify a case, short enough to hide


def fingerprint(session_id: str, issued_at: datetime | None = None) -> str:
    """
    Short, non-reversible case fingerprint.

    Keyed with the server secret so a fingerprint cannot be forged or
    brute-forced back to a session id by anyone holding a letter.
    """
    issued_at = issued_at or datetime.now(timezone.utc)
    stamp = issued_at.strftime("%Y%m%d%H")
    raw = f"{session_id}:{stamp}".encode()
    digest = hmac.new(config.CYPHER_SERVER_SECRET.encode(), raw, hashlib.sha256).digest()
    return digest[: FINGERPRINT_BITS // 8].hex()


def _bits(payload: str) -> str:
    return "".join(f"{byte:08b}" for byte in bytes.fromhex(payload))


# Spans that have to survive byte-exact. "Period-space" alone treated every
# legal abbreviation as a sentence end, so the carrier landed inside the
# citations: "15 U.S.C. § 1681c" became "15 U.S.C. <zw>§ 1681c", and a bureau
# searching its own intake for "15 U.S.C. § 1681c" no longer matched the letter
# that cited it.
_CITATION_SPAN = re.compile(
    r"\d+\s+U\.S\.C\.(?:\s*§+\s*[\w().\-]+)*"      # 15 U.S.C. § 1681c(a)(4)
    r"|§+\s*[\w().\-]+"                            # § 1681i(a)(7)
    r"|\b\d+\s+[A-Z][A-Za-z.]{0,7}\.?(?:\s+\d[a-z]{0,2})?\s+\d+"  # 84 F. Supp. 3d 1044
    r"|\bv\.\s+[A-Z][^,\n]{0,70}"                  # v. Experian Information …
    r"|\([^)\n]{0,40}\d{4}\)"                      # (C.D. Cal. 2014)
)

# Undotted abbreviations that end in a period without ending a sentence.
# Dotted ones (U.S.C., C.D., P.O.) are caught by the dotted-token test below.
_NOT_SENTENCE_END = frozenset({
    "supp", "cir", "seq", "inc", "ltd", "corp", "llc", "llp", "stat", "art",
    "sec", "subsec", "para", "rev", "reg", "ibid", "etc", "viz", "mrs",
    "ave", "apt", "dept", "div", "est", "fed", "dist", "app", "rptr",
    "cal", "tex", "wash", "mich", "mass", "minn", "colo", "conn", "fla",
    "ill", "kan", "mont", "neb", "nev", "okla", "ore", "tenn", "wis",
    "ariz", "ark", "del", "ind", "super", "bankr", "comm", "admin", "misc",
})


def _sentence_anchors(text: str) -> list[int]:
    """
    Offsets just past a real sentence end.

    Three things disqualify a period-space: the next character not opening a
    new sentence, the token before the period being an abbreviation rather
    than a word, and the position falling inside a citation. What survives is
    ordinary prose, so the carrier never lands in text that has to be quoted
    back exactly.
    """
    blocked = [m.span() for m in _CITATION_SPAN.finditer(text)]

    anchors: list[int] = []
    for i in range(len(text) - 2):
        if text[i] != "." or text[i + 1] != " ":
            continue

        nxt = text[i + 2]
        if not (nxt.isupper() or nxt.isdigit() or nxt in '"“'):
            continue

        # The token ending at this period.
        j = i - 1
        while j >= 0 and (text[j].isalpha() or text[j] == "."):
            j -= 1
        token = text[j + 1: i]
        if "." in token:
            continue          # U.S.C, C.D — mid-citation
        low = token.lower()
        if low and (len(low) < 2 or low in _NOT_SENTENCE_END):
            continue

        at = i + 2
        if any(start < at < end for start, end in blocked):
            continue

        anchors.append(at)
    return anchors


def embed_invisible(text: str, fp: str) -> str:
    """
    Weave the fingerprint through the letter body.

    Bits are distributed after sentence-ending spaces rather than dumped in
    one block, so truncating the letter still leaves a recoverable partial
    fingerprint, and a casual glance at the raw bytes shows nothing unusual.
    """
    if not text or not fp:
        return text

    payload = _bits(fp)
    carrier = _MARK + "".join(_ONE if b == "1" else _ZERO for b in payload) + _MARK

    anchors = _sentence_anchors(text)

    if not anchors:
        return text + carrier

    chunk = max(1, len(carrier) // min(len(anchors), 12))
    out, cursor, pos = [], 0, 0
    for anchor in anchors[:12]:
        out.append(text[cursor:anchor])
        out.append(carrier[pos: pos + chunk])
        pos += chunk
        cursor = anchor
    out.append(text[cursor:])
    if pos < len(carrier):
        out.append(carrier[pos:])
    return "".join(out)


def extract_invisible(text: str) -> str | None:
    """
    Recover a fingerprint from a letter found in the wild.

    Returns the hex fingerprint, or None if no watermark survived. Compare
    it against `fingerprint(session_id, issued_at)` for each candidate case
    to identify the source.
    """
    if not text:
        return None
    bits = "".join(
        "1" if ch == _ONE else "0"
        for ch in text
        if ch in (_ZERO, _ONE)
    )
    if len(bits) < 8:
        return None
    usable = bits[: (len(bits) // 8) * 8]
    try:
        return bytes(int(usable[i: i + 8], 2) for i in range(0, len(usable), 8)).hex()
    except ValueError:
        return None


def strip_invisible(text: str) -> str:
    """Remove every watermark character. Used before diffing or testing."""
    for ch in _ZW_ALL:
        text = text.replace(ch, "")
    return text


# ── Visible provenance footer ───────────────────────────────────────────────

_FOOTER = """

────────────────────────────────────────────────────────────
Case reference: {ref}
Prepared: {ts} UTC
Round: Tier {tier} — {tier_name}
Prepared by the consumer using self-help document preparation
software. Not legal advice. Retain this reference for your records.
────────────────────────────────────────────────────────────"""


def provenance_footer(session_id: str, tier: int = 1, tier_name: str = "",
                      issued_at: datetime | None = None) -> str:
    """The visible block that goes at the foot of every letter."""
    issued_at = issued_at or datetime.now(timezone.utc)
    return _FOOTER.format(
        ref=session_id[:8].upper(),
        ts=issued_at.strftime("%Y-%m-%d %H:%M"),
        tier=tier,
        tier_name=tier_name or "Reinvestigation Demand",
    )


def stamp_letter(letter: dict, session_id: str, issued_at: datetime | None = None) -> dict:
    """
    Apply both marks to one letter: visible footer, invisible fingerprint.

    Called at generation time, so the stored letter carries its provenance
    and everything downstream — PDF, mail, email — inherits it.
    """
    issued_at = issued_at or datetime.now(timezone.utc)
    body = letter.get("text") or ""
    if not body:
        return letter

    fp = fingerprint(session_id, issued_at)
    # One blank line between the signature block and the footer rule, matching
    # the single-blank-line spacing `_assemble()` enforces everywhere else.
    # Appending the footer to a body that already ended in a newline left a
    # three-newline gap that no other join in the letter has.
    body = body.rstrip("\n") + provenance_footer(
        session_id, letter.get("tier", 1), letter.get("tier_name", ""), issued_at
    )
    body = embed_invisible(body, fp)

    return {
        **letter,
        "text": body,
        "fingerprint": fp,
        "issued_at": issued_at.isoformat(),
    }


# ── Hash-chained audit log ──────────────────────────────────────────────────

_AUDIT_DB = os.environ.get("AUDIT_DB", "audit_chain.db")
_lock = threading.Lock()

GENESIS = "0" * 64


def _conn():
    c = sqlite3.connect(_AUDIT_DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_audit():
    """Create the audit table. Idempotent; safe across multiple workers."""
    with _lock, _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS audit_chain (
                seq        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts         TEXT NOT NULL,
                session_id TEXT NOT NULL,
                event      TEXT NOT NULL,
                detail     TEXT NOT NULL DEFAULT '',
                prev_hash  TEXT NOT NULL,
                hash       TEXT NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS ix_audit_session ON audit_chain(session_id)")
        c.execute("CREATE INDEX IF NOT EXISTS ix_audit_ts ON audit_chain(ts)")


def _entry_hash(ts: str, session_id: str, event: str, detail: str, prev_hash: str) -> str:
    raw = f"{ts}|{session_id}|{event}|{detail}|{prev_hash}".encode()
    return hashlib.sha256(raw).hexdigest()


def record(session_id: str, event: str, detail: dict | str = "") -> str:
    """
    Append one event to the chain. Returns the new entry's hash.

    Events worth recording: letters_generated, letters_previewed,
    payment_requested, payment_released, letters_mailed, pdf_downloaded.

    `detail` must never contain PII — it is not encrypted. Counts, tiers,
    targets and tracking numbers only.
    """
    if isinstance(detail, dict):
        detail = json.dumps(detail, sort_keys=True, separators=(",", ":"))

    ts = datetime.now(timezone.utc).isoformat()
    with _lock, _conn() as c:
        row = c.execute("SELECT hash FROM audit_chain ORDER BY seq DESC LIMIT 1").fetchone()
        prev = row["hash"] if row else GENESIS
        h = _entry_hash(ts, session_id, event, detail, prev)
        c.execute(
            "INSERT INTO audit_chain (ts, session_id, event, detail, prev_hash, hash)"
            " VALUES (?,?,?,?,?,?)",
            (ts, session_id, event, detail, prev, h),
        )
    return h


def verify_chain() -> dict:
    """
    Walk the chain and confirm nothing has been altered or removed.

    Returns {"ok": bool, "entries": int, "broken_at": seq|None}. A break
    means someone edited the database directly — the log is append-only by
    construction, so there is no legitimate way for this to fail.
    """
    with _lock, _conn() as c:
        rows = c.execute("SELECT * FROM audit_chain ORDER BY seq ASC").fetchall()

    prev = GENESIS
    for row in rows:
        expected = _entry_hash(row["ts"], row["session_id"], row["event"],
                               row["detail"], prev)
        if expected != row["hash"] or row["prev_hash"] != prev:
            return {"ok": False, "entries": len(rows), "broken_at": row["seq"]}
        prev = row["hash"]

    return {"ok": True, "entries": len(rows), "broken_at": None}


def history(session_id: str | None = None, limit: int = 100) -> list[dict]:
    """Read the trail, newest first. Scoped to one case when given."""
    sql = "SELECT seq, ts, session_id, event, detail, hash FROM audit_chain"
    args: tuple = ()
    if session_id:
        sql += " WHERE session_id = ?"
        args = (session_id,)
    sql += " ORDER BY seq DESC LIMIT ?"
    args = args + (limit,)

    with _lock, _conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


def identify(letter_text: str, candidates: list[tuple[str, datetime]]) -> str | None:
    """
    Given a letter found in the wild and a list of (session_id, issued_at)
    candidates, return the session it was generated for.

    Used when investigating a leak: pull the day's cases from the audit log,
    pass them in, and this names the source.
    """
    found = extract_invisible(letter_text)
    if not found:
        return None
    for session_id, issued_at in candidates:
        expected = fingerprint(session_id, issued_at)
        if found.startswith(expected[: len(found)]) or expected.startswith(found):
            return session_id
    return None
