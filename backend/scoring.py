"""
Removal likelihood — combining independent grounds into one number.

An item disputed on three grounds comes off if *any* one of them holds. So
the arithmetic is not "pick the best argument", it is "what is the chance
they all fail":

    P(removed) = 1 - ∏(1 - pᵢ)

This is the noisy-OR. It captures the intuition directly: one ground at 30%,
one at 50%, one at 20% gives 1 - (0.70 × 0.50 × 0.80) = 0.72. Three
mediocre arguments beat one good one, which is exactly why the letter raises
every ground it can rather than leading with the strongest and stopping.

── Two honesty constraints ────────────────────────────────────────────────

**The priors below are assumptions, not measurements.** They encode how much
weight a ground *should* carry given what it rests on — a closed statutory
window is near-certain, a "please verify this" is not. They are starting
values, and every one of them is replaced by a measured rate from
`outcomes.py` as soon as that cell has enough observations. `explain()`
always says which of the two produced a number.

**Grounds are not fully independent.** The same clerk resolves all three on
the same afternoon with the same incentive. Treating them as independent
overstates the combination, so a correlation dampener pulls the result back
toward the strongest single ground. Without it, stacking six weak arguments
would "prove" a 95% chance of removal, which would be a lie with a decimal
point on it.
"""
from __future__ import annotations

import math
import sqlite3

try:
    import outcomes
    HAS_OUTCOMES = True
except ImportError:  # ledger module unavailable
    HAS_OUTCOMES = False

_LEDGER_WARNED = False


def _warn_ledger_unreadable(exc: sqlite3.Error) -> None:
    """Report an unreadable outcome ledger once per process, not per score."""
    global _LEDGER_WARNED
    if not _LEDGER_WARNED:
        _LEDGER_WARNED = True
        print(f"[scoring] outcome ledger unreadable ({type(exc).__name__}); "
              f"all probabilities are priors, not measurements")


# ── Priors ──────────────────────────────────────────────────────────────────
# Per (category, strength). Deliberately conservative: a bureau's default
# behaviour is to verify and move on, so anything short of a contradiction in
# their own record starts low.
#
# These are the model's beliefs before it has seen a single outcome. They are
# not claims about the industry and should not be quoted as such.
PRIORS: dict[tuple[str, str], float] = {
    # A closed reporting window is arithmetic, not argument.
    ("obsolete", "strong"):            0.82,
    ("obsolete", "moderate"):          0.35,

    # Dates that contradict each other in the bureau's own file.
    ("re_aging", "strong"):            0.48,
    ("re_aging", "moderate"):          0.26,

    # The furnisher must show it may report at all.
    ("improper_chain_of_ownership", "strong"):   0.40,
    ("debt_buyer", "moderate"):        0.30,
    ("collection", "moderate"):        0.24,

    ("mixed_file_indicators", "strong"):  0.55,
    ("identity_error", "strong"):      0.60,
    ("duplicate", "moderate"):         0.34,

    ("charge_off", "moderate"):        0.18,
    ("late_payment", "weak"):          0.11,
    ("balance_inaccuracy", "weak"):    0.14,
    ("status_inaccuracy", "moderate"): 0.22,
    ("student_loan", "moderate"):      0.16,
    ("inquiry", "moderate"):           0.20,
    ("personal_info", "moderate"):     0.45,
}

# Fallback when a (category, strength) pair has no prior of its own.
STRENGTH_FLOOR = {"strong": 0.40, "moderate": 0.20, "weak": 0.10}

# How much of the independence assumption to keep. 1.0 = fully independent
# (overstates), 0.0 = only the best ground counts (understates). 0.62 keeps
# real benefit from stacking while refusing to let six weak grounds imply
# near-certainty.
INDEPENDENCE = 0.62


def ground_probability(category: str, strength: str,
                       bureau: str = "") -> tuple[float, str]:
    """
    Probability this single ground succeeds, and where the number came from.

    Prefers a measured rate from the outcome ledger; falls back to the prior.
    Returns (p, source) so nothing can quote a number without knowing whether
    it was counted or assumed.
    """
    if HAS_OUTCOMES:
        try:
            obs = outcomes.removal_rate(category=category, bureau=bureau)
            if obs.get("confident") and obs.get("rate") is not None:
                return float(obs["rate"]), f"measured (n={obs['n']})"
        except sqlite3.Error as e:
            # The ledger is unreadable, so every number below is a prior, not a
            # measurement. Report it once rather than degrading silently: a
            # missing `dispute_outcomes` table means init_outcomes() was never
            # called, and no outcome has ever been recorded.
            _warn_ledger_unreadable(e)

    p = PRIORS.get((category, strength))
    if p is None:
        p = STRENGTH_FLOOR.get(strength, 0.10)
        return p, "prior (strength floor)"
    return p, "prior"


