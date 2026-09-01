"""
Calibration — turning priors into measurements, gradually.

`scoring.py` currently flips: below 25 observations it uses a prior, at 25 it
switches to the measured rate. That cliff is wrong in both directions. At
n=24 it ignores real evidence; at n=25 it throws away everything we believed
before and trusts a rate computed from 25 disputes as if it were fact.

The fix is a Beta-binomial. Express each prior as a Beta distribution with a
pseudo-count — "we believe 0.35, about as strongly as if we'd seen 20 cases"
— then every real outcome updates it:

    prior          Beta(α₀, β₀)      where α₀ = p·w, β₀ = (1-p)·w
    observe k of n  →  Beta(α₀+k, β₀+n-k)
    posterior mean  =  (α₀+k) / (α₀+β₀+n)

At n=0 that returns the prior exactly. At n=5 it has moved a little. At
n=500 the prior is irrelevant. No cliff, no arbitrary threshold, and the
credible interval tells you how much to trust it.

── Calibration, not just accuracy ─────────────────────────────────────────

A model that says "60%" should be right about 60% of the time. That is a
different question from whether it ranks items correctly, and it is the one
that matters when a number is shown to a consumer. `reliability()` bins
predictions and compares each bin's predicted rate to what actually
happened; `brier_score()` gives the single summary. Both need real outcomes
to mean anything, and both say so when they don't have them.

── What this deliberately does not do ─────────────────────────────────────

**No score prediction.** Not because the machinery couldn't carry it, but
because the inputs don't exist: FICO's weighting is a trade secret, the
score data we'd train on is self-reported by a handful of consumers, and a
number presented as "your score will rise 40 points" is the exact implied
outcome promise the disclosures exist to avoid.

The same Beta-binomial *would* work on score movement the day there is
honest data behind it — enough verified before/after pairs, from consumers
who reported both, with the confounds understood. `score_movement_readiness()`
below reports how far off that is rather than pretending it's here. Until it
returns ready, the answer to "how many points?" is the observed distribution
in `outcomes.score_deltas()`, with its sample size attached.
"""
from __future__ import annotations

import math
import sqlite3

import scoring

try:
    import outcomes
    HAS_OUTCOMES = True
except ImportError:
    HAS_OUTCOMES = False


# How strongly to hold a prior, in pseudo-observations. A prior weighted 20
# is worth 20 real cases: five outcomes nudge it, fifty overwrite it.
#
# Strong priors rest on statute (a closed reporting window is not a matter of
# opinion) so they hold harder. Weak ones are guesses and should yield fast.
PRIOR_WEIGHT = {"strong": 30.0, "moderate": 18.0, "weak": 8.0}

# Enough outcomes before we'll describe a rate as measured rather than modelled.
# Not a switch any more — only a labelling threshold.
MEASURED_LABEL_AT = 15


def beta_posterior(prior_p: float, weight: float,
                   successes: int, trials: int) -> dict:
    """
    Update a prior with observed outcomes.

    Returns the posterior mean, a 90% credible interval, and how much of the
    result is still coming from the prior — so a caller can tell the
    difference between "0.62, from 400 cases" and "0.62, mostly assumption".
    """
    a0 = max(prior_p * weight, 0.01)
    b0 = max((1.0 - prior_p) * weight, 0.01)

    a = a0 + successes
    b = b0 + (trials - successes)

    mean = a / (a + b)
    # Normal approximation to the Beta is adequate here and avoids a scipy
    # dependency; with a+b >= ~10 the error is well under the precision we
    # would ever display.
    var = (a * b) / (((a + b) ** 2) * (a + b + 1))
    sd = math.sqrt(var)

    return {
        "mean": round(mean, 4),
        "sd": round(sd, 4),
        "ci_low": round(max(0.0, mean - 1.645 * sd), 4),
        "ci_high": round(min(1.0, mean + 1.645 * sd), 4),
        "n": trials,
        "successes": successes,
        # 1.0 = entirely prior, 0.0 = entirely data.
        "prior_share": round((a0 + b0) / (a0 + b0 + trials), 3),
    }


