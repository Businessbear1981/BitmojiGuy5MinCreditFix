# BitmojiGuy 5-Min Credit Fix — Production Build
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# All rights reserved. AE.CC.001

import os
import re
import uuid
import json
import hashlib
import smtplib
import tempfile
import base64
import threading
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

from flask import (Flask, render_template, request, jsonify,
                   session, redirect, url_for, abort)
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
import pdfplumber
import stripe
import requests as http_requests

import database

# ─── APP SETUP ────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ae-labs-credit-fix-dev-key-change-me')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

UPLOAD_FOLDER = tempfile.mkdtemp(prefix='aecf_')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}
ADMIN_KEY = os.environ.get('ADMIN_KEY', 'ae-admin-2025')

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUB_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
PRICE_CENTS = 1999
CLICK2MAIL_API_KEY = os.environ.get('CLICK2MAIL_API_KEY', '')

# In-memory ephemeral stores
submissions = {}   # session_id -> encrypted blob
admin_log = []     # lightweight log for admin (no PII)


# ═════════════════════════════════════════════════════════════════════════════
# ENCRYPTION ENGINE — timestamp + IP hash, no permanent storage
# ═════════════════════════════════════════════════════════════════════════════

def _derive_key(session_id, ip, timestamp):
    raw = f"{session_id}:{ip}:{timestamp}:{app.secret_key}"
    digest = hashlib.sha256(raw.encode()).digest()
    return base64.urlsafe_b64encode(digest[:32])


def encrypt_data(data, session_id, ip, timestamp):
    return Fernet(_derive_key(session_id, ip, timestamp)).encrypt(json.dumps(data).encode())


def decrypt_data(token, session_id, ip, timestamp):
    return json.loads(Fernet(_derive_key(session_id, ip, timestamp)).decrypt(token).decode())


def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr or '0.0.0.0').split(',')[0].strip()


def store_submission(sid, data):
    ip = get_client_ip()
    ts = session.get('enc_ts', datetime.utcnow().isoformat())
    session['enc_ts'] = ts
    submissions[sid] = encrypt_data(data, sid, ip, ts)
    # Admin log (no PII)
    existing = next((e for e in admin_log if e['id'] == sid), None)
    if existing:
        existing.update(status=data.get('status'), updated_at=datetime.utcnow().isoformat(),
                        dispute_count=len(data.get('dispute_items', [])),
                        paid=data.get('paid', False), confirmation=data.get('confirmation', ''))
    else:
        admin_log.append(dict(id=sid, status=data.get('status', 'started'),
                              created_at=datetime.utcnow().isoformat(),
                              updated_at=datetime.utcnow().isoformat(),
                              dispute_count=0, paid=False, confirmation='',
                              initials=(data.get('name', '??')[:2]).upper()))


def load_submission(sid):
    token = submissions.get(sid)
    if not token:
        return None
    try:
        return decrypt_data(token, sid, get_client_ip(), session.get('enc_ts', ''))
    except Exception:
        return None


# ═════════════════════════════════════════════════════════════════════════════
# GILMORE DISPUTE ORDER — enforced sequence for maximum impact
# ═════════════════════════════════════════════════════════════════════════════

GILMORE_ORDER = ['wrong_addresses', 'unknown_accounts', 'collections', 'aged_debt', 'late_payments', 'mov_demand']
GILMORE_LABELS = {
    'wrong_addresses': 'Phase 1: Personal Info',
    'unknown_accounts': 'Phase 2: Inquiries & Unknown Accounts',
    'collections': 'Phase 3: Collections',
    'aged_debt': 'Phase 4: Charge-Offs & Aged Debt',
    'late_payments': 'Phase 5: Late Payments',
    'mov_demand': 'Follow-Up: Method of Verification',
}


# ═════════════════════════════════════════════════════════════════════════════
# CLIENT PROFILE SCHEMA — structured JSON replacing loose dicts
# ═════════════════════════════════════════════════════════════════════════════

def create_client_profile(sid, name, email, phone, state):
    """Factory for a well-defined client profile."""
    now = datetime.utcnow().isoformat()
    return {
        'id': sid,
        'name': name,
        'email': email,
        'phone': phone,
        'state': state,
        'created_at': now,
        'updated_at': now,
        'status': 'started',
        'confirmation': None,
        'paid': False,
        'paid_at': None,
        'payment_method': None,
        'files': [],
        'parsed_disputes': {},
        'dispute_items': [],
        'dispute_types': [],
        'dispute_order': [],
        'letters': [],
        'status_per_item': {},
        'follow_up_dates': {'day_30': None, 'day_60': None, 'day_90': None},
        'follow_up_history': [],
        'follow_up_letters': {},
        'mov_letters_sent': [],
    }


# ═════════════════════════════════════════════════════════════════════════════
# DOCUMENT PARSING ENGINE
# ═════════════════════════════════════════════════════════════════════════════

DISPUTE_PATTERNS = {
    'collections': {
        'label': 'Collection Account',
        'patterns': [
            r'(?i)collect(?:ion|ions)\s+(?:account|agency|balance)',
            r'(?i)(?:placed|sent|sold)\s+(?:for|to)\s+collect',
            r'(?i)charged?\s*off.*collect',
            r'(?i)(?:portfolio|midland|lvnv|encore|cavalry|ic system)',
        ],
        'extract': r'(?i)((?:collection|collect\w+).{0,80}(?:\$[\d,.]+|\d{4,}))',
    },
    'late_payments': {
        'label': 'Late Payment',
        'patterns': [
            r'(?i)(?:30|60|90|120)\s*days?\s*(?:late|past\s*due|delinq)',
            r'(?i)late\s+payment',
            r'(?i)past\s+due\s+(?:amount|balance)',
            r'(?i)delinquen(?:t|cy)',
        ],
        'extract': r'(?i)((?:late|past due|delinq)\w*.{0,80}(?:\$[\d,.]+|\d{2}/\d{2,4}))',
    },
    'wrong_addresses': {
        'label': 'Incorrect Address',
        'patterns': [
            r'(?i)address(?:es)?\s+(?:reported|on file|listed)',
            r'(?i)(?:previous|former|old|prior)\s+address',
            r'(?i)(?:po box|p\.o\.\s*box)\s*\d+',
        ],
        'extract': r'(?i)((?:address|addr).{0,120})',
    },
    'unknown_accounts': {
        'label': 'Unknown / Unrecognized Account',
        'patterns': [
            r'(?i)(?:authorized\s+user|au\s+account)',
            r'(?i)inquir(?:y|ies)',
            r'(?i)(?:hard|soft)\s+(?:pull|inquiry)',
            r'(?i)account\s+(?:number|#|no)[\s.:]*\w{4,}',
        ],
        'extract': r'(?i)((?:account|acct)[\s#.:]*\w*.{0,80})',
    },
    'aged_debt': {
        'label': 'Aged / Time-Barred Debt',
        'patterns': [
            r'(?i)(?:date\s+)?open(?:ed)?[\s:]+\d{1,2}/\d{2,4}',
            r'(?i)(?:original|first)\s+delinquency',
            r'(?i)statute\s+of\s+limitation',
            r'(?i)charge[\s-]*off\s+(?:date|since)',
        ],
        'extract': r'(?i)((?:charge.?off|delinquen|open(?:ed)?).{0,100}(?:\d{1,2}/\d{2,4}|\$[\d,.]+))',
    },
}


