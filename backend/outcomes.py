"""
Outcome ledger — the training set.

Every case teaches us something: which theory, aimed at which bureau, against
which kind of tradeline, actually got the item deleted. Nobody publishes that.
FICO's weighting is a trade secret and the bureaus don't disclose their
reinvestigation logic — but *removal rates are observable*, and after enough
disputes they are estimable from our own data.

That is the difference between folklore and evidence:

    folklore : "a collection costs you 8 points"       (invented)
    evidence : "43 of 61 obsolescence disputes against
                Experian were deleted"                  (counted)

The second is defensible, useful, and impossible for a competitor to copy
without running the same volume.

── Why this is a separate store ────────────────────────────────────────────

Case records are hard-deleted at 24 hours (ADR-0002). Outcome rows must
outlive them, so they are written here instead, carrying **no PII and no
session id** — only the features needed to learn from, plus a salted case
hash so a duplicate submission cannot be double-counted.

You cannot get back from an outcome row to a person. That is deliberate: it
means the ledger can be kept indefinitely, exported, and modelled without
inheriting the retention promise made to consumers.

── What can and cannot be claimed ──────────────────────────────────────────

Removal rates: measurable, and once n is large enough per cell, reportable
as an observed historical rate.

Score movement: only if consumers voluntarily report before/after scores.
Even then it is self-reported, unverified, confounded by everything else in
their file, and should never be presented as a prediction for a specific
person. `score_deltas()` returns the observed distribution and the sample
size, so the number can never be quoted without its own uncertainty.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import statistics
import threading
from datetime import datetime, timezone

import config

_DB = os.environ.get("OUTCOMES_DB", "outcomes.db")
_lock = threading.Lock()

# A cell needs this many observations before we will quote a rate at all.
MIN_SAMPLE_FOR_RATE = 25


def _conn():
    c = sqlite3.connect(_DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_outcomes():
    """Create the ledger. Idempotent."""
    with _lock, _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS dispute_outcomes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                case_hash     TEXT NOT NULL,
                item_hash     TEXT NOT NULL,
                created_at    TEXT NOT NULL,

                -- Features. No PII: categories, theories, coarse buckets.
                category      TEXT NOT NULL,
                theory        TEXT NOT NULL DEFAULT '',
                bureau        TEXT NOT NULL,
                tier          INTEGER NOT NULL DEFAULT 1,
                item_age_days INTEGER,
                balance_band  TEXT,
                is_debt_buyer INTEGER DEFAULT 0,
                state         TEXT DEFAULT '',

                -- Outcome, filled in later when we learn what happened.
                outcome       TEXT,          -- deleted | verified | updated | no_response
                resolved_at   TEXT,
                days_to_resolve INTEGER,
                source        TEXT,          -- consumer_reported | report_reupload | admin

                UNIQUE(case_hash, item_hash, tier)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS score_reports (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                case_hash   TEXT NOT NULL,
                reported_at TEXT NOT NULL,
                bureau      TEXT NOT NULL,
                score_before INTEGER,
                score_after  INTEGER,
                items_removed INTEGER,
                days_elapsed  INTEGER,
                source      TEXT DEFAULT 'consumer_reported'
            )
        """)
        for stmt in (
            "CREATE INDEX IF NOT EXISTS ix_out_cat ON dispute_outcomes(category, bureau, outcome)",
            "CREATE INDEX IF NOT EXISTS ix_out_theory ON dispute_outcomes(theory, outcome)",
            "CREATE INDEX IF NOT EXISTS ix_out_case ON dispute_outcomes(case_hash)",
        ):
            c.execute(stmt)


# ── Hashing ─────────────────────────────────────────────────────────────────

def _h(*parts: str) -> str:
    """Salted one-way hash. Identifies without identifying."""
    raw = "|".join(parts).encode()
    return hashlib.sha256(config.PII_ENCRYPTION_KEY.encode() + raw).hexdigest()[:24]


def _balance_band(amount) -> str:
    """Coarse buckets — the exact figure is not needed and is more revealing."""
    try:
        v = float(amount or 0)
    except (TypeError, ValueError):
        return "unknown"
    if v <= 0:
        return "zero"
    for cap, label in ((100, "0-100"), (500, "100-500"), (1000, "500-1k"),
                       (5000, "1k-5k"), (10000, "5k-10k")):
        if v < cap:
            return label
    return "10k+"


