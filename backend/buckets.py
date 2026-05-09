"""
Dispute Buckets — predefined categories that map to specific FCRA
letter templates and legal citations.

Each bucket defines:
  - The dispute type (bureau vs creditor)
  - Which FCRA sections to cite
  - The letter body template
  - Keywords the AI scanner should look for
"""

DISPUTE_BUCKETS = {
    "collection": {
        "label": "Collection Account",
        "type": "bureau",
        "fcra_sections": ["609", "611"],
        "keywords": [
            "collection", "collections", "placed for collection",
            "sold to", "transferred to", "debt buyer",
            "assigned to", "purchased by",
        ],
        "reason_template": "This collection account is disputed. I have no contract with {target}. "
                           "Provide full validation including the original signed agreement, "
                           "complete payment history, and proof of assignment chain.",
        "letter_body": (
            "I am formally disputing the collection account listed below under {cit}. "
            "I do not recognize this debt and/or I have no contractual relationship with "
            "the collecting entity. Under FCRA §611, you must conduct a reasonable "
            "reinvestigation. If you cannot provide complete verification — including the "
            "original signed contract, full payment history, and proof of assignment — you "
            "must delete this tradeline within 30 days.\n\n"
            "Account: {account}\nCreditor/Collector: {target}\n"
            "Amount: {amount}\nReason: {reason}"
        ),
    },
    "late_payment": {
        "label": "Late Payment",
        "type": "bureau",
        "fcra_sections": ["609", "611"],
        "keywords": [
            "late payment", "30 days late", "60 days late", "90 days late",
            "120 days late", "past due", "delinquent", "delinquency",
        ],
        "reason_template": "Late payment reported on {account} is inaccurate. "
                           "I was never late on this account / the dates reported are incorrect.",
        "letter_body": (
            "I am disputing the late payment notation(s) on the account below under {cit}. "
            "The reported delinquency is inaccurate. I request that you reinvestigate "
            "and provide the method of verification, including the specific dates and "
            "amounts reported by the furnisher. If this cannot be verified with documentary "
            "evidence, delete the negative notation immediately.\n\n"
            "Account: {account}\nCreditor: {target}\nReason: {reason}"
        ),
    },
    "charge_off": {
        "label": "Charge-Off",
        "type": "bureau",
        "fcra_sections": ["609", "611", "623"],
        "keywords": [
            "charge-off", "charged off", "charge off", "profit and loss",
            "written off", "bad debt",
        ],
        "reason_template": "Charge-off on {account} is disputed. The balance and/or "
                           "status reported is inaccurate.",
        "letter_body": (
            "I am disputing the charge-off status on the account below under {cit}. "
            "The reported balance, status, and/or date of first delinquency is inaccurate. "
            "A charge-off is an accounting action by the creditor, not a legal status, and "
            "should not continue to be reported with an increasing balance. I demand full "
            "reinvestigation and documentary proof of the balance claimed.\n\n"
            "Account: {account}\nCreditor: {target}\nAmount: {amount}\nReason: {reason}"
        ),
    },
    "identity_error": {
        "label": "Not My Account / Identity Error",
        "type": "bureau",
        "fcra_sections": ["609", "611"],
        "keywords": [
            "not mine", "identity", "fraud", "unauthorized",
            "mixed file", "not my account", "unknown account",
        ],
        "reason_template": "This account does not belong to me. This may be a mixed file "
                           "error or the result of identity theft.",
        "letter_body": (
            "I am disputing the account below under {cit}. This account does not belong "
            "to me. I have never opened, authorized, or benefited from this account. This "
            "may be the result of a mixed credit file or identity theft. I demand that you "
            "conduct a thorough reinvestigation and provide full subscriber details "
            "(name, address, phone) for the furnisher. If you cannot verify that I am "
            "the account holder with documentary proof, delete immediately.\n\n"
            "Account: {account}\nReported by: {target}\nReason: {reason}"
        ),
    },
    "inquiry": {
        "label": "Unauthorized Hard Inquiry",
        "type": "bureau",
        "fcra_sections": ["609", "611"],
        "keywords": [
            "inquiry", "hard inquiry", "hard pull", "unauthorized inquiry",
            "credit check", "credit inquiry",
        ],
        "reason_template": "I did not authorize this credit inquiry. Remove it.",
        "letter_body": (
            "I am disputing the hard inquiry listed below under {cit}. I did not "
            "authorize this entity to pull my credit report. Under FCRA §604, a "
            "permissible purpose is required for any credit inquiry. Please provide "
            "proof of my written authorization. If you cannot, remove this inquiry "
            "within 30 days.\n\n"
            "Inquiry by: {target}\nDate: {opened}\nReason: {reason}"
        ),
    },
    "medical_debt": {
        "label": "Medical Debt",
        "type": "bureau",
        "fcra_sections": ["609", "611"],
        "keywords": [
            "medical", "hospital", "doctor", "healthcare",
            "health", "clinic", "emergency", "patient",
        ],
        "reason_template": "Medical debt on {account} is disputed. Verify with the "
                           "original healthcare provider and provide itemized billing.",
        "letter_body": (
            "I am disputing the medical debt listed below under {cit}. Under recent "
            "FCRA amendments, paid medical debts and medical debts under $500 should not "
            "appear on credit reports. I demand reinvestigation and request that you "
            "verify this debt with the original healthcare provider, not just the "
            "collection agency. Provide the original itemized bill and proof that this "
            "debt is eligible for credit reporting.\n\n"
            "Account: {account}\nReported by: {target}\nAmount: {amount}\nReason: {reason}"
        ),
    },
    "creditor_direct": {
        "label": "Direct Creditor Dispute (§623)",
        "type": "creditor",
        "fcra_sections": ["623"],
        "keywords": [],
        "reason_template": "I am directly disputing the information you are furnishing "
                           "about account {account}.",
        "letter_body": (
            "Under {cit}, I am directly disputing the accuracy of the information you "
            "are furnishing to consumer reporting agencies regarding my account. You are "
            "required to conduct a reasonable investigation and correct or delete any "
            "information that cannot be verified. If you are a debt collector, this also "
            "serves as a validation request under the FDCPA.\n\n"
            "Account: {account}\nReason: {reason}\n\n"
            "Provide complete validation/contract and account-level documentation. "
            "Update all CRAs to delete or correct inaccurate data. Cease collection "
            "and reporting until validation is complete."
        ),
    },
    "obsolete": {
        "label": "Obsolete / Expired Item (>7 years)",
        "type": "bureau",
        "fcra_sections": ["609", "611"],
        "keywords": [
            "obsolete", "expired", "7 years", "seven years",
            "aged off", "re-aged", "date of first delinquency",
        ],
        "reason_template": "This item has exceeded the 7-year reporting period under "
                           "FCRA §605 and must be removed.",
        "letter_body": (
            "I am disputing the account below under {cit}. This negative item has "
            "exceeded the maximum reporting period of 7 years (7.5 years for certain "
            "items) as defined by FCRA §605. The date of first delinquency as reported "
            "is inaccurate and/or the item is obsolete. Delete this tradeline "
            "immediately.\n\n"
            "Account: {account}\nCreditor: {target}\nReason: {reason}"
        ),
    },
}

