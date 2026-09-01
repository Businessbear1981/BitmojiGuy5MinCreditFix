"""
The Watcher — the 30/60/90-day clock, and what it is allowed to promise.

The dispute ladder in `dispute_engine/tiers.py` already defines the sequence:
tier 1 opens the dispute, tier 2 demands the method of verification at day 30,
tier 3 gives pre-litigation notice at day 60, tier 4 escalates to regulators at
day 90. The Watcher is the thing that remembers those dates on the consumer's
behalf and puts the next round in their hands when it comes due.

Everything below exists to make that honest. Four things had to be settled
before any of it could ship:

── 1. The clock starts on receipt, not on dispatch ────────────────────────

§ 1681i(a)(1)(A) gives the bureau thirty days from *receipt* of the dispute.
The old frontend counted from `created_at` — the moment the consumer filled in
a form, which can be days before anything is mailed and weeks before it lands.
That overstates progress and would have had people sending a
"you missed your deadline" letter while the bureau was still inside it.

So: count from the delivery date when the mail carrier gave us one, and from
dispatch plus a transit allowance when it did not. `basis` says which, on
every milestone, and the UI is expected to show it. A deadline the consumer
cannot check the derivation of is a deadline they cannot rely on.

── 2. A 90-day tracker cannot live on a 24-hour purge ─────────────────────

`cleanup.py` hard-deletes every case older than `SESSION_TTL_HOURS`. That is
the right default and it is what the privacy page promises. It also makes a
90-day product impossible, because the case is gone long before day 30.

The resolution is not to weaken the default. It is that subscribing to the
Watcher is the consumer choosing, explicitly, to have their case retained for
the length of the tracking window — and being told so in those words before
they pay. `retention_notice()` is that sentence, `retain_until` is the field
it maps to, and `cleanup.py` honours it. A consumer who does not subscribe is
purged in 24 hours exactly as before.

── 3. We can only notify where we can actually deliver ────────────────────

The page offers Email, Snapchat, TikTok and Instagram. Only one of those can
be delivered: there is no API that lets an application send an unsolicited
direct message to a Snapchat, TikTok or Instagram user, and there is not going
to be one. Offering a reminder channel that silently never fires is worse than
not offering it, because the consumer stops watching their own calendar.

`available_channels()` reports what can actually be delivered and why the
others cannot. The UI shows the rest as unavailable rather than hiding them,
so someone who wants Instagram reminders knows we heard them and knows why the
answer is no.

── 4. Nothing here predicts an outcome ────────────────────────────────────

A milestone says a statutory period has elapsed. It does not say the consumer
has won, that a deletion is due, or that they have a case worth money. Day 90
means the regulatory escalation round is available to send — not that anyone
owes anyone $1,000. The copy in `MILESTONES` is written to that line.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from dispute_engine.tiers import TIER_LADDER

# How long to allow for first-class mail to arrive, when the carrier never
# reported a delivery date. Deliberately generous: counting the clock as
# starting later than it did is the safe direction to be wrong in, because it
# delays the next letter rather than sending it prematurely.
ASSUMED_TRANSIT_DAYS = 5

# Days past the last tier to keep the case before it is purged. Long enough to
# send the tier-4 round and receive an answer to it.
RETENTION_TAIL_DAYS = 45


# ── Notification channels ───────────────────────────────────────────────────

CHANNELS = {
    "email": {
        "value": "email",
        "label": "Email",
        "icon": "✉",
        "available": True,
        "placeholder": "your@email.com",
        "note": "",
    },
    "snapchat": {
        "value": "snapchat",
        "label": "Snapchat",
        "icon": "\U0001F47B",
        "available": False,
        "placeholder": "@yoursnapchathandle",
        "note": "Snapchat has no way for an app to message you unless you "
                "start the conversation, so we cannot deliver a reminder here. "
                "We would rather say so than take your money for a reminder "
                "that never arrives.",
    },
    "tiktok": {
        "value": "tiktok",
        "label": "TikTok",
        "icon": "\U0001F3B5",
        "available": False,
        "placeholder": "@yourtiktokhandle",
        "note": "TikTok does not allow applications to send direct messages, "
                "so a reminder here would never reach you.",
    },
    "instagram": {
        "value": "instagram",
        "label": "Instagram",
        "icon": "\U0001F4F7",
        "available": False,
        "placeholder": "@yourinstagramhandle",
        "note": "Instagram only permits business messaging to people who "
                "message first, so we cannot start a reminder thread with you.",
    },
}


def available_channels() -> list[dict]:
    """Every channel, with the unavailable ones carrying their reason."""
    return list(CHANNELS.values())


def validate_handle(method: str, handle: str) -> tuple[bool, str]:
    """(ok, error). Rejects a channel we cannot deliver on, by name."""
    channel = CHANNELS.get(method)
    if not channel:
        return False, "Choose a notification method."
    if not channel["available"]:
        return False, channel["note"]

    handle = (handle or "").strip()
    if method == "email":
        if "@" not in handle or "." not in handle.split("@")[-1] or len(handle) < 6:
            return False, "Enter a valid email address."
        if len(handle) > 254:
            return False, "That email address is too long."
    return True, ""


# ── Milestones ──────────────────────────────────────────────────────────────
# One per tier past the opening round. Wording states what becomes *available*,
# never what the consumer is owed.

MILESTONES = {
    30: {
        "day": 30,
        "tier": 2,
        "title": "First Response Window",
        "statute": "15 U.S.C. § 1681i(a)(1)(A)",
        "body": "The bureau has 30 days from receiving your dispute to complete "
                "its reinvestigation. Once that has passed, the method-of-"
                "verification round becomes available — it asks how the item was "
                "verified, by whom, and with what documents.",
        "on_reach": "Your day-30 letters are ready to generate.",
    },
    60: {
        "day": 60,
        "tier": 3,
        "title": "Escalation Checkpoint",
        "statute": "15 U.S.C. §§ 1681n, 1681o",
        "body": "If the response was boilerplate, absent, or did not answer how "
                "the item was verified, the pre-litigation round puts the bureau "
                "on notice of negligent and willful noncompliance. Send it "
                "certified.",
        "on_reach": "Your day-60 letters are ready to generate.",
    },
    90: {
        "day": 90,
        "tier": 4,
        "title": "Regulatory Escalation",
        "statute": "12 U.S.C. § 5493(b)(3)",
        "body": "The regulatory round copies the CFPB, the FTC and your state "
                "Attorney General. Filing a complaint is free and you do not "
                "need a lawyer to do it. Whether you have a claim worth bringing "
                "is a question for an attorney — this platform does not assess "
                "that and cannot.",
        "on_reach": "Your day-90 letters and complaint pack are ready.",
    },
}


def _delivery_date(mail_tracking: Optional[list]) -> Optional[datetime]:
    """
    The latest confirmed delivery across the mailed letters, if any.

    The latest, not the earliest: the clock the consumer cares about is the one
    that finishes last, because a letter still in transit has not started its
    thirty days. Being early with a follow-up is the failure mode to avoid.
    """
    dates = []
    for entry in (mail_tracking or []):
        if not isinstance(entry, dict):
            continue
        raw = entry.get("delivered_at") or entry.get("delivery_date")
        if not raw:
            continue
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dates.append(datetime.strptime(str(raw)[:len(fmt) + 2].strip()[:19], fmt))
                break
            except ValueError:
                continue
    return max(dates) if dates else None


def clock_start(record) -> dict:
    """
    When the statutory clock began, and how confidently we know it.

    Returns `start`, a `basis` string for the UI, and `confirmed`, so a screen
    can style an assumed date differently from a carrier-confirmed one.
    """
    delivered = _delivery_date(getattr(record, "mail_tracking", None))
    if delivered:
        return {
            "start": delivered,
            "basis": f"counted from confirmed delivery on "
                     f"{delivered.strftime('%b %d, %Y')}",
            "confirmed": True,
        }

    dispatched = getattr(record, "mail_dispatched_at", None)
    if dispatched:
        start = dispatched + timedelta(days=ASSUMED_TRANSIT_DAYS)
        return {
            "start": start,
            "basis": f"mailed {dispatched.strftime('%b %d, %Y')}; delivery not "
                     f"yet confirmed, so we allow {ASSUMED_TRANSIT_DAYS} days "
                     f"transit before starting the count",
            "confirmed": False,
        }

    return {
        "start": None,
        "basis": "nothing mailed yet — the clock starts when the bureau "
                 "receives your letters",
        "confirmed": False,
    }


def milestones_for(record, now: Optional[datetime] = None) -> dict:
    """
    Every milestone with its real date, keyed `day_30` / `day_60` / `day_90`.

    `reached` is a fact about the calendar and nothing else. It does not mean
    the bureau failed, and it does not mean the consumer should send anything
    — it means the next round has become available to send.
    """
    now = now or datetime.utcnow()
    clock = clock_start(record)
    start = clock["start"]
    rounds_sent = set(getattr(record, "watcher_rounds", None) or [])

    out = {}
    for day, spec in MILESTONES.items():
        if start is None:
            out[f"day_{day}"] = {
                **spec,
                "date": "",
                "days_remaining": day,
                "reached": False,
                "letter_sent": spec["tier"] in rounds_sent,
                "basis": clock["basis"],
                "clock_confirmed": False,
            }
            continue

        due = start + timedelta(days=day)
        remaining = max(0, (due - now).days)
        out[f"day_{day}"] = {
            **spec,
            "date": due.strftime("%Y-%m-%d"),
            "days_remaining": remaining,
            "reached": now >= due,
            "letter_sent": spec["tier"] in rounds_sent,
            "basis": clock["basis"],
            "clock_confirmed": clock["confirmed"],
        }
    return out


def due_tier(record, now: Optional[datetime] = None) -> int:
    """
    The highest tier whose date has passed. 1 when nothing is due yet.

    Deliberately not `dispute_engine.tier_for_day`: that helper counts from a
    raw day number, and this has to count from the receipt-based clock.
    """
    now = now or datetime.utcnow()
    start = clock_start(record)["start"]
    if start is None:
        return 1
    elapsed = (now - start).days
    due = 1
    for tier, spec in sorted(TIER_LADDER.items()):
        if elapsed >= spec["day"]:
            due = tier
    return due


def can_generate(record, day: int, now: Optional[datetime] = None) -> tuple[bool, str, int]:
    """
    May the consumer pull the round for this milestone yet? (ok, reason, tier)

    Refusing early is the point. A method-of-verification letter sent on day 12
    tells the bureau the sender does not know the statute, and it is the kind
    of mistake that gets a whole file treated as frivolous.
    """
    spec = MILESTONES.get(day)
    if not spec:
        return False, "Unknown milestone.", 0

    ms = milestones_for(record, now).get(f"day_{day}", {})
    if not ms.get("date"):
        return False, ("Nothing has been mailed yet, so the clock has not "
                       "started. Send your first round from the Gate."), spec["tier"]
    if not ms.get("reached"):
        return False, (f"{ms['days_remaining']} days left. The bureau is still "
                       f"inside its statutory window — sending this now would "
                       f"undercut it."), spec["tier"]
    return True, "", spec["tier"]


# ── Retention ───────────────────────────────────────────────────────────────

def retention_until(record, now: Optional[datetime] = None) -> datetime:
    """How long a subscribed case must survive: last milestone plus a tail."""
    now = now or datetime.utcnow()
    start = clock_start(record)["start"] or now
    return start + timedelta(days=max(MILESTONES) + RETENTION_TAIL_DAYS)


def retention_notice(record=None) -> str:
    """
    The sentence the consumer must see *before* subscribing.

    Without the Watcher their case is destroyed in 24 hours, which is the
    promise the privacy page makes. Subscribing is them choosing to override
    that for themselves. They cannot consent to it if nobody says it plainly.
    """
    total = max(MILESTONES) + RETENTION_TAIL_DAYS
    return (
        f"Tracking your deadlines means keeping your case. Without the Watcher, "
        f"everything you uploaded is destroyed within 24 hours. If you turn the "
        f"Watcher on, we keep your encrypted case for about {total} days so the "
        f"day-30, day-60 and day-90 rounds can be built from it — then it is "
        f"destroyed on the same schedule as everything else. You can cancel at "
        f"any time, and cancelling deletes it immediately."
    )


# ── Status payload ──────────────────────────────────────────────────────────

def status_payload(record, now: Optional[datetime] = None) -> dict:
    """
    Everything the Watcher screen renders, in one shape.

    Kept in the backend rather than assembled in the browser so the milestone
    arithmetic has exactly one implementation. The frontend had its own; the
    two disagreed, and the frontend's was the wrong one.
    """
    now = now or datetime.utcnow()
    clock = clock_start(record)
    subscribed = bool(getattr(record, "watcher_subscribed", False))
    start = clock["start"]

    return {
        "dispatched": bool(getattr(record, "mail_sent", False)),
        "subscribed": subscribed,
        "dispatched_at": (record.mail_dispatched_at.isoformat()
                          if getattr(record, "mail_dispatched_at", None) else None),
        "days_since_dispatch": ((now - start).days if start else 0),
        "clock_basis": clock["basis"],
        "clock_confirmed": clock["confirmed"],
        "milestones": milestones_for(record, now),
        "due_tier": due_tier(record, now),
        "rounds_generated": sorted(getattr(record, "watcher_rounds", None) or []),
        "notify_method": getattr(record, "watcher_notify_method", None),
        "notify_handle": getattr(record, "watcher_notify_handle", None),
        "notifications_sent": getattr(record, "watcher_notifications", None) or [],
        "confirmation": next(
            (t.get("tracking_number", "") for t in (record.mail_tracking or [])
             if isinstance(t, dict) and t.get("tracking_number")), ""),
        "letter_count": len(record.letters or []),
        "channels": available_channels(),
        "retention_notice": retention_notice(record),
        "retain_until": (record.watcher_retain_until.isoformat()
                         if getattr(record, "watcher_retain_until", None) else None),
        # Said out loud on the screen, not buried in terms. A tracker that
        # counts days is not a tracker that knows what the bureau decided.
        "scope_note":
            "The Watcher tracks dates, not decisions. It knows when each "
            "statutory window closes and builds the next round when one does. "
            "It cannot see the bureau's response — you tell us what came back, "
            "and nothing here predicts whether an item will be removed.",
    }