def parse_text_for_disputes(text):
    results = {}
    for dtype, cfg in DISPUTE_PATTERNS.items():
        if any(re.search(p, text) for p in cfg['patterns']):
            hits = [re.sub(r'\s+', ' ', m.strip())[:120]
                    for m in re.findall(cfg['extract'], text)[:5]
                    if len(m.strip()) > 15]
            if not hits:
                hits = [f"{cfg['label']} detected in report"]
            results[dtype] = {'label': cfg['label'], 'items': hits}
    return results


def extract_text_from_pdf(filepath):
    text = ''
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages[:30]:
                t = page.extract_text()
                if t:
                    text += t + '\n'
    except Exception as e:
        print(f"[PDF ERROR] {e}")
    return text


def parse_uploaded_files(filepaths):
    combined = ''
    has_images = False
    for fp, fn in filepaths:
        ext = fn.rsplit('.', 1)[-1].lower() if '.' in fn else ''
        if ext == 'pdf':
            combined += extract_text_from_pdf(fp) + '\n'
        elif ext == 'txt':
            try:
                with open(fp, 'r', errors='ignore') as f:
                    combined += f.read() + '\n'
            except Exception:
                pass
        elif ext in ('png', 'jpg', 'jpeg'):
            has_images = True
    results = parse_text_for_disputes(combined)
    if has_images and not results:
        results['unknown_accounts'] = {
            'label': 'Manual Review Needed',
            'items': ['Image uploaded -- select dispute types manually below'],
        }
    return results


# ═════════════════════════════════════════════════════════════════════════════
# STATE LAW DATABASE — statute of limitations + consumer protection statutes
# ═════════════════════════════════════════════════════════════════════════════

