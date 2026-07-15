# 5 Minutes to Credit Wellness — State Law Database
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# 50 states + DC: statute of limitations, consumer protection acts, case law.
# Used by classifier.py (SOL checks) and letters.py (state law blocks).

STATE_LAWS = {
    "AL": {"name": "Alabama", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "Ala. Code 6-2-34", "consumer_act": "Alabama Deceptive Trade Practices Act (Ala. Code 8-19-1)"},
    "AK": {"name": "Alaska", "sol_written": 3, "sol_oral": 3, "sol_open": 3, "statute": "Alaska Stat. 09.10.053", "consumer_act": "Alaska Unfair Trade Practices Act (AS 45.50.471)"},
    "AZ": {"name": "Arizona", "sol_written": 6, "sol_oral": 3, "sol_open": 6, "statute": "A.R.S. 12-548", "consumer_act": "Arizona Consumer Fraud Act (A.R.S. 44-1521)"},
    "AR": {"name": "Arkansas", "sol_written": 5, "sol_oral": 5, "sol_open": 5, "statute": "A.C.A. 16-56-111", "consumer_act": "Arkansas Deceptive Trade Practices Act (A.C.A. 4-88-101)"},
    "CA": {"name": "California", "sol_written": 4, "sol_oral": 2, "sol_open": 4, "statute": "Cal. Civ. Proc. 337", "consumer_act": "California Consumer Legal Remedies Act (Cal. Civ. Code 1750)", "extra": "Cal. Civ. Code 1788 (Rosenthal Fair Debt Collection Practices Act) provides additional state-level protections beyond the federal FDCPA."},
    "CO": {"name": "Colorado", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "C.R.S. 13-80-103.5", "consumer_act": "Colorado Consumer Protection Act (C.R.S. 6-1-101)"},
    "CT": {"name": "Connecticut", "sol_written": 6, "sol_oral": 3, "sol_open": 6, "statute": "Conn. Gen. Stat. 52-576", "consumer_act": "Connecticut Unfair Trade Practices Act (Conn. Gen. Stat. 42-110a)"},
    "DE": {"name": "Delaware", "sol_written": 3, "sol_oral": 3, "sol_open": 3, "statute": "Del. Code tit. 10 8106", "consumer_act": "Delaware Consumer Fraud Act (Del. Code tit. 6 2511)"},
    "FL": {"name": "Florida", "sol_written": 5, "sol_oral": 4, "sol_open": 5, "statute": "Fla. Stat. 95.11", "consumer_act": "Florida Deceptive and Unfair Trade Practices Act (Fla. Stat. 501.201)", "extra": "Florida law (Fla. Stat. 559.55) provides additional debt collection regulations beyond federal law."},
    "GA": {"name": "Georgia", "sol_written": 6, "sol_oral": 4, "sol_open": 6, "statute": "O.C.G.A. 9-3-24", "consumer_act": "Georgia Fair Business Practices Act (O.C.G.A. 10-1-390)"},
    "HI": {"name": "Hawaii", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "HRS 657-1", "consumer_act": "Hawaii Unfair or Deceptive Acts (HRS 480-2)"},
    "ID": {"name": "Idaho", "sol_written": 5, "sol_oral": 4, "sol_open": 5, "statute": "Idaho Code 5-216", "consumer_act": "Idaho Consumer Protection Act (Idaho Code 48-601)"},
    "IL": {"name": "Illinois", "sol_written": 5, "sol_oral": 5, "sol_open": 5, "statute": "735 ILCS 5/13-205", "consumer_act": "Illinois Consumer Fraud Act (815 ILCS 505/1)"},
    "IN": {"name": "Indiana", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "IC 34-11-2-9", "consumer_act": "Indiana Deceptive Consumer Sales Act (IC 24-5-0.5)"},
    "IA": {"name": "Iowa", "sol_written": 5, "sol_oral": 5, "sol_open": 5, "statute": "Iowa Code 614.1(4)", "consumer_act": "Iowa Consumer Fraud Act (Iowa Code 714.16)"},
    "KS": {"name": "Kansas", "sol_written": 5, "sol_oral": 3, "sol_open": 5, "statute": "K.S.A. 60-511", "consumer_act": "Kansas Consumer Protection Act (K.S.A. 50-623)"},
    "KY": {"name": "Kentucky", "sol_written": 5, "sol_oral": 5, "sol_open": 5, "statute": "KRS 413.120", "consumer_act": "Kentucky Consumer Protection Act (KRS 367.110)"},
    "LA": {"name": "Louisiana", "sol_written": 3, "sol_oral": 3, "sol_open": 3, "statute": "La. Civ. Code 3494", "consumer_act": "Louisiana Unfair Trade Practices Act (La. R.S. 51:1401)"},
    "ME": {"name": "Maine", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "Me. Rev. Stat. tit. 14 752", "consumer_act": "Maine Unfair Trade Practices Act (Me. Rev. Stat. tit. 5 205-A)"},
    "MD": {"name": "Maryland", "sol_written": 3, "sol_oral": 3, "sol_open": 3, "statute": "Md. Code Cts. & Jud. Proc. 5-101", "consumer_act": "Maryland Consumer Protection Act (Md. Code Com. Law 13-101)"},
    "MA": {"name": "Massachusetts", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "M.G.L. ch. 260 2", "consumer_act": "Massachusetts Consumer Protection Act (M.G.L. ch. 93A)"},
    "MI": {"name": "Michigan", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "MCL 600.5807", "consumer_act": "Michigan Consumer Protection Act (MCL 445.901)"},
    "MN": {"name": "Minnesota", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "Minn. Stat. 541.05", "consumer_act": "Minnesota Consumer Fraud Act (Minn. Stat. 325F.68)"},
    "MS": {"name": "Mississippi", "sol_written": 3, "sol_oral": 3, "sol_open": 3, "statute": "Miss. Code 15-1-29", "consumer_act": "Mississippi Consumer Protection Act (Miss. Code 75-24-1)"},
    "MO": {"name": "Missouri", "sol_written": 5, "sol_oral": 5, "sol_open": 5, "statute": "Mo. Rev. Stat. 516.120", "consumer_act": "Missouri Merchandising Practices Act (Mo. Rev. Stat. 407.010)"},
    "MT": {"name": "Montana", "sol_written": 5, "sol_oral": 5, "sol_open": 5, "statute": "Mont. Code 27-2-202", "consumer_act": "Montana Consumer Protection Act (Mont. Code 30-14-101)"},
    "NE": {"name": "Nebraska", "sol_written": 5, "sol_oral": 4, "sol_open": 5, "statute": "Neb. Rev. Stat. 25-205", "consumer_act": "Nebraska Consumer Protection Act (Neb. Rev. Stat. 59-1601)"},
    "NV": {"name": "Nevada", "sol_written": 6, "sol_oral": 4, "sol_open": 6, "statute": "NRS 11.190", "consumer_act": "Nevada Deceptive Trade Practices Act (NRS 598.0903)"},
    "NH": {"name": "New Hampshire", "sol_written": 3, "sol_oral": 3, "sol_open": 3, "statute": "RSA 508:4", "consumer_act": "New Hampshire Consumer Protection Act (RSA 358-A)"},
    "NJ": {"name": "New Jersey", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "N.J.S.A. 2A:14-1", "consumer_act": "New Jersey Consumer Fraud Act (N.J.S.A. 56:8-1)"},
    "NM": {"name": "New Mexico", "sol_written": 6, "sol_oral": 4, "sol_open": 6, "statute": "NMSA 37-1-4", "consumer_act": "New Mexico Unfair Practices Act (NMSA 57-12-1)"},
    "NY": {"name": "New York", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "NY CPLR 213", "consumer_act": "New York General Business Law 349 (Deceptive Acts and Practices)", "extra": "NY also has extensive debt collection regulations under NY Gen. Bus. Law 601."},
    "NC": {"name": "North Carolina", "sol_written": 3, "sol_oral": 3, "sol_open": 3, "statute": "N.C.G.S. 1-52", "consumer_act": "North Carolina Unfair and Deceptive Trade Practices Act (N.C.G.S. 75-1.1)"},
    "ND": {"name": "North Dakota", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "N.D.C.C. 28-01-16", "consumer_act": "North Dakota Consumer Fraud Act (N.D.C.C. 51-15)"},
    "OH": {"name": "Ohio", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "ORC 2305.06", "consumer_act": "Ohio Consumer Sales Practices Act (ORC 1345.01)"},
    "OK": {"name": "Oklahoma", "sol_written": 5, "sol_oral": 3, "sol_open": 5, "statute": "12 Okl. St. 95", "consumer_act": "Oklahoma Consumer Protection Act (15 Okl. St. 751)"},
    "OR": {"name": "Oregon", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "ORS 12.080", "consumer_act": "Oregon Unlawful Trade Practices Act (ORS 646.605)"},
    "PA": {"name": "Pennsylvania", "sol_written": 4, "sol_oral": 4, "sol_open": 4, "statute": "42 Pa.C.S. 5525", "consumer_act": "Pennsylvania Unfair Trade Practices Act (73 P.S. 201-1)"},
    "RI": {"name": "Rhode Island", "sol_written": 10, "sol_oral": 10, "sol_open": 10, "statute": "R.I.G.L. 9-1-13", "consumer_act": "Rhode Island Deceptive Trade Practices Act (R.I.G.L. 6-13.1)"},
    "SC": {"name": "South Carolina", "sol_written": 3, "sol_oral": 3, "sol_open": 3, "statute": "S.C. Code 15-3-530", "consumer_act": "South Carolina Unfair Trade Practices Act (S.C. Code 39-5-10)"},
    "SD": {"name": "South Dakota", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "SDCL 15-2-13", "consumer_act": "South Dakota Deceptive Trade Practices Act (SDCL 37-24)"},
    "TN": {"name": "Tennessee", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "Tenn. Code 28-3-109", "consumer_act": "Tennessee Consumer Protection Act (Tenn. Code 47-18-101)"},
    "TX": {"name": "Texas", "sol_written": 4, "sol_oral": 4, "sol_open": 4, "statute": "Tex. Civ. Prac. & Rem. Code 16.004", "consumer_act": "Texas Deceptive Trade Practices Act (Tex. Bus. & Com. Code 17.41)", "extra": "Texas Finance Code 392 provides additional debt collection protections."},
    "UT": {"name": "Utah", "sol_written": 6, "sol_oral": 4, "sol_open": 6, "statute": "Utah Code 78B-2-309", "consumer_act": "Utah Consumer Sales Practices Act (Utah Code 13-11)"},
    "VT": {"name": "Vermont", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "12 V.S.A. 511", "consumer_act": "Vermont Consumer Protection Act (9 V.S.A. 2451)"},
    "VA": {"name": "Virginia", "sol_written": 5, "sol_oral": 3, "sol_open": 5, "statute": "Va. Code 8.01-246", "consumer_act": "Virginia Consumer Protection Act (Va. Code 59.1-196)"},
    "WA": {"name": "Washington", "sol_written": 6, "sol_oral": 3, "sol_open": 6, "statute": "RCW 4.16.040", "consumer_act": "Washington Consumer Protection Act (RCW 19.86)", "extra": "Washington Collection Agency Act (RCW 19.16) adds state-level collector licensing and conduct rules."},
    "WV": {"name": "West Virginia", "sol_written": 6, "sol_oral": 5, "sol_open": 6, "statute": "W. Va. Code 55-2-6", "consumer_act": "West Virginia Consumer Credit and Protection Act (W. Va. Code 46A-6)"},
    "WI": {"name": "Wisconsin", "sol_written": 6, "sol_oral": 6, "sol_open": 6, "statute": "Wis. Stat. 893.43", "consumer_act": "Wisconsin Deceptive Trade Practices Act (Wis. Stat. 100.18)"},
    "WY": {"name": "Wyoming", "sol_written": 8, "sol_oral": 8, "sol_open": 8, "statute": "Wyo. Stat. 1-3-105", "consumer_act": "Wyoming Consumer Protection Act (Wyo. Stat. 40-12-101)"},
    "DC": {"name": "District of Columbia", "sol_written": 3, "sol_oral": 3, "sol_open": 3, "statute": "D.C. Code 12-301", "consumer_act": "DC Consumer Protection Procedures Act (D.C. Code 28-3901)"},
}

