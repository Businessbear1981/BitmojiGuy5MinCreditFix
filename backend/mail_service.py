"""
Mail integration via Lob API — printing, stuffing, and USPS mailing with
tracking. Webhooks notify us of delivery status.

Postage ladder (product design, confirmed w/ Sean):
  round 1        -> First Class
  round 2 (d30)  -> Certified
  round 3 (d60)  -> Certified + Return Receipt
  round 4 (d90+) -> Certified + Return Receipt (+ CFPB/FTC escalation letters)
Follow-up rounds are the customer re-running the flow; the round number is
passed per send.

Set these env vars:
  LOB_API_KEY       - your Lob API key (test or live)
  LOB_WEBHOOK_SECRET - webhook signature secret from Lob dashboard

Docs: https://docs.lob.com/
"""
import hashlib
import hmac
import os
from datetime import datetime, timezone

import httpx

from config import IS_PROD

LOB_API_KEY = os.environ.get("LOB_API_KEY", "")
LOB_BASE_URL = "https://api.lob.com/v1"
LOB_WEBHOOK_SECRET = os.environ.get("LOB_WEBHOOK_SECRET", "")

# The ladder now lives with the letters that depend on it, so the legal
# escalation and the postage escalation can never drift apart.
from dispute_engine.tiers import TIER_LADDER, postage_for_tier

# round number -> Lob extra_service (None = plain First Class)
POSTAGE_LADDER = {t: spec["extra_service"] for t, spec in TIER_LADDER.items()}

BUREAU_ADDRESSES = {
    "Experian": {
        "name": "Experian Disputes",
        "address_line1": "P.O. Box 4500",
        "address_city": "Allen",
        "address_state": "TX",
        "address_zip": "75013",
    },
    "Equifax": {
        "name": "Equifax Information Services",
        "address_line1": "P.O. Box 740241",
        "address_city": "Atlanta",
        "address_state": "GA",
        "address_zip": "30374-0241",
    },
    "TransUnion": {
        "name": "TransUnion Consumer Solutions",
        "address_line1": "P.O. Box 2000",
        "address_city": "Chester",
        "address_state": "PA",
        "address_zip": "19016-2000",
    },
}


def send_letter(
    client_name: str,
    client_address: str,
    target: str,
    letter_html: str,
    session_id: str,
    round_number: int = 1,
    client_city: str = "",
    client_state: str = "",
    client_zip: str = "",
) -> dict | None:
    """
    Send a letter via Lob, with postage escalating by dispute round.
    Returns Lob letter object with tracking info, or None if not configured.
    """
    if not LOB_API_KEY:
        print("WARN: LOB_API_KEY not set, skipping mail")
        return None

    to_addr = BUREAU_ADDRESSES.get(target)
    if not to_addr:
        print(f"WARN: No address for target '{target}', skipping")
        return None

    # City / state / ZIP arrive as discrete fields, collected as discrete
    # boxes at intake. They used to be recovered by splitting the free-text
    # address on commas, which put "Apt 3B" in the city field and "Austin" in
    # the state field for any address with a unit number, and produced four
    # empty fields for an address typed without commas. Lob rejected those,
    # the 4xx was swallowed, and the customer was told the mail had gone.
    address_line1 = (client_address or "").strip()
    city = (client_city or "").strip()
    state = (client_state or "").strip().upper()
    zip_code = (client_zip or "").strip()

    missing = [n for n, v in (("city", city), ("state", state), ("zip", zip_code))
               if not v]
    if missing:
        # Refuse rather than hand Lob a payload it will reject silently.
        print(f"WARN: cannot mail to {target} — missing {', '.join(missing)}")
        return None

    payload = {
        "description": f"AE CreditFix dispute r{round_number} - {session_id[:8]} -> {target}",
        "to": to_addr,
        "from": {
            "name": client_name,
            "address_line1": address_line1,
            "address_city": city,
            "address_state": state,
            "address_zip": zip_code,
        },
        "file": letter_html,
        "color": False,
        "metadata": {
            "session_id": session_id,
            "target": target,
            "round": str(round_number),
        },
    }
    # mail_type / return_envelope / extra_service all come from the tier.
    payload.update(postage_for_tier(round_number))

    try:
        resp = httpx.post(
            f"{LOB_BASE_URL}/letters",
            json=payload,
            auth=(LOB_API_KEY, ""),
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        return {
            "lob_id": result.get("id"),
            "target": target,
            "tracking_number": result.get("tracking_number"),
            "expected_delivery": result.get("expected_delivery_date"),
            "status": "mailed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:  # noqa: BLE001 - boundary must degrade, not crash; type logged
        print(f"Lob API error: {type(e).__name__}")
        return None


def send_all_letters(
    client_name: str,
    client_address: str,
    letters: list,
    session_id: str,
    round_number: int = 1,
    client_city: str = "",
    client_state: str = "",
    client_zip: str = "",
) -> list:
    """
    Send all dispute letters via Lob.

    Returns (results, skipped): the tracking entries for what was actually
    accepted, and one entry per letter that was not sent with the reason.
    A partial send used to be indistinguishable from a full one — three
    letters generated, two mailed, and the case still reported "sent".
    """
    results = []
    skipped = []
    for ltr in letters:
        target = ltr.get("target", "")
        text = ltr.get("text", "")
        # Convert plain text to simple HTML for Lob
        html = f"<html><body><pre style='font-family:Courier;font-size:11pt;'>{text}</pre></body></html>"
        result = send_letter(
            client_name, client_address, target, html, session_id, round_number,
            client_city=client_city, client_state=client_state, client_zip=client_zip,
        )
        if result:
            results.append(result)
        else:
            skipped.append({"target": target, "reason": "not accepted by the mail carrier"})
    return results, skipped


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Lob webhook signature. Fails closed in production."""
    if not LOB_WEBHOOK_SECRET:
        # Without a secret we cannot verify anything: reject in production,
        # allow only for local development.
        return not IS_PROD
    expected = hmac.new(
        LOB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
