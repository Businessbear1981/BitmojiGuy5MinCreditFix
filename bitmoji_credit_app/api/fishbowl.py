"""
Trapdoor Fishbowl — zip-code-based workflow router.

For the beta launch (TX, CA, WA), incoming cases are routed into
regional "fishbowl" queues based on the user's zip code. This prevents
any single queue from being overloaded and lets us scale letter generation
and mailing by region.

Each fishbowl processes letters independently and can be rate-limited
separately.
"""
import re
from typing import Optional

# Beta regions: state -> zip prefix ranges
# TX: 750xx-799xx, CA: 900xx-961xx, WA: 980xx-994xx
BETA_REGIONS = {
    "TX": {"name": "Texas", "zip_prefixes": list(range(750, 800)), "queue_limit": 100},
    "CA": {"name": "California", "zip_prefixes": list(range(900, 962)), "queue_limit": 150},
    "WA": {"name": "Washington", "zip_prefixes": list(range(980, 995)), "queue_limit": 80},
}

# Active fishbowl queues (in-memory counters; in production, use Redis)
_fishbowl_counts = {state: 0 for state in BETA_REGIONS}


def extract_zip(address: str) -> Optional[str]:
    """Extract 5-digit zip code from an address string."""
    match = re.search(r"\b(\d{5})(?:-\d{4})?\b", address)
    return match.group(1) if match else None


def get_region(zip_code: str) -> Optional[str]:
    """Map a zip code to a beta region. Returns state code or None."""
    try:
        prefix = int(zip_code[:3])
    except (ValueError, IndexError):
        return None
    for state, config in BETA_REGIONS.items():
        if prefix in config["zip_prefixes"]:
            return state
    return None


def check_beta_eligibility(address: str) -> dict:
    """
    Check if an address is in a beta-eligible region.
    Returns eligibility status and region info.
    """
    zip_code = extract_zip(address)
    if not zip_code:
        return {
            "eligible": False,
            "reason": "Could not detect zip code from address",
            "zip": None,
            "region": None,
        }

    region = get_region(zip_code)
    if not region:
        return {
            "eligible": False,
            "reason": f"Zip code {zip_code} is not in a beta region (TX, CA, WA only)",
            "zip": zip_code,
            "region": None,
        }

    config = BETA_REGIONS[region]
    current_count = _fishbowl_counts.get(region, 0)

    if current_count >= config["queue_limit"]:
        return {
            "eligible": False,
            "reason": f"{config['name']} fishbowl is at capacity ({config['queue_limit']}). Try again shortly.",
            "zip": zip_code,
            "region": region,
            "queue_full": True,
        }

    return {
        "eligible": True,
        "zip": zip_code,
        "region": region,
        "region_name": config["name"],
        "queue_position": current_count + 1,
        "queue_limit": config["queue_limit"],
    }


def enter_fishbowl(region: str) -> int:
    """Add a case to a regional fishbowl. Returns queue position."""
    _fishbowl_counts[region] = _fishbowl_counts.get(region, 0) + 1
    return _fishbowl_counts[region]


def exit_fishbowl(region: str):
    """Remove a completed case from the fishbowl."""
    _fishbowl_counts[region] = max(0, _fishbowl_counts.get(region, 0) - 1)


def get_fishbowl_status() -> dict:
    """Get current status of all fishbowl queues."""
    status = {}
    for state, config in BETA_REGIONS.items():
        count = _fishbowl_counts.get(state, 0)
        status[state] = {
            "name": config["name"],
            "current": count,
            "limit": config["queue_limit"],
            "available": config["queue_limit"] - count,
            "utilization": round(count / config["queue_limit"] * 100, 1),
        }
    return status