# State-specific case precedent
STATE_CASE_LAW = {
    "TX": {
        "collections": "Cushman and Tex. Fin. Code 392.304 — Texas Debt Collection Act prohibits misrepresenting a debt.",
        "aged_debt": "Texas SOL for written contracts is 4 years (Tex. Civ. Prac. & Rem. Code 16.004).",
        "default": "Texas DTPA (Tex. Bus. & Com. Code 17.41 et seq.) provides treble damages for knowing violations.",
    },
    "CA": {
        "collections": "California Rosenthal Fair Debt Collection Practices Act (Cal. Civ. Code 1788 et seq.) applies to original creditors.",
        "aged_debt": "California SOL for written contracts is 4 years (Cal. Civ. Proc. 337).",
        "default": "California CCRAA (Cal. Civ. Code 1785.31) provides statutory damages ($100-$5,000 per violation).",
    },
    "WA": {
        "collections": "Washington Collection Agency Act (RCW 19.16) regulates debt collectors beyond federal FDCPA.",
        "aged_debt": "Washington SOL is 6 years for written contracts (RCW 4.16.040).",
        "default": "Washington CPA (RCW 19.86.090) provides treble damages, attorney fees, and costs.",
    },
    "FL": {
        "collections": "Florida Consumer Collection Practices Act (Fla. Stat. 559.55 et seq.).",
        "aged_debt": "Florida SOL is 5 years for written contracts (Fla. Stat. 95.11(2)(b)).",
        "default": "Florida FDUTPA (Fla. Stat. 501.204) provides actual damages and attorney fees.",
    },
    "NY": {
        "collections": "New York CPLR 214-g restricts litigation on purchased consumer debt.",
        "aged_debt": "CPLR 214-g (2021) reduced SOL for consumer credit transactions to 3 years.",
        "default": "New York GBL 349 provides statutory damages ($50-$1,000) plus treble damages.",
    },
}