FCRA_CITATIONS = {
    "609": "15 U.S.C. §1681g (FCRA §609(a))",
    "611": "15 U.S.C. §1681i (FCRA §611)",
    "623": "15 U.S.C. §1681s-2 (FCRA §623)",
}


def get_bucket(bucket_id: str) -> dict:
    return DISPUTE_BUCKETS.get(bucket_id, {})


def get_all_buckets() -> dict:
    """Return all buckets with labels for admin/frontend."""
    return {
        k: {"label": v["label"], "type": v["type"], "fcra_sections": v["fcra_sections"]}
        for k, v in DISPUTE_BUCKETS.items()
    }


def render_letter_for_bucket(bucket_id: str, item: dict) -> str:
    """Render a dispute letter body using the bucket's template."""
    bucket = DISPUTE_BUCKETS.get(bucket_id)
    if not bucket:
        return ""

    citations = ", ".join(FCRA_CITATIONS.get(s, s) for s in bucket["fcra_sections"])

    return bucket["letter_body"].format(
        cit=citations,
        account=item.get("account", "N/A"),
        target=item.get("target", "N/A"),
        amount=f"${item['amount']:.2f}" if item.get("amount") else "N/A",
        reason=item.get("reason", "N/A"),
        opened=item.get("opened", "N/A"),
    )
