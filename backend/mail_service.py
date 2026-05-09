"""
Certified mail integration via Lob API.
Lob handles printing, stuffing, and mailing letters via USPS Certified Mail
with tracking. Webhooks notify us of delivery status.

Set these env vars:
  LOB_API_KEY       - your Lob API key (test or live)
  LOB_WEBHOOK_SECRET - webhook signature secret from Lob dashboard

Docs: https://docs.lob.com/
"""
import os
import json
import hmac
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

LOB_API_KEY = os.environ.get("LOB_API_KEY", "")
LOB_BASE_URL = "https://api.lob.com/v1"
LOB_WEBHOOK_SECRET = os.environ.get("LOB_WEBHOOK_SECRET", "")

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


def send_certified_letter(
    client_name: str,
    client_address: str,
    target: str,
    letter_html: str,
    session_id: str,
) -> Optional[dict]:
    """
    Send a letter via Lob Certified Mail.
    Returns Lob letter object with tracking info, or None if not configured.
    """
    if not LOB_API_KEY:
        print("WARN: LOB_API_KEY not set, skipping certified mail")
        return None

    to_addr = BUREAU_ADDRESSES.get(target)
    if not to_addr:
        print(f"WARN: No address for target '{target}', skipping")
        return None

    # Parse client address into components (simple split)
    addr_parts = [p.strip() for p in client_address.split(",")]
    address_line1 = addr_parts[0] if addr_parts else client_address
    city = addr_parts[1] if len(addr_parts) > 1 else ""
    state_zip = addr_parts[2].strip().split(" ") if len(addr_parts) > 2 else ["", ""]
    state = state_zip[0] if state_zip else ""
    zip_code = state_zip[1] if len(state_zip) > 1 else ""

    payload = {
        "description": f"AE CreditFix dispute - {session_id[:8]} -> {target}",
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
        "mail_type": "usps_first_class",
        "extra_service": "certified",
        "return_envelope": True,
        "metadata": {
            "session_id": session_id,
            "target": target,
        },
    }

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
            "created_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"Lob API error: {e}")
        return None


def send_all_letters(
    client_name: str,
    client_address: str,
    letters: list,
    session_id: str,
) -> list:
    """Send all dispute letters via certified mail. Returns list of tracking results."""
    results = []
    for ltr in letters:
        target = ltr.get("target", "")
        text = ltr.get("text", "")
        # Convert plain text to simple HTML for Lob
        html = f"<html><body><pre style='font-family:Courier;font-size:11pt;'>{text}</pre></body></html>"
        result = send_certified_letter(client_name, client_address, target, html, session_id)
        if result:
            results.append(result)
    return results


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Lob webhook signature."""
    if not LOB_WEBHOOK_SECRET:
        return True  # Skip verification if no secret configured
    expected = hmac.new(
        LOB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