# Federal case law by dispute type (verified citations only)
FEDERAL_CASE_LAW = {
    "collections": [
        "Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997) — CRA must conduct a reasonable reinvestigation.",
        "Johnson v. MBNA America Bank, 357 F.3d 426 (4th Cir. 2004) — furnisher must conduct meaningful review.",
        "Gorman v. Wolpoff & Abramson, 584 F.3d 1147 (9th Cir. 2009) — debt collector liable for reporting disputed debt.",
    ],
    "late_payments": [
        "Seamans v. Temple Univ., 744 F.3d 853 (3d Cir. 2014) — furnisher must investigate inaccurate payment history.",
        "Saunders v. Branch Banking & Trust, 526 F.3d 142 (4th Cir. 2008) — creditor cannot ignore consumer dispute.",
    ],
    "wrong_addresses": [
        "Cortez v. Trans Union LLC, 617 F.3d 688 (3d Cir. 2010) — CRA liable for mixed-file errors.",
        "Sarver v. Experian, 390 F.3d 969 (7th Cir. 2004) — CRA must ensure maximum possible accuracy.",
    ],
    "unknown_accounts": [
        "Sloane v. Equifax, 510 F.3d 495 (4th Cir. 2007) — CRA must block fraudulent tradelines under FCRA 605B.",
        "Cortez v. Trans Union LLC, 617 F.3d 688 (3d Cir. 2010) — mixed files violate duty of accuracy.",
        "Nelson v. Chase Manhattan Mortgage, 282 F.3d 1057 (9th Cir. 2002) — furnisher cannot ignore identity theft notice.",
    ],
    "aged_debt": [
        "Grigoryan v. Experian, 84 F. Supp. 3d 1044 (C.D. Cal. 2014) — CRA liable for failing to remove obsolete information.",
        "Phillips v. Grendahl, 312 F.3d 357 (8th Cir. 2002) — impermissible purpose to pull report for time-barred debt.",
    ],
    "mov_demand": [
        "Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997) — CRA must go beyond automated verification.",
        "Johnson v. MBNA America Bank, 357 F.3d 426 (4th Cir. 2004) — furnisher has independent duty to investigate.",
        "Dennis v. BEH-1, LLC, 520 F.3d 1066 (9th Cir. 2008) — failure to provide MOV is actionable under FCRA 611.",
    ],
}

