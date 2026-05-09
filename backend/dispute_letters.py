"""
AE 5-Min Credit Fix — Full Dispute Letter Library

Paste your complete letter templates below. Each letter maps to a
dispute bucket defined in buckets.py.

Format: Each letter is a dict with:
  - bucket: the bucket ID (collection, late_payment, charge_off, etc.)
  - subject: the Re: line
  - body: the full letter text (use {name}, {address}, {phone}, {email},
          {dob}, {ssn_last4}, {today}, {account}, {target}, {amount},
          {reason} as placeholders)
"""

# Paste your letter library content below this line:
LETTER_LIBRARY = [
    # Example format (replace with your actual letters):
    #
    # {
    #     "bucket": "collection",
    #     "subject": "Re: Demand for Investigation — Collection Account",
    #     "body": """...""",
    # },
]