def calibrated_probability(category: str, strength: str,
                           bureau: str = "") -> dict:
    """
    The probability this ground succeeds, blending prior and evidence.

    Drop-in replacement for `scoring.ground_probability()` that returns the
    full picture instead of a bare float.
    """
    prior_p = scoring.PRIORS.get(
        (category, strength),
        scoring.STRENGTH_FLOOR.get(strength, 0.10),
    )
    weight = PRIOR_WEIGHT.get(strength, 15.0)

    successes = trials = 0
    if HAS_OUTCOMES:
        try:
            obs = outcomes.removal_rate(category=category, bureau=bureau)
            trials = obs.get("n", 0) or 0
            successes = obs.get("deleted", 0) or 0
        except sqlite3.Error as e:
            # No observations readable: the posterior is then just the prior.
            print(f"[calibration] ledger unreadable ({type(e).__name__}); "
                  f"posterior for {category}/{strength} falls back to the prior")

    post = beta_posterior(prior_p, weight, successes, trials)
    post.update({
        "category": category,
        "strength": strength,
        "bureau": bureau,
        "prior": prior_p,
        "basis": ("measured" if trials >= MEASURED_LABEL_AT
                  else "blended" if trials > 0
                  else "prior"),
    })
    return post


def install_into_scoring() -> None:
    """
    Point `scoring.ground_probability` at the calibrated estimate.

    Monkey-patching rather than editing scoring.py keeps the noisy-OR module
    free of any dependency on the ledger — it stays testable with fixed
    numbers, and a deployment without an outcomes database behaves exactly
    as it did before.
    """
    def _calibrated(category: str, strength: str, bureau: str = ""):
        est = calibrated_probability(category, strength, bureau)
        label = est["basis"]
        if est["n"]:
            label += f" (n={est['n']}, prior {est['prior_share']:.0%})"
        return est["mean"], label

    scoring.ground_probability = _calibrated


# ── Is the model any good? ──────────────────────────────────────────────────

def brier_score(predictions: list[tuple[float, bool]]) -> dict:
    """
    Mean squared error between predicted probability and what happened.

    0 is perfect, 0.25 is what you get by always guessing 50%. Compare
    against the base rate: a Brier score no better than predicting the
    overall deletion rate for everything means the model is adding nothing.
    """
    if not predictions:
        return {"n": 0, "sufficient": False,
                "note": "no resolved predictions yet"}

    n = len(predictions)
    bs = sum((p - (1.0 if hit else 0.0)) ** 2 for p, hit in predictions) / n

    base = sum(1 for _, hit in predictions if hit) / n
    bs_base = sum((base - (1.0 if hit else 0.0)) ** 2 for _, hit in predictions) / n

    return {
        "n": n,
        "sufficient": n >= 30,
        "brier": round(bs, 4),
        "brier_baseline": round(bs_base, 4),
        "skill": round(1 - bs / bs_base, 3) if bs_base else 0.0,
        "base_rate": round(base, 3),
        "note": ("skill > 0 means the model beats predicting the base rate "
                 "for everything"),
    }


def reliability(predictions: list[tuple[float, bool]], bins: int = 5) -> list[dict]:
    """
    Are the numbers honest? Bin by predicted probability and compare.

    If the 0.6–0.8 bucket actually resolves at 0.45, the model is
    overconfident there and the priors in that range need pulling down. This
    is the diagnostic that tells you *where* it is wrong, not just that it is.
    """
    if not predictions:
        return []

    out = []
    for i in range(bins):
        lo, hi = i / bins, (i + 1) / bins
        rows = [(p, h) for p, h in predictions if lo <= p < hi or (i == bins - 1 and p == 1.0)]
        if not rows:
            continue
        pred = sum(p for p, _ in rows) / len(rows)
        act = sum(1 for _, h in rows if h) / len(rows)
        out.append({
            "range": f"{lo:.1f}–{hi:.1f}",
            "n": len(rows),
            "predicted": round(pred, 3),
            "actual": round(act, 3),
            "gap": round(act - pred, 3),
            "verdict": ("overconfident" if act < pred - 0.08
                        else "underconfident" if act > pred + 0.08
                        else "well calibrated"),
        })
    return out