STATE_LAWS = {
    'AL': {'name': 'Alabama', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'Ala. Code 6-2-34', 'consumer_act': 'Alabama Deceptive Trade Practices Act (Ala. Code 8-19-1)'},
    'AK': {'name': 'Alaska', 'sol_written': 3, 'sol_oral': 3, 'sol_open': 3, 'statute': 'Alaska Stat. 09.10.053', 'consumer_act': 'Alaska Unfair Trade Practices Act (AS 45.50.471)'},
    'AZ': {'name': 'Arizona', 'sol_written': 6, 'sol_oral': 3, 'sol_open': 6, 'statute': 'A.R.S. 12-548', 'consumer_act': 'Arizona Consumer Fraud Act (A.R.S. 44-1521)'},
    'AR': {'name': 'Arkansas', 'sol_written': 5, 'sol_oral': 5, 'sol_open': 5, 'statute': 'A.C.A. 16-56-111', 'consumer_act': 'Arkansas Deceptive Trade Practices Act (A.C.A. 4-88-101)'},
    'CA': {'name': 'California', 'sol_written': 4, 'sol_oral': 2, 'sol_open': 4, 'statute': 'Cal. Civ. Proc. 337', 'consumer_act': 'California Consumer Legal Remedies Act (Cal. Civ. Code 1750)', 'extra': 'Cal. Civ. Code 1788 (Rosenthal Fair Debt Collection Practices Act) provides additional state-level protections beyond the federal FDCPA.'},
    'CO': {'name': 'Colorado', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'C.R.S. 13-80-103.5', 'consumer_act': 'Colorado Consumer Protection Act (C.R.S. 6-1-101)'},
    'CT': {'name': 'Connecticut', 'sol_written': 6, 'sol_oral': 3, 'sol_open': 6, 'statute': 'Conn. Gen. Stat. 52-576', 'consumer_act': 'Connecticut Unfair Trade Practices Act (Conn. Gen. Stat. 42-110a)'},
    'DE': {'name': 'Delaware', 'sol_written': 3, 'sol_oral': 3, 'sol_open': 3, 'statute': 'Del. Code tit. 10 8106', 'consumer_act': 'Delaware Consumer Fraud Act (Del. Code tit. 6 2511)'},
    'FL': {'name': 'Florida', 'sol_written': 5, 'sol_oral': 4, 'sol_open': 5, 'statute': 'Fla. Stat. 95.11', 'consumer_act': 'Florida Deceptive and Unfair Trade Practices Act (Fla. Stat. 501.201)', 'extra': 'Florida law (Fla. Stat. 559.55) provides additional debt collection regulations beyond federal law.'},
    'GA': {'name': 'Georgia', 'sol_written': 6, 'sol_oral': 4, 'sol_open': 6, 'statute': 'O.C.G.A. 9-3-24', 'consumer_act': 'Georgia Fair Business Practices Act (O.C.G.A. 10-1-390)'},
    'HI': {'name': 'Hawaii', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'HRS 657-1', 'consumer_act': 'Hawaii Unfair or Deceptive Acts (HRS 480-2)'},
    'ID': {'name': 'Idaho', 'sol_written': 5, 'sol_oral': 4, 'sol_open': 5, 'statute': 'Idaho Code 5-216', 'consumer_act': 'Idaho Consumer Protection Act (Idaho Code 48-601)'},
    'IL': {'name': 'Illinois', 'sol_written': 5, 'sol_oral': 5, 'sol_open': 5, 'statute': '735 ILCS 5/13-205', 'consumer_act': 'Illinois Consumer Fraud Act (815 ILCS 505/1)'},
    'IN': {'name': 'Indiana', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'IC 34-11-2-9', 'consumer_act': 'Indiana Deceptive Consumer Sales Act (IC 24-5-0.5)'},
    'IA': {'name': 'Iowa', 'sol_written': 5, 'sol_oral': 5, 'sol_open': 5, 'statute': 'Iowa Code 614.1(4)', 'consumer_act': 'Iowa Consumer Fraud Act (Iowa Code 714.16)'},
    'KS': {'name': 'Kansas', 'sol_written': 5, 'sol_oral': 3, 'sol_open': 5, 'statute': 'K.S.A. 60-511', 'consumer_act': 'Kansas Consumer Protection Act (K.S.A. 50-623)'},
    'KY': {'name': 'Kentucky', 'sol_written': 5, 'sol_oral': 5, 'sol_open': 5, 'statute': 'KRS 413.120', 'consumer_act': 'Kentucky Consumer Protection Act (KRS 367.110)'},
    'LA': {'name': 'Louisiana', 'sol_written': 3, 'sol_oral': 3, 'sol_open': 3, 'statute': 'La. Civ. Code 3494', 'consumer_act': 'Louisiana Unfair Trade Practices Act (La. R.S. 51:1401)'},
    'ME': {'name': 'Maine', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'Me. Rev. Stat. tit. 14 752', 'consumer_act': 'Maine Unfair Trade Practices Act (Me. Rev. Stat. tit. 5 205-A)'},
    'MD': {'name': 'Maryland', 'sol_written': 3, 'sol_oral': 3, 'sol_open': 3, 'statute': 'Md. Code Cts. & Jud. Proc. 5-101', 'consumer_act': 'Maryland Consumer Protection Act (Md. Code Com. Law 13-101)'},
    'MA': {'name': 'Massachusetts', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'M.G.L. ch. 260 2', 'consumer_act': 'Massachusetts Consumer Protection Act (M.G.L. ch. 93A)'},
    'MI': {'name': 'Michigan', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'MCL 600.5807', 'consumer_act': 'Michigan Consumer Protection Act (MCL 445.901)'},
    'MN': {'name': 'Minnesota', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'Minn. Stat. 541.05', 'consumer_act': 'Minnesota Consumer Fraud Act (Minn. Stat. 325F.68)'},
    'MS': {'name': 'Mississippi', 'sol_written': 3, 'sol_oral': 3, 'sol_open': 3, 'statute': 'Miss. Code 15-1-29', 'consumer_act': 'Mississippi Consumer Protection Act (Miss. Code 75-24-1)'},
    'MO': {'name': 'Missouri', 'sol_written': 5, 'sol_oral': 5, 'sol_open': 5, 'statute': 'Mo. Rev. Stat. 516.120', 'consumer_act': 'Missouri Merchandising Practices Act (Mo. Rev. Stat. 407.010)'},
    'MT': {'name': 'Montana', 'sol_written': 5, 'sol_oral': 5, 'sol_open': 5, 'statute': 'Mont. Code 27-2-202', 'consumer_act': 'Montana Consumer Protection Act (Mont. Code 30-14-101)'},
    'NE': {'name': 'Nebraska', 'sol_written': 5, 'sol_oral': 4, 'sol_open': 5, 'statute': 'Neb. Rev. Stat. 25-205', 'consumer_act': 'Nebraska Consumer Protection Act (Neb. Rev. Stat. 59-1601)'},
    'NV': {'name': 'Nevada', 'sol_written': 6, 'sol_oral': 4, 'sol_open': 6, 'statute': 'NRS 11.190', 'consumer_act': 'Nevada Deceptive Trade Practices Act (NRS 598.0903)'},
    'NH': {'name': 'New Hampshire', 'sol_written': 3, 'sol_oral': 3, 'sol_open': 3, 'statute': 'RSA 508:4', 'consumer_act': 'New Hampshire Consumer Protection Act (RSA 358-A)'},
    'NJ': {'name': 'New Jersey', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'N.J.S.A. 2A:14-1', 'consumer_act': 'New Jersey Consumer Fraud Act (N.J.S.A. 56:8-1)'},
    'NM': {'name': 'New Mexico', 'sol_written': 6, 'sol_oral': 4, 'sol_open': 6, 'statute': 'NMSA 37-1-4', 'consumer_act': 'New Mexico Unfair Practices Act (NMSA 57-12-1)'},
    'NY': {'name': 'New York', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'NY CPLR 213', 'consumer_act': 'New York General Business Law 349 (Deceptive Acts and Practices)', 'extra': 'NY also has extensive debt collection regulations under NY Gen. Bus. Law 601.'},
    'NC': {'name': 'North Carolina', 'sol_written': 3, 'sol_oral': 3, 'sol_open': 3, 'statute': 'N.C.G.S. 1-52', 'consumer_act': 'North Carolina Unfair and Deceptive Trade Practices Act (N.C.G.S. 75-1.1)'},
    'ND': {'name': 'North Dakota', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'N.D.C.C. 28-01-16', 'consumer_act': 'North Dakota Consumer Fraud Act (N.D.C.C. 51-15)'},
    'OH': {'name': 'Ohio', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'ORC 2305.06', 'consumer_act': 'Ohio Consumer Sales Practices Act (ORC 1345.01)'},
    'OK': {'name': 'Oklahoma', 'sol_written': 5, 'sol_oral': 3, 'sol_open': 5, 'statute': '12 Okl. St. 95', 'consumer_act': 'Oklahoma Consumer Protection Act (15 Okl. St. 751)'},
    'OR': {'name': 'Oregon', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'ORS 12.080', 'consumer_act': 'Oregon Unlawful Trade Practices Act (ORS 646.605)'},
    'PA': {'name': 'Pennsylvania', 'sol_written': 4, 'sol_oral': 4, 'sol_open': 4, 'statute': '42 Pa.C.S. 5525', 'consumer_act': 'Pennsylvania Unfair Trade Practices Act (73 P.S. 201-1)'},
    'RI': {'name': 'Rhode Island', 'sol_written': 10, 'sol_oral': 10, 'sol_open': 10, 'statute': 'R.I.G.L. 9-1-13', 'consumer_act': 'Rhode Island Deceptive Trade Practices Act (R.I.G.L. 6-13.1)'},
    'SC': {'name': 'South Carolina', 'sol_written': 3, 'sol_oral': 3, 'sol_open': 3, 'statute': 'S.C. Code 15-3-530', 'consumer_act': 'South Carolina Unfair Trade Practices Act (S.C. Code 39-5-10)'},
    'SD': {'name': 'South Dakota', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'SDCL 15-2-13', 'consumer_act': 'South Dakota Deceptive Trade Practices Act (SDCL 37-24)'},
    'TN': {'name': 'Tennessee', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'Tenn. Code 28-3-109', 'consumer_act': 'Tennessee Consumer Protection Act (Tenn. Code 47-18-101)'},
    'TX': {'name': 'Texas', 'sol_written': 4, 'sol_oral': 4, 'sol_open': 4, 'statute': 'Tex. Civ. Prac. & Rem. Code 16.004', 'consumer_act': 'Texas Deceptive Trade Practices Act (Tex. Bus. & Com. Code 17.41)', 'extra': 'Texas Finance Code 392 provides additional debt collection protections.'},
    'UT': {'name': 'Utah', 'sol_written': 6, 'sol_oral': 4, 'sol_open': 6, 'statute': 'Utah Code 78B-2-309', 'consumer_act': 'Utah Consumer Sales Practices Act (Utah Code 13-11)'},
    'VT': {'name': 'Vermont', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': '12 V.S.A. 511', 'consumer_act': 'Vermont Consumer Protection Act (9 V.S.A. 2451)'},
    'VA': {'name': 'Virginia', 'sol_written': 5, 'sol_oral': 3, 'sol_open': 5, 'statute': 'Va. Code 8.01-246', 'consumer_act': 'Virginia Consumer Protection Act (Va. Code 59.1-196)'},
    'WA': {'name': 'Washington', 'sol_written': 6, 'sol_oral': 3, 'sol_open': 6, 'statute': 'RCW 4.16.040', 'consumer_act': 'Washington Consumer Protection Act (RCW 19.86)', 'extra': 'Washington Collection Agency Act (RCW 19.16) adds state-level collector licensing and conduct rules.'},
    'WV': {'name': 'West Virginia', 'sol_written': 6, 'sol_oral': 5, 'sol_open': 6, 'statute': 'W. Va. Code 55-2-6', 'consumer_act': 'West Virginia Consumer Credit and Protection Act (W. Va. Code 46A-6)'},
    'WI': {'name': 'Wisconsin', 'sol_written': 6, 'sol_oral': 6, 'sol_open': 6, 'statute': 'Wis. Stat. 893.43', 'consumer_act': 'Wisconsin Deceptive Trade Practices Act (Wis. Stat. 100.18)'},
    'WY': {'name': 'Wyoming', 'sol_written': 8, 'sol_oral': 8, 'sol_open': 8, 'statute': 'Wyo. Stat. 1-3-105', 'consumer_act': 'Wyoming Consumer Protection Act (Wyo. Stat. 40-12-101)'},
    'DC': {'name': 'District of Columbia', 'sol_written': 3, 'sol_oral': 3, 'sol_open': 3, 'statute': 'D.C. Code 12-301', 'consumer_act': 'DC Consumer Protection Procedures Act (D.C. Code 28-3901)'},
}


# ═════════════════════════════════════════════════════════════════════════════
# DISPUTE LETTER ENGINE — 15 templates (3 variants x 5 types)
# ═════════════════════════════════════════════════════════════════════════════

BUREAUS = [
    {'name': 'Equifax', 'address': 'P.O. Box 740256, Atlanta, GA 30374-0256'},
    {'name': 'Experian', 'address': 'P.O. Box 4500, Allen, TX 75013'},
    {'name': 'TransUnion', 'address': 'P.O. Box 2000, Chester, PA 19016'},
]

LETTER_TEMPLATES = {
    'collections': [
        {'variant': 'A', 'title': 'Debt Validation Demand',
         'body': """Dear {bureau},

I am writing to formally dispute the following collection account on my credit report under the FDCPA Section 809(b) and FCRA Section 611.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I do not recognize this debt. Please provide:
1. Original creditor name and address
2. Original account number
3. Amount at time of default
4. Complete payment history from original creditor
5. Copy of original signed agreement bearing my signature

You have 30 days to investigate under the FCRA. If unverifiable, delete this account permanently.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'B', 'title': 'Collection Statute of Limitations Challenge',
         'body': """Dear {bureau},

I dispute the collection account below under the FCRA. I believe it exceeds the statute of limitations for reporting.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

Under FCRA Section 605, negative information must be removed after 7 years from the date of first delinquency. I request:
1. Verify the date of first delinquency with the original creditor
2. Confirm the account has not been re-aged
3. Provide documentation proving it is within the legal reporting window
4. Remove immediately if verification cannot be completed in 30 days

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'C', 'title': 'Cease Collection and Remove',
         'body': """Dear {bureau},

This is a formal dispute and demand for removal of the following collection account(s).

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I dispute this debt in its entirety. The collection agency has failed to provide adequate validation per the FDCPA. Under FCRA Section 611(a)(5)(A), if unverifiable, you must delete it. I request:
1. Immediate investigation
2. Deletion if the furnisher cannot verify in 30 days
3. Written confirmation of results
4. Updated credit report showing deletion

Failure to respond within 30 days will result in a CFPB complaint.

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
    'late_payments': [
        {'variant': 'A', 'title': 'Goodwill Late Payment Removal',
         'body': """Dear {bureau},

I am requesting a goodwill adjustment for the late payment(s) reported on my account.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I have been a responsible borrower. This late payment does not reflect my usual behavior -- I experienced a temporary hardship that has since been resolved. My account is now current and in good standing.

I respectfully request removal of this late payment notation as a goodwill gesture. This would greatly help me qualify for housing and financing.

Thank you for your consideration.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'B', 'title': 'Late Payment Accuracy Dispute',
         'body': """Dear {bureau},

Under FCRA Section 611, I formally dispute the late payment(s) below as inaccurate.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I dispute accuracy for these reasons:
1. My records show payment was made on time
2. I was not properly notified of any discrepancy
3. Payment processing may have been delayed by the creditor

I request:
1. Contact the furnisher to verify exact date payment was received
2. Provide proof of the exact posting date
3. Remove the late notation if it cannot be verified as accurate
4. Written results within 30 days

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'C', 'title': 'Late Payment Dispute -- Accommodation Period',
         'body': """Dear {bureau},

I dispute the late payment(s) below, which were reported during a period when I had a hardship accommodation with the creditor.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

Under the CARES Act and FCRA Section 623(a)(1)(F), if a consumer has a payment accommodation, the account must be reported as current if it was current when the accommodation was granted.

I had a forbearance/deferment agreement in place. The creditor should not have reported these as late. I request:
1. Verification of account status during the accommodation period
2. Correction to reflect "current" or "paid as agreed"
3. Written confirmation within 30 days

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
    'wrong_addresses': [
        {'variant': 'A', 'title': 'Incorrect Address -- Possible Fraud',
         'body': """Dear {bureau},

I dispute incorrect address information on my credit report that I did not provide. This may indicate identity fraud or mixed files.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

These addresses have never been associated with me. I request:
1. Immediately remove all addresses I have not verified
2. Investigate whether accounts from these addresses belong to another consumer
3. Place a note that these addresses are disputed
4. Written confirmation of removal

Under FCRA Section 611, you must maintain accurate consumer information.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'B', 'title': 'Address Correction -- Mixed File',
         'body': """Dear {bureau},

I dispute inaccurate address information on my report. I believe my file may contain info belonging to another consumer.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

My correct address is the one on file. The disputed addresses do not belong to me. Mixed files violate FCRA Section 607(b). I request:
1. Removal of all incorrect addresses
2. Review of all tradelines associated with those addresses
3. Removal of incorrectly merged accounts
4. Written confirmation of corrections

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'C', 'title': 'Address Correction Request',
         'body': """Dear {bureau},

I request correction of address information on my credit report. The following addresses are inaccurate.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I have never resided at the listed addresses. This may result from data entry error, creditor error, or unauthorized use of my information. Please remove all inaccurate entries and send written confirmation within 30 days.

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
    'unknown_accounts': [
        {'variant': 'A', 'title': 'Unknown Account -- Potential Identity Theft',
         'body': """Dear {bureau},

I dispute the following account(s) that I do not recognize. I may be a victim of identity theft.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I did not open or authorize these accounts. Under FCRA Section 605B, I request blocking of information resulting from identity theft. I request:
1. Immediate investigation
2. Removal/blocking of fraudulent accounts
3. Copy of all information used to open these accounts
4. Notification to furnisher(s) that these are disputed as fraud
5. Written confirmation within 30 days

I am prepared to file an FTC Identity Theft Report if needed.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'B', 'title': 'Unknown Account Verification Demand',
         'body': """Dear {bureau},

Under FCRA Section 611, I formally dispute the following accounts. These are not mine.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I demand verification of:
1. Original application or agreement bearing my signature
2. SSN used to open the account
3. Address on the original application
4. Complete account history

If you cannot verify within 30 days, delete these accounts per FCRA Section 611(a)(5)(A).

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'C', 'title': 'Unauthorized Account / Inquiry Dispute',
         'body': """Dear {bureau},

I dispute the following unauthorized accounts and/or hard inquiries made without my permission.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

I did not authorize access to my credit report or opening of accounts. This violates FCRA Section 604. I request:
1. Removal of all unauthorized inquiries
2. Removal of unauthorized accounts
3. Investigation into how my information was obtained
4. Written confirmation within 30 days

If unresolved, I will file CFPB and FTC complaints.

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
    'aged_debt': [
        {'variant': 'A', 'title': 'Time-Barred Debt Removal Demand',
         'body': """Dear {bureau},

I dispute the following account(s) that have exceeded the maximum FCRA reporting period.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

Under FCRA Section 605(a), most negative information must be removed after 7 years from date of first delinquency. I request:
1. Verify date of first delinquency with original creditor
2. Confirm exact scheduled removal date
3. Remove immediately if the 7-year period has expired
4. Ensure the date has not been re-aged

If unverifiable, it must be deleted.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'B', 'title': 'Aged Debt -- Re-Aging Violation',
         'body': """Dear {bureau},

I dispute the following account(s) which I believe have been illegally re-aged, extending the reporting period beyond FCRA limits.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

FCRA Section 605(c) prohibits re-aging. The date of first delinquency cannot change even if the account is sold. I believe:
1. The date of first delinquency has been altered
2. Account transfer resulted in a new, incorrect date
3. This artificially extended the reporting period

I demand documentation of the original date and immediate correction or removal. Re-aging is a federal violation -- I will escalate to the CFPB if unresolved.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'C', 'title': 'Obsolete Information Removal',
         'body': """Dear {bureau},

I dispute outdated information on my credit report that should have been removed per the FCRA.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

Under FCRA Section 605, time limits apply:
- Most negative info: 7 years from date of first delinquency
- Bankruptcies: 7-10 years from filing
- Tax liens: 7 years from payment
- Judgments: 7 years from entry

The above item(s) exceed the applicable limit. I request:
1. Verification of original delinquency date with documentation
2. Immediate removal if it exceeds the reporting period
3. Corrected copy of my report
4. Written notification within 30 days

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],

    'mov_demand': [
        {'variant': 'A', 'title': 'Method of Verification Demand -- Initial',
         'body': """Dear {bureau},

You recently responded to my dispute (Ref: {confirmation}) claiming verification of the following item(s). However, you failed to provide the method of verification as required by law.

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

Under FCRA Section 611(a)(6)(B)(iii), upon completion of a reinvestigation you must provide me with a description of the procedure used to determine accuracy, including the business name, address, and telephone number of any furnisher contacted.

I demand:
1. The specific method used to verify this information
2. Name, address, and phone number of the verifying entity
3. Documentation provided by the furnisher during reinvestigation
4. The specific records reviewed to determine accuracy

Your failure to provide this information violates the FCRA. I reserve all rights under Sections 616 and 617.

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'B', 'title': 'MOV Demand -- Procedural Challenge',
         'body': """Dear {bureau},

I received your response to dispute {confirmation}, which claims the disputed information has been "verified." I am now demanding the method of verification under FCRA Section 611(a)(6)(B)(iii).

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

Your verification appears to have been conducted via automated e-OSCAR system without a genuine reinvestigation. Courts have consistently held that merely parroting furnisher responses does not constitute a "reasonable reinvestigation" under the FCRA. See Cushman v. Trans Union Corp., 115 F.3d 220 (3d Cir. 1997); Johnson v. MBNA America Bank, 357 F.3d 426 (4th Cir. 2004).

A reasonable reinvestigation requires you to:
1. Review all relevant information submitted by the consumer
2. Independently evaluate the furnisher's response
3. Consider whether the furnished information is complete and accurate
4. Provide the consumer with the method and source of verification

I demand all of the above within 15 days. If you cannot substantiate your verification, the disputed items must be deleted per FCRA Section 611(a)(5)(A).

{state_law}

Sincerely,
{name}
Date: {date}"""},
        {'variant': 'C', 'title': 'MOV Demand -- Pre-Litigation Final Notice',
         'body': """Dear {bureau},

This is my final demand for method of verification regarding dispute {confirmation}. Your prior response failed to satisfy the requirements of FCRA Section 611(a)(6)(B)(iii).

Disputed Item(s):
{items}

Consumer: {name} | Ref: {confirmation}

FINAL DEMAND:

You have 15 days from receipt of this letter to provide:
1. Complete method of verification documentation
2. Furnisher contact information (name, address, phone)
3. All records reviewed during your reinvestigation
4. Proof that a genuine reinvestigation was conducted (not automated)

NOTICE OF INTENT TO PURSUE LEGAL REMEDIES:

If adequate verification is not provided within 15 days, I intend to:
1. File a formal complaint with the Consumer Financial Protection Bureau
2. File a complaint with my state Attorney General
3. Pursue remedies under FCRA Section 616 (willful noncompliance) including statutory damages of $100-$1,000 per violation, punitive damages, and attorney's fees
4. Pursue remedies under FCRA Section 617 (negligent noncompliance)

This letter and all prior correspondence are preserved as evidence. Your continued refusal to comply with the FCRA constitutes willful noncompliance.

{state_law}

Sincerely,
{name}
Date: {date}"""},
    ],
}

# Add MOV to pattern labels for display purposes
DISPUTE_PATTERNS['mov_demand'] = {'label': 'Method of Verification Demand'}


def build_state_law_block(state_code, dispute_type):
    """Build a state-specific legal paragraph for the letter."""
    law = STATE_LAWS.get(state_code)
    if not law:
        return ''
    sol = law['sol_written']
    lines = [f'Additionally, under {law["name"]} state law ({law["statute"]}), the statute of limitations for written contracts and credit obligations is {sol} year{"s" if sol != 1 else ""}.']
    if dispute_type in ('collections', 'aged_debt'):
        lines.append(f'Any attempt to collect on a debt that exceeds this {sol}-year period may violate the {law["consumer_act"]}.')
    else:
        lines.append(f'I also reserve my rights under the {law["consumer_act"]}.')
    if law.get('extra'):
        lines.append(law['extra'])
    return '\n'.join(lines)


def generate_letters(dispute_types, items_by_type, client_data):
    letters = []
    date_str = datetime.utcnow().strftime('%B %d, %Y')
    state_code = client_data.get('state', '')
    # Enforce Gilmore dispute order
    ordered_types = sorted(dispute_types, key=lambda t: GILMORE_ORDER.index(t) if t in GILMORE_ORDER else 99)
    for dtype in ordered_types:
        templates = LETTER_TEMPLATES.get(dtype, [])
        items_list = items_by_type.get(dtype, [])
        if isinstance(items_list, dict):
            items_list = items_list.get('items', [])
        items_fmt = '\n'.join(f'  - {i}' for i in items_list) if items_list else '  - See attached documentation'
        state_law = build_state_law_block(state_code, dtype)
        for tmpl in templates:
            for bureau in BUREAUS:
                letters.append({
                    'bureau': bureau['name'],
                    'bureau_address': bureau['address'],
                    'type': dtype,
                    'type_label': DISPUTE_PATTERNS[dtype]['label'],
                    'variant': tmpl['variant'],
                    'title': tmpl['title'],
                    'body': tmpl['body'].format(
                        bureau=bureau['name'], items=items_fmt,
                        name=client_data.get('name', '[YOUR NAME]'),
                        confirmation=client_data.get('confirmation', 'N/A'),
                        date=date_str, state_law=state_law),
                })
    return letters


# ═════════════════════════════════════════════════════════════════════════════
# EMAIL
# ═════════════════════════════════════════════════════════════════════════════

def send_confirmation_email(email, name, confirmation, items):
    smtp_host = os.environ.get('SMTP_HOST', '')
    smtp_user = os.environ.get('SMTP_USER', '')
    if not smtp_host or not smtp_user:
        print(f"[EMAIL SKIP] No SMTP. Confirmation: {confirmation}")
        return True
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f'Your Credit Fix Is In Motion -- {confirmation}'
        msg['From'] = os.environ.get('FROM_EMAIL', 'noreply@aelabs.com')
        msg['To'] = email
        items_str = '\n'.join(f'  * {i}' for i in items) if items else '  * General credit review'
        msg.attach(MIMEText(f"Hey {name},\n\nConfirmation: {confirmation}\n\nDisputing:\n{items_str}\n\nNext: Download your letters, print, and mail via certified mail to all 3 bureaus.\n\n-- AE Labs Credit Team\n(c) 2025 Arden Edge Capital", 'plain'))
        with smtplib.SMTP(smtp_host, int(os.environ.get('SMTP_PORT', 587))) as s:
            s.starttls()
            s.login(smtp_user, os.environ.get('SMTP_PASS', ''))
            s.sendmail(msg['From'], email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.args.get('key', '') or session.get('admin_key', '')
        if key == ADMIN_KEY:
            session['admin_key'] = key
            return f(*args, **kwargs)
        return redirect(url_for('admin_login'))
    return decorated


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def gen_confirmation():
    return 'AE-' + str(uuid.uuid4()).upper()[:8]


def _mark_paid(sub, sid):
    """Mark a submission as paid, compute follow-up dates, persist to DB."""
    now = datetime.utcnow()
    sub['paid'] = True
    sub['status'] = 'paid'
    sub['paid_at'] = now.isoformat()
    sub['updated_at'] = now.isoformat()
    sub['follow_up_dates'] = {
        'day_30': (now + timedelta(days=30)).isoformat(),
        'day_60': (now + timedelta(days=60)).isoformat(),
        'day_90': (now + timedelta(days=90)).isoformat(),
    }
    store_submission(sid, sub)
    database.save_client(sub)
    items_flat = [i.get('text', str(i)) if isinstance(i, dict) else str(i) for i in sub.get('dispute_items', [])]
    send_confirmation_email(sub['email'], sub['name'], sub.get('confirmation', ''), items_flat)


# ═════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html', stripe_key=STRIPE_PUB_KEY)


@app.route('/health')
def health():
    return jsonify(status='ok', service='BitmojiGuy 5-Min Credit Fix', version='2.0.0')


# Step 1 — Start
@app.route('/api/start', methods=['POST'])
def api_start():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    state = data.get('state', '').strip().upper()
    if not name or not email:
        return jsonify(error='Name and email are required'), 400
    if state and state not in STATE_LAWS:
        state = ''
    sid = str(uuid.uuid4())
    session['submission_id'] = sid
    session['enc_ts'] = datetime.utcnow().isoformat()
    sub = create_client_profile(sid, name, email, phone, state)
    store_submission(sid, sub)
    database.save_client(sub)
    return jsonify(ok=True, session_id=sid, name=name)


# Step 2 — Upload & Parse
@app.route('/api/upload', methods=['POST'])
def api_upload():
    sid = session.get('submission_id')
    sub = load_submission(sid) if sid else None
    if not sub:
        return jsonify(error='Session not found. Please start over.'), 400
    files_info, filepaths = [], []
    for key in request.files:
        f = request.files[key]
        if f and f.filename and allowed_file(f.filename):
            fn = secure_filename(f"{sid}_{f.filename}")
            fp = os.path.join(UPLOAD_FOLDER, fn)
            f.save(fp)
            files_info.append({'name': f.filename, 'saved_as': fn})
            filepaths.append((fp, f.filename))
    if not filepaths:
        return jsonify(error='No valid files uploaded'), 400
    parsed = parse_uploaded_files(filepaths)
    for fp, _ in filepaths:
        try: os.remove(fp)
        except OSError: pass
    sub['files'] = files_info
    sub['parsed_disputes'] = parsed
    sub['status'] = 'parsed'
    all_items = []
    for dtype, info in parsed.items():
        for item in info['items']:
            all_items.append(dict(type=dtype, label=info['label'], text=item))
    sub['dispute_items'] = all_items
    store_submission(sid, sub)
    return jsonify(ok=True, files_received=len(files_info),
                   parsed_disputes=parsed, dispute_items=all_items)


# Step 3 — Review & Generate Letters
@app.route('/api/review', methods=['POST'])
def api_review():
    sid = session.get('submission_id')
    sub = load_submission(sid) if sid else None
    if not sub:
        return jsonify(error='Session not found'), 400
    data = request.get_json()
    all_items = data.get('items', []) + data.get('custom_items', [])
    sub['dispute_items'] = all_items
    types_set = set()
    for item in all_items:
        types_set.add(item.get('type', 'unknown_accounts') if isinstance(item, dict) else 'unknown_accounts')
    # Enforce Gilmore dispute order
    sub['dispute_types'] = sorted(list(types_set), key=lambda t: GILMORE_ORDER.index(t) if t in GILMORE_ORDER else 99)
    sub['dispute_order'] = sub['dispute_types'][:]
    sub['status'] = 'reviewed'
    sub['updated_at'] = datetime.utcnow().isoformat()
    confirmation = gen_confirmation()
    sub['confirmation'] = confirmation
    # Init status tracking per item
    for item in all_items:
        if isinstance(item, dict):
            key = hashlib.md5(item.get('text', '').encode()).hexdigest()[:12]
            sub.setdefault('status_per_item', {})[key] = 'pending'
    items_by_type = {}
    for item in all_items:
        if isinstance(item, dict):
            items_by_type.setdefault(item.get('type', 'unknown_accounts'), []).append(item.get('text', ''))
        else:
            items_by_type.setdefault('unknown_accounts', []).append(str(item))
    sub['letters'] = generate_letters(sub['dispute_types'], items_by_type,
                                       dict(name=sub['name'], confirmation=confirmation,
                                            state=sub.get('state', '')))
    store_submission(sid, sub)
    database.save_client(sub)
    return jsonify(ok=True, confirmation=confirmation, dispute_types=sub['dispute_types'],
                   dispute_order=sub['dispute_order'], letter_count=len(sub['letters']), items=all_items)


# Step 4 — Stripe Checkout
@app.route('/api/create-checkout', methods=['POST'])
def api_create_checkout():
    sid = session.get('submission_id')
    sub = load_submission(sid) if sid else None
    if not sub:
        return jsonify(error='Session not found'), 400
    if not stripe.api_key:
        sub['paid'] = True
        sub['status'] = 'paid'
        sub['paid_at'] = datetime.utcnow().isoformat()
        store_submission(sid, sub)
        return jsonify(ok=True, dev_mode=True, message='Payment skipped (dev mode)')
    try:
        cs = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price_data': {
                'currency': 'usd',
                'product_data': {'name': '5-Min Credit Fix -- Dispute Letter Package',
                                 'description': f'{len(sub.get("letters", []))} dispute letters for all 3 bureaus'},
                'unit_amount': PRICE_CENTS}, 'quantity': 1}],
            mode='payment',
            success_url=request.host_url.rstrip('/') + f'/api/payment-success?sid={sid}&ss={{CHECKOUT_SESSION_ID}}',
            cancel_url=request.host_url.rstrip('/') + '/#step-4',
            metadata={'submission_id': sid})
        return jsonify(ok=True, checkout_url=cs.url, session_id=cs.id)
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.route('/api/manual-pay', methods=['POST'])
def api_manual_pay():
    """Cash App / Chime manual payment — marks as pending-verify, admin approves."""
    sid = session.get('submission_id')
    sub = load_submission(sid) if sid else None
    if not sub:
        return jsonify(error='Session not found'), 400
    data = request.get_json()
    method = data.get('method', 'cashapp')
    sub['payment_method'] = method
    _mark_paid(sub, sid)
    return jsonify(ok=True, confirmation=sub.get('confirmation'))


@app.route('/api/payment-success')
def api_payment_success():
    sid = request.args.get('sid', session.get('submission_id'))
    if sid:
        session['submission_id'] = sid
        sub = load_submission(sid)
        if sub:
            _mark_paid(sub, sid)
    return redirect('/#step-5')


@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig = request.headers.get('Stripe-Signature')
    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
        except Exception:
            abort(400)
    else:
        event = json.loads(payload)
    if event.get('type') == 'checkout.session.completed':
        sid = event['data']['object'].get('metadata', {}).get('submission_id')
        if sid and sid in submissions:
            sub = load_submission(sid)
            if sub:
                sub['paid'] = True
                sub['status'] = 'paid'
                sub['paid_at'] = datetime.utcnow().isoformat()
                store_submission(sid, sub)
    return jsonify(received=True)


# Letters (requires payment)
@app.route('/api/letters')
def api_letters():
    sid = session.get('submission_id')
    sub = load_submission(sid) if sid else None
    if not sub:
        return jsonify(error='Session not found'), 400
    if not sub.get('paid'):
        return jsonify(error='Payment required', paid=False), 403
    return jsonify(ok=True, confirmation=sub.get('confirmation'), name=sub.get('name'),
                   letters=sub.get('letters', []), dispute_types=sub.get('dispute_types', []))


# Send via Certified Mail (Click2Mail)
CLICK2MAIL_URL = 'https://rest.click2mail.com/molpro'

BUREAU_ADDRESSES = {
    'Equifax': {'name': 'Equifax Information Services', 'address': 'PO Box 740256', 'city': 'Atlanta', 'state': 'GA', 'zip': '30374'},
    'TransUnion': {'name': 'TransUnion Consumer Solutions', 'address': 'PO Box 2000', 'city': 'Chester', 'state': 'PA', 'zip': '19016'},
    'Experian': {'name': 'Experian Disputes', 'address': 'PO Box 4500', 'city': 'Allen', 'state': 'TX', 'zip': '75013'},
}

@app.route('/api/send-certified', methods=['POST'])
def api_send_certified():
    sid = session.get('submission_id')
    sub = load_submission(sid) if sid else None
    if not sub:
        return jsonify(error='Session not found'), 400
    if not sub.get('paid'):
        return jsonify(error='Payment required'), 403
    if not CLICK2MAIL_API_KEY:
        return jsonify(error='Click2Mail not configured', sent=0), 503

    letters = sub.get('letters', [])
    if not letters:
        return jsonify(error='No letters generated', sent=0), 400

    data = request.get_json(silent=True) or {}
    day_number = data.get('dayNumber', 0)
    manual_class = data.get('mailClass', '')

    # Escalating mail classes by follow-up day
    if manual_class in ('First Class', 'Certified Mail'):
        mail_class = manual_class
        return_receipt = manual_class == 'Certified Mail'
        cfpb_notice = False
    elif day_number >= 90:
        mail_class = 'Certified Mail'
        return_receipt = True
        cfpb_notice = True
    elif day_number >= 60:
        mail_class = 'Certified Mail'
        return_receipt = True
        cfpb_notice = False
    elif day_number >= 30:
        mail_class = 'Certified Mail'
        return_receipt = False
        cfpb_notice = False
    else:
        mail_class = 'First Class'
        return_receipt = False
        cfpb_notice = False

    sender_name = sub.get('name', '')
    sender_address = sub.get('address', '')
    sender_state = sub.get('state', '')

    sent = 0
    job_ids = []
    errors = []

    for letter in letters:
        bureau = letter.get('bureau', '')
        bureau_addr = BUREAU_ADDRESSES.get(bureau)
        if not bureau_addr:
            continue

        # Append CFPB complaint notice for 90-day escalation
        doc_body = letter.get('body', '')
        if cfpb_notice and 'CFPB COMPLAINT NOTICE' not in doc_body:
            doc_body += '\n\n--- CFPB COMPLAINT NOTICE ---\n'
            doc_body += 'This letter is being sent simultaneously with a formal complaint '
            doc_body += 'to the Consumer Financial Protection Bureau (CFPB) at '
            doc_body += 'consumerfinance.gov/complaint, the Federal Trade Commission (FTC), '
            doc_body += f'and the {STATE_LAWS.get(sender_state, {}).get("name", "state")} '
            doc_body += 'Attorney General regarding your continued non-compliance with the '
            doc_body += 'Fair Credit Reporting Act.\n'

        try:
            payload = {
                'username': CLICK2MAIL_API_KEY,
                'documentClass': 'Letter 8.5 x 11',
                'layout': 'Address on Separate Page',
                'productionTime': 'Next Day',
                'envelope': 'Flat #10 pointed flap',
                'color': 'Full Color',
                'paperType': 'White 24#',
                'printOption': 'Printing One side',
                'mailClass': mail_class,
                'mailTracking': mail_class,
                'returnEnvelope': 'Return Envelope' if return_receipt else 'No',
                'returnReceipt': 'Yes' if return_receipt else 'No',
                'sender_name': sender_name,
                'sender_address1': sender_address,
                'sender_state': sender_state,
                'recipient_name': bureau_addr['name'],
                'recipient_address1': bureau_addr['address'],
                'recipient_city': bureau_addr['city'],
                'recipient_state': bureau_addr['state'],
                'recipient_zip': bureau_addr['zip'],
                'document': doc_body,
            }

            resp = http_requests.post(
                CLICK2MAIL_URL,
                json=payload,
                headers={
                    'Authorization': f'Bearer {CLICK2MAIL_API_KEY}',
                    'Content-Type': 'application/json',
                },
                timeout=30,
            )

            if resp.status_code in (200, 201):
                resp_data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
                job_id = resp_data.get('id', resp_data.get('jobId', f'job-{sent+1}'))
                job_ids.append({'bureau': bureau, 'job_id': str(job_id), 'title': letter.get('title', '')})
                sent += 1
            else:
                errors.append({'bureau': bureau, 'status': resp.status_code, 'detail': resp.text[:200]})

        except Exception as e:
            errors.append({'bureau': bureau, 'error': str(e)})

    return jsonify(ok=True, sent=sent, job_ids=job_ids, errors=errors if errors else None)


# Status
@app.route('/api/status/<confirmation>')
def api_status(confirmation):
    for e in admin_log:
        if e.get('confirmation') == confirmation:
            return jsonify(found=True, status=e['status'], dispute_count=e.get('dispute_count', 0),
                           created_at=e.get('created_at'))
    return jsonify(found=False), 404


# Admin
@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')


@app.route('/admin/auth', methods=['POST'])
def admin_auth():
    if request.form.get('key') == ADMIN_KEY:
        session['admin_key'] = ADMIN_KEY
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))


