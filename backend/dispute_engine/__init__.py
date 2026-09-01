"""
Dispute Engine — the merged letter generator.

    categories.py       every dispute type the platform recognises
    legal_library.py    verified statutes, case law, 50-state authorities
    analyst.py          violation theory matching against the facts
    letter_generator.py the seven-section letter composer
    tiers.py            the 4-round escalation ladder and its postage
    adapter.py          case model <-> engine model translation
    compose.py          the single entry point

Application code should import from `compose` and nothing else:

    from dispute_engine import generate_case_letters
"""

from .compose import engine_manifest, generate_case_letters
from .tiers import MAX_TIER, TIER_LADDER, ladder_summary, postage_for_tier, tier_for_day

__all__ = [
    "MAX_TIER",
    "TIER_LADDER",
    "engine_manifest",
    "generate_case_letters",
    "ladder_summary",
    "postage_for_tier",
    "tier_for_day",
]