def combine(probabilities: list[float], independence: float = INDEPENDENCE) -> float:
    """
    Noisy-OR with a correlation dampener.

    Full independence would be `1 - ∏(1-p)`. The dampener interpolates
    between that and the single strongest ground, because the grounds are
    judged by the same reviewer under the same policy and do not fail
    independently in practice.
    """
    ps = [min(max(p, 0.0), 0.995) for p in probabilities if p > 0]
    if not ps:
        return 0.0
    if len(ps) == 1:
        return ps[0]

    independent = 1.0 - math.prod(1.0 - p for p in ps)
    best = max(ps)
    return best + (independent - best) * independence


def score_item(item: dict, bureau: str = "") -> dict:
    """
    Removal likelihood for one item, with the working shown.

    Returns every ground's individual probability, its source, the combined
    figure, and a plain-language band. The bands matter more than the decimal:
    a consumer should read "likely" or "worth trying", not "0.63".
    """
    cats = item.get("categories") or []
    if not cats and item.get("bucket"):
        cats = [{"category": item["bucket"], "strength": "moderate",
                 "evidence": item.get("reason", "")}]

    grounds = []
    for c in cats:
        p, source = ground_probability(c["category"], c["strength"], bureau)
        grounds.append({
            "category": c["category"],
            "strength": c["strength"],
            "p": round(p, 3),
            "source": source,
            "evidence": c.get("evidence", ""),
        })

    combined = combine([g["p"] for g in grounds])
    return {
        "grounds": grounds,
        "ground_count": len(grounds),
        "p_removed": round(combined, 3),
        "band": band(combined),
        "best_single": round(max((g["p"] for g in grounds), default=0.0), 3),
        "lift_from_stacking": round(
            combined - max((g["p"] for g in grounds), default=0.0), 3),
        "any_measured": any(g["source"].startswith("measured") for g in grounds),
    }


def band(p: float) -> str:
    """Plain language. The number is for ranking; this is for reading."""
    if p >= 0.65:
        return "strong"
    if p >= 0.40:
        return "likely"
    if p >= 0.20:
        return "worth trying"
    return "long shot"


def rank_items(items: list[dict], bureau: str = "") -> list[dict]:
    """
    Order the file by removal likelihood, heaviest first.

    This is what drives the review screen: the consumer sees which disputes
    have the best chance, not just which debts are largest. A $200 collection
    three grounds deep outranks a $9,000 charge-off with one weak angle.
    """
    scored = []
    for item in items:
        s = score_item(item, bureau)
        scored.append({**item, "scoring": s})
    scored.sort(key=lambda i: -i["scoring"]["p_removed"])
    return scored


def portfolio(items: list[dict], bureau: str = "") -> dict:
    """
    What to expect across the whole round.

    The expected count is the sum of per-item probabilities — the standard
    result for independent Bernoulli trials, and the honest way to answer
    "how many of these will come off?" without promising which ones.
    """
    scored = [score_item(i, bureau) for i in items]
    if not scored:
        return {"items": 0}

    ps = [s["p_removed"] for s in scored]
    expected = sum(ps)
    # Variance of a Poisson-binomial: Σ p(1-p).
    variance = sum(p * (1 - p) for p in ps)
    sd = math.sqrt(variance)

    return {
        "items": len(ps),
        "expected_removals": round(expected, 1),
        "range_low": max(0, round(expected - sd)),
        "range_high": min(len(ps), round(expected + sd)),
        "strong": sum(1 for s in scored if s["band"] == "strong"),
        "likely": sum(1 for s in scored if s["band"] == "likely"),
        "worth_trying": sum(1 for s in scored if s["band"] == "worth trying"),
        "long_shot": sum(1 for s in scored if s["band"] == "long shot"),
        "grounds_total": sum(s["ground_count"] for s in scored),
        "any_measured": any(s["any_measured"] for s in scored),
        "basis": ("measured from our own outcome history"
                  if any(s["any_measured"] for s in scored)
                  else "modelled priors — no measured history yet"),
    }


def explain(item: dict, bureau: str = "") -> str:
    """The arithmetic, written out. For the reviewer, and for the audit log."""
    s = score_item(item, bureau)
    name = item.get("furnisher") or item.get("target") or "Item"
    lines = [f"{name} — {s['ground_count']} independent grounds"]

    running = 1.0
    for g in s["grounds"]:
        running *= (1 - g["p"])
        lines.append(
            f"  {g['category']:<24} {g['strength']:<9} p={g['p']:.2f}  "
            f"[{g['source']}]  → all-fail so far {running:.3f}")

    lines.append(f"  {'':<24} {'':<9} " +
                 f"fully independent : {1 - running:.3f}")
    lines.append(f"  {'':<24} {'':<9} " +
                 f"dampened (ρ={INDEPENDENCE}) : {s['p_removed']:.3f}  → {s['band']}")
    lines.append(f"  best single ground {s['best_single']:.3f}; "
                 f"stacking adds {s['lift_from_stacking']:+.3f}")
    return "\n".join(lines)
