"""
Consumer e-signature — capture, validate, and render onto letters.

Closes the loop that was open: the consumer signs once, in the browser,
and every letter in their packet goes out already signed. Nobody has to
post anything back.

What this is *not*: a qualified electronic signature under eIDAS, or a
notarised mark. It is a captured signature image plus an intent record —
which is what E-SIGN (15 U.S.C. § 7001) and UETA contemplate for exactly
this kind of consumer transaction, and considerably more than the bureaus
require. A § 611 dispute needs no wet signature at all; the bureaus'
own portals accept disputes with none. The signature is here because a
signed letter is taken more seriously, and because the consumer should
feel they authored the thing going out in their name.

Stored as a PNG data URL in an encrypted column, purged with the rest of
the case at 24 hours.
"""
from __future__ import annotations

import base64
import re
from datetime import datetime, timezone
from io import BytesIO

# A signature should be a few KB of strokes. Anything much larger is either
# a pasted photograph or someone probing the endpoint.
MAX_SIGNATURE_BYTES = 400_000
MIN_SIGNATURE_BYTES = 200

_DATA_URL = re.compile(r"^data:image/png;base64,([A-Za-z0-9+/=\s]+)$")


class SignatureError(ValueError):
    """Raised when a submitted signature cannot be accepted."""


def decode_signature(data_url: str) -> bytes:
    """
    Validate a canvas data URL and return raw PNG bytes.

    Rejects anything that is not a PNG data URL, is implausibly small (an
    accidental tap rather than a signature), or is large enough to be an
    uploaded photo.
    """
    if not data_url or not isinstance(data_url, str):
        raise SignatureError("No signature was provided.")

    match = _DATA_URL.match(data_url.strip())
    if not match:
        raise SignatureError("Signature must be a PNG image from the signing pad.")

    try:
        raw = base64.b64decode(match.group(1), validate=True)
    except Exception:  # noqa: BLE001 - boundary must degrade, not crash; type logged
        raise SignatureError("Signature image could not be read.")

    if len(raw) < MIN_SIGNATURE_BYTES:
        raise SignatureError("That signature looks empty — please sign again.")
    if len(raw) > MAX_SIGNATURE_BYTES:
        raise SignatureError("Signature image is too large.")
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SignatureError("Signature must be a PNG image.")

    return raw


def signature_record(
    data_url: str,
    typed_name: str,
    client_ip: str = "",
    user_agent: str = "",
) -> dict:
    """
    Build the stored signature record.

    Carries the mark itself plus the surrounding intent evidence that makes
    an electronic signature meaningful: what they typed as their name, when
    they signed, and a truncated fingerprint of where from. E-SIGN turns on
    intent and attribution, not on the image.
    """
    raw = decode_signature(data_url)
    typed = (typed_name or "").strip()
    if len(typed) < 2:
        raise SignatureError("Type your full legal name to confirm the signature.")

    return {
        "png_b64": base64.b64encode(raw).decode(),
        "typed_name": typed[:120],
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "bytes": len(raw),
        # Attribution evidence, deliberately coarse: enough to show the
        # signature came from the consumer's own session, not enough to
        # become a tracking record.
        "ip_prefix": ".".join(client_ip.split(".")[:2]) if "." in client_ip else "",
        "agent": (user_agent or "")[:120],
    }


def signature_bytes(record: dict | None) -> BytesIO | None:
    """Return the stored signature as a stream ReportLab can draw, or None."""
    if not record or not record.get("png_b64"):
        return None
    try:
        return BytesIO(base64.b64decode(record["png_b64"]))
    except Exception:  # noqa: BLE001 - boundary must degrade, not crash; type logged
        return None


def attestation_line(record: dict | None) -> str:
    """
    The line printed beneath the signature on every letter.

    States plainly that the mark is an electronic signature and when it was
    made. A bureau clerk should never have to wonder whether the signature
    is genuine or what it represents.
    """
    if not record:
        return ""
    when = (record.get("signed_at") or "")[:19].replace("T", " ")
    return (
        f"Electronically signed by {record.get('typed_name', '')} on {when} UTC. "
        f"Signed under the Electronic Signatures in Global and National Commerce Act "
        f"(15 U.S.C. § 7001)."
    )