def _age_days(opened: str | None) -> int | None:
    if not opened:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(opened[:10], fmt)
            return (datetime.now() - dt).days
        except ValueError:
            continue
    return None


# ── Writing ─────────────────────────────────────────────────────────────────

def record_dispute(session_id: str, item: dict, bureau: str, tier: int,
                   theory: str = "", state: str = "") -> None:
    """
    Log that a dispute went out. Outcome is unknown at this point.

    Called at mail time, not generation time — a letter that was never sent
    teaches us nothing and would bias the denominator.
    """
    case_hash = _h("case", session_id)
    item_hash = _h("item", session_id, str(item.get("account", "")), str(item.get("target", "")))

    with _lock, _conn() as c:
        c.execute("""
            INSERT OR IGNORE INTO dispute_outcomes
              (case_hash, item_hash, created_at, category, theory, bureau, tier,
               item_age_days, balance_band, is_debt_buyer, state)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            case_hash, item_hash, datetime.now(timezone.utc).isoformat(),
            item.get("bucket") or item.get("category") or "unknown",
            theory, bureau, int(tier or 1),
            _age_days(item.get("dofd") or item.get("opened")),
            _balance_band(item.get("amount")),
            1 if item.get("bucket") == "debt_buyer" else 0,
            (state or "")[:2],
        ))


def record_result(session_id: str, item: dict, bureau: str, outcome: str,
                  tier: int = 1, source: str = "consumer_reported") -> bool:
    """
    Close the loop: what actually happened to this item.

    outcome: deleted | verified | updated | no_response
    """
    if outcome not in ("deleted", "verified", "updated", "no_response"):
        raise ValueError(f"Unknown outcome: {outcome}")

    case_hash = _h("case", session_id)
    item_hash = _h("item", session_id, str(item.get("account", "")), str(item.get("target", "")))
    now = datetime.now(timezone.utc)

    with _lock, _conn() as c:
        row = c.execute(
            "SELECT created_at FROM dispute_outcomes WHERE case_hash=? AND item_hash=? AND tier=?",
            (case_hash, item_hash, tier),
        ).fetchone()
        if not row:
            return False

        try:
            started = datetime.fromisoformat(row["created_at"])
            days = (now - started).days
        except (ValueError, TypeError):
            # Unparseable or absent created_at: record the outcome without a
            # day count rather than losing the outcome itself.
            days = None

        c.execute("""
            UPDATE dispute_outcomes
               SET outcome=?, resolved_at=?, days_to_resolve=?, source=?
             WHERE case_hash=? AND item_hash=? AND tier=?
        """, (outcome, now.isoformat(), days, source, case_hash, item_hash, tier))
    return True


def record_score(session_id: str, bureau: str, before: int, after: int,
                 items_removed: int = 0, days_elapsed: int = 0) -> None:
    """
    A consumer voluntarily told us their score moved.

    Self-reported and unverified. Useful in aggregate, meaningless alone,
    and never to be shown back to a different consumer as a forecast.
    """
    with _lock, _conn() as c:
        c.execute("""
            INSERT INTO score_reports
              (case_hash, reported_at, bureau, score_before, score_after,
               items_removed, days_elapsed, source)
            VALUES (?,?,?,?,?,?,?,'consumer_reported')
        """, (_h("case", session_id), datetime.now(timezone.utc).isoformat(),
              bureau, int(before), int(after), int(items_removed), int(days_elapsed)))


# ── Reading ─────────────────────────────────────────────────────────────────

def removal_rate(category: str = "", bureau: str = "", theory: str = "",
                 tier: int | None = None) -> dict:
    """
    Observed deletion rate for a slice of history.

    Returns `{"n": …, "deleted": …, "rate": …, "confident": bool}`. Below
    MIN_SAMPLE_FOR_RATE, `rate` is None — a rate computed from four disputes
    is a rumour with a decimal point.
    """
    where, args = ["outcome IS NOT NULL"], []
    for col, val in (("category", category), ("bureau", bureau), ("theory", theory)):
        if val:
            where.append(f"{col}=?"); args.append(val)
    if tier is not None:
        where.append("tier=?"); args.append(tier)

    sql = f"""SELECT COUNT(*) n,
                     SUM(CASE WHEN outcome='deleted' THEN 1 ELSE 0 END) deleted,
                     AVG(days_to_resolve) avg_days
                FROM dispute_outcomes WHERE {' AND '.join(where)}"""

    with _lock, _conn() as c:
        r = c.execute(sql, args).fetchone()

    n = r["n"] or 0
    deleted = r["deleted"] or 0
    return {
        "n": n,
        "deleted": deleted,
        "rate": round(deleted / n, 3) if n >= MIN_SAMPLE_FOR_RATE else None,
        "avg_days_to_resolve": round(r["avg_days"], 1) if r["avg_days"] else None,
        "confident": n >= MIN_SAMPLE_FOR_RATE,
        "min_sample": MIN_SAMPLE_FOR_RATE,
    }


def theory_leaderboard(min_n: int = MIN_SAMPLE_FOR_RATE) -> list[dict]:
    """
    Which arguments actually work, ranked. This is the feedback loop that
    makes the letter engine better with every case.
    """
    with _lock, _conn() as c:
        rows = c.execute("""
            SELECT theory, bureau, COUNT(*) n,
                   SUM(CASE WHEN outcome='deleted' THEN 1 ELSE 0 END) deleted
              FROM dispute_outcomes
             WHERE outcome IS NOT NULL AND theory != ''
          GROUP BY theory, bureau
            HAVING n >= ?
          ORDER BY (CAST(deleted AS FLOAT)/n) DESC
        """, (min_n,)).fetchall()

    return [{
        "theory": r["theory"], "bureau": r["bureau"],
        "n": r["n"], "deleted": r["deleted"],
        "rate": round(r["deleted"] / r["n"], 3),
    } for r in rows]


def score_deltas(min_n: int = MIN_SAMPLE_FOR_RATE) -> dict:
    """
    The observed distribution of self-reported score movement.

    Deliberately returns median and quartiles rather than a mean, and always
    returns `n` alongside — so the figure cannot be quoted without the sample
    size that qualifies it. Below `min_n` it refuses to summarise at all.
    """
    with _lock, _conn() as c:
        rows = c.execute("""
            SELECT score_after - score_before AS delta, items_removed
              FROM score_reports
             WHERE score_before IS NOT NULL AND score_after IS NOT NULL
        """).fetchall()

    deltas = [r["delta"] for r in rows]
    if len(deltas) < min_n:
        return {
            "n": len(deltas), "sufficient": False,
            "note": (f"{len(deltas)} self-reported observations — too few to summarise. "
                     f"Need {min_n}."),
        }

    deltas.sort()
    q = statistics.quantiles(deltas, n=4) if len(deltas) >= 4 else [None, None, None]
    return {
        "n": len(deltas),
        "sufficient": True,
        "median": statistics.median(deltas),
        "q1": q[0], "q3": q[2],
        "min": deltas[0], "max": deltas[-1],
        "caveat": ("Self-reported by consumers, unverified, and confounded by "
                   "other activity on their files. An observed historical range, "
                   "not a prediction for any individual."),
    }


def training_export() -> list[dict]:
    """
    The full de-identified feature set, for fitting a model offline.

    Every column here is a category, a bucket or a count. There is no route
    back to a person, so this can be exported and modelled freely.
    """
    with _lock, _conn() as c:
        rows = c.execute("""
            SELECT category, theory, bureau, tier, item_age_days, balance_band,
                   is_debt_buyer, state, outcome, days_to_resolve
              FROM dispute_outcomes WHERE outcome IS NOT NULL
        """).fetchall()
    return [dict(r) for r in rows]


def ledger_stats() -> dict:
    """Headline numbers for the admin panel."""
    with _lock, _conn() as c:
        total = c.execute("SELECT COUNT(*) n FROM dispute_outcomes").fetchone()["n"]
        resolved = c.execute(
            "SELECT COUNT(*) n FROM dispute_outcomes WHERE outcome IS NOT NULL").fetchone()["n"]
        scores = c.execute("SELECT COUNT(*) n FROM score_reports").fetchone()["n"]

    return {
        "disputes_logged": total,
        "outcomes_known": resolved,
        "awaiting_outcome": total - resolved,
        "score_reports": scores,
        "ready_to_model": resolved >= MIN_SAMPLE_FOR_RATE,
        "min_sample": MIN_SAMPLE_FOR_RATE,
    }