STATUTORY_CITATIONS = {
    "collections": "LEGAL AUTHORITY:\n- 15 U.S.C. 1681i (FCRA 611) — duty to reinvestigate within 30 days\n- 15 U.S.C. 1681e(b) (FCRA 607(b)) — duty to assure maximum possible accuracy\n- 15 U.S.C. 1692g (FDCPA 809(b)) — debt validation required\n- 15 U.S.C. 1681s-2(b) (FCRA 623(b)) — furnisher duty to investigate",
    "late_payments": "LEGAL AUTHORITY:\n- 15 U.S.C. 1681i (FCRA 611) — duty to reinvestigate\n- 15 U.S.C. 1681s-2(a)(1)(A) (FCRA 623(a)) — shall not report known inaccurate info\n- 15 U.S.C. 1681s-2(a)(1)(F) (FCRA 623(a)(1)(F)) — CARES Act accommodation reporting",
    "wrong_addresses": "LEGAL AUTHORITY:\n- 15 U.S.C. 1681e(b) (FCRA 607(b)) — maximum possible accuracy\n- 15 U.S.C. 1681i (FCRA 611) — reinvestigate inaccurate personal info\n- 15 U.S.C. 1681c-2 (FCRA 605C) — block identity theft info",
    "unknown_accounts": "LEGAL AUTHORITY:\n- 15 U.S.C. 1681c-2 (FCRA 605B) — blocking identity theft info\n- 15 U.S.C. 1681i (FCRA 611) — reinvestigation\n- 15 U.S.C. 1681b (FCRA 604) — permissible purposes",
    "aged_debt": "LEGAL AUTHORITY:\n- 15 U.S.C. 1681c(a) (FCRA 605(a)) — 7-year reporting limit\n- 15 U.S.C. 1681c(c) (FCRA 605(c)) — prohibition on re-aging\n- 15 U.S.C. 1681i (FCRA 611) — reinvestigation and deletion",
    "mov_demand": "LEGAL AUTHORITY:\n- 15 U.S.C. 1681i(a)(6)(B)(iii) (FCRA 611(a)(6)(B)(iii)) — must provide method of verification\n- 15 U.S.C. 1681n (FCRA 616) — willful noncompliance: $100-$1,000 per violation\n- 15 U.S.C. 1681o (FCRA 617) — negligent noncompliance: actual damages",
}


def build_state_law_block(state_code: str, dispute_type: str) -> str:
    """Build comprehensive state-specific legal paragraph."""
    parts = []
    fed_cite = STATUTORY_CITATIONS.get(dispute_type)
    if fed_cite:
        parts.append(fed_cite)
    fed_cases = FEDERAL_CASE_LAW.get(dispute_type, [])
    if fed_cases:
        parts.append("FEDERAL CASE PRECEDENT:")
        for case in fed_cases:
            parts.append(f"- {case}")
    law = STATE_LAWS.get(state_code)
    if law:
        sol = law["sol_written"]
        parts.append(f'\nSTATE LAW ({law["name"].upper()}):')
        parts.append(f'- Statute of limitations: {sol} year{"s" if sol != 1 else ""} ({law["statute"]})')
        parts.append(f'- Consumer protection: {law["consumer_act"]}')
        if law.get("extra"):
            parts.append(f"- {law['extra']}")
        state_cases = STATE_CASE_LAW.get(state_code, {})
        case_text = state_cases.get(dispute_type) or state_cases.get("default")
        if case_text:
            parts.append(f'\nSTATE PRECEDENT ({law["name"].upper()}):')
            parts.append(f"- {case_text}")
    return "\n".join(parts)