def suggest_prior_updates(min_n: int = 40) -> list[dict]:
    """
    Where the evidence has moved far enough from the prior to rewrite it.

    Returns suggestions, not changes. A prior that has been contradicted by
    100 cases should be edited in `scoring.PRIORS` deliberately, with someone
    looking at it — not silently drifted by a background job.
    """
    if not HAS_OUTCOMES:
        return []

    suggestions = []
    for (category, strength), prior_p in scoring.PRIORS.items():
        try:
            obs = outcomes.removal_rate(category=category)
        except sqlite3.Error as e:
            print(f"[calibration] skipping {category}: ledger unreadable "
                  f"({type(e).__name__})")
            continue
        n = obs.get("n", 0) or 0
        if n < min_n or obs.get("rate") is None:
            continue

        measured = obs["rate"]
        drift = measured - prior_p
        if abs(drift) < 0.10:
            continue

        post = beta_posterior(prior_p, PRIOR_WEIGHT.get(strength, 15.0),
                              obs["deleted"], n)
        suggestions.append({
            "category": category,
            "strength": strength,
            "prior": prior_p,
            "measured": measured,
            "posterior": post["mean"],
            "n": n,
            "drift": round(drift, 3),
            "recommendation": (
                f"prior {prior_p:.2f} → {post['mean']:.2f} "
                f"({'over' if drift < 0 else 'under'}-estimated across {n} cases)"),
        })

    suggestions.sort(key=lambda s: -abs(s["drift"]))
    return suggestions


def model_status() -> dict:
    """One call for the admin panel: how much does this model actually know?"""
    if not HAS_OUTCOMES:
        return {"ledger": False, "note": "outcome ledger not available"}

    stats = outcomes.ledger_stats()
    board = outcomes.theory_leaderboard(min_n=MEASURED_LABEL_AT)

    cells_total = len(scoring.PRIORS)
    cells_measured = sum(
        1 for (cat, _s) in scoring.PRIORS
        if (outcomes.removal_rate(category=cat).get("n", 0) or 0) >= MEASURED_LABEL_AT
    )

    return {
        "ledger": True,
        "disputes_logged": stats["disputes_logged"],
        "outcomes_known": stats["outcomes_known"],
        "awaiting_outcome": stats["awaiting_outcome"],
        "cells_total": cells_total,
        "cells_measured": cells_measured,
        "coverage": round(cells_measured / cells_total, 3) if cells_total else 0.0,
        "measured_pairs": len(board),
        "stage": (
            "priors only" if stats["outcomes_known"] == 0 else
            "learning" if cells_measured < cells_total * 0.3 else
            "partly measured" if cells_measured < cells_total * 0.7 else
            "measured"
        ),
    }


def score_movement_readiness() -> dict:
    """
    How far from being able to say anything honest about score movement.

    Not a promise that we will. The gate is deliberately high: self-reported
    scores from a handful of consumers, confounded by everything else on
    their files, cannot support a per-person forecast no matter how good the
    arithmetic is. What enough data *would* support is a described
    distribution — "clients who removed a collection reported a median of X"
    — which is a statement about the past, not a prediction.
    """
    if not HAS_OUTCOMES:
        return {"ready": False, "reason": "no ledger"}

    deltas = outcomes.score_deltas()
    n = deltas.get("n", 0)

    NEEDED = 200
    return {
        "ready": False,
        "reports": n,
        "needed_for_distribution": NEEDED,
        "shortfall": max(0, NEEDED - n),
        "what_becomes_possible": (
            "an observed distribution of reported movement, with its sample "
            "size — never a per-person forecast"),
        "why_not_a_prediction": (
            "scores are self-reported and unverified; FICO's weighting is not "
            "published; and a number shown as an expected gain is an implied "
            "outcome promise"),
        "current": deltas,
    }
