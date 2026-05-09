
from __future__ import annotations

FCRA = {
    "609": "15 U.S.C. §1681g (FCRA §609(a))",
    "611": "15 U.S.C. §1681i (FCRA §611)",
    "623": "15 U.S.C. §1681s-2 (FCRA §623)",
}

BUREAU_ADDRESSES = {
    "Experian": "P.O. Box 4500, Allen, TX 75013",
    "Equifax": "P.O. Box 740241, Atlanta, GA 30374-0241",
    "TransUnion": "P.O. Box 2000, Chester, PA 19016-2000",
}

HEADER = """{name}
{address}
{phone} | {email}
DOB: {dob} | SSN (last 4): {ssn_last4}
{today}
"""

BUREAU_BODY = """Re: Demand for Investigation & Full File Disclosure — FCRA {cit_609} & {cit_611}

To {target}:
This is a formal dispute and request for reinvestigation pursuant to {cit_611} and a request for
full file disclosure under {cit_609}. I dispute the accuracy and/or completeness of the account(s)
listed below. Please conduct a reasonable reinvestigation, delete unverifiable data, and provide
me a complete updated report. If you verify any item, provide the name, address, and telephone
number of each furnisher you contacted and the method of verification, as required.

Disputed Item(s):
{items_block}

Action Requested:
  • Delete any item you cannot fully verify.
  • Provide full file disclosure, including soft inquiries and all subscriber info.
  • Send results to the address above within 30 days.

Sincerely,

{name}
"""

CREDITOR_BODY = """Re: Direct Dispute & Validation Request — FCRA {cit_623} / FDCPA (as applicable)

To {target}:
I am disputing the accuracy and completeness of the information you are furnishing to consumer
reporting agencies regarding the account identified below. Under {cit_623}, you must conduct a
reasonable investigation and correct or delete any information that you cannot verify. If you are a
debt collector, treat this as a validation request under the FDCPA and cease reporting until validated.

Account: {account}
Reason(s) for dispute: {reason}

Action Requested:
  • Provide complete validation/contract and account-level documentation.
  • Update all CRAs to delete or correct inaccurate data.
  • Cease collection/reporting until validation is complete.

Sincerely,

{name}
"""

COVER_SHEET = """MASTER COVER SHEET — Credit Dispute Binder
Client: {name} | DOB: {dob} | SSN last4: {ssn_last4} | Phone: {phone} | Email: {email}
Address: {address}
Generated: {today}

Phases: 
  Phase 1 — Docs/ID (Complete?) {p1}
  Phase 2 — Bureau Disputes (Open Items) {p2_count}
  Phase 3 — Creditor Disputes (Open Items) {p3_count}
  Phase 4 — Follow-Up & Escalation (CFPB/AG) (Pending) {p4}

Attachments on File: {attachments}
"""