@app.route('/admin')
@require_admin
def admin_dashboard():
    stats = database.get_stats()
    clients = database.get_all_clients_admin()
    return render_template('admin.html', entries=clients, stats=stats)


@app.route('/admin/api/submissions')
@require_admin
def admin_api_submissions():
    stats = database.get_stats()
    clients = database.get_all_clients_admin()
    return jsonify(entries=clients, stats=stats)


@app.route('/admin/api/run-followups', methods=['POST'])
@require_admin
def admin_run_followups():
    """Manually trigger follow-up check."""
    import followup
    count = followup.check_and_send_followups()
    return jsonify(ok=True, processed=count)


@app.route('/admin/api/run-purge', methods=['POST'])
@require_admin
def admin_run_purge():
    """Manually trigger 90-day purge."""
    deleted = database.delete_expired_clients()
    return jsonify(ok=True, deleted=deleted)


# --- Follow-up letters (after payment) ---

@app.route('/api/followup-letters/<int:day>')
def api_followup_letters(day):
    """Get follow-up letters for a specific day mark (30, 60, 90)."""
    if day not in (30, 60, 90):
        return jsonify(error='Invalid day'), 400
    sid = session.get('submission_id')
    sub = load_submission(sid) if sid else None
    if not sub:
        return jsonify(error='Session not found'), 400
    if not sub.get('paid'):
        return jsonify(error='Payment required'), 403
    import followup
    letters = followup.generate_followup_letters(sub, day)
    return jsonify(ok=True, letters=letters, day=day)


# ═════════════════════════════════════════════════════════════════════════════
# BACKGROUND JOBS — follow-up engine + auto-delete
# ═════════════════════════════════════════════════════════════════════════════

def _background_jobs():
    """Daily background job: run follow-ups, purge expired records."""
    while True:
        time.sleep(86400)  # 24 hours
        try:
            import followup
            followup.check_and_send_followups()
        except Exception as e:
            print(f"[BG JOB ERROR] follow-up: {e}")
        try:
            database.delete_expired_clients()
        except Exception as e:
            print(f"[BG JOB ERROR] purge: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# STARTUP
# ═════════════════════════════════════════════════════════════════════════════

database.init_db()

# Start background job thread (daemon = dies with main process)
_bg_thread = threading.Thread(target=_background_jobs, daemon=True)
_bg_thread.start()

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
