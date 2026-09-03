import asyncio
import base64
import dataclasses
import hmac
import json
import re
import sqlite3
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import stripe
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

import config
import outcomes
import print_packet
import provenance
import relief_pathways
import signature as sig
import watcher
from ae_creditfix.case import Case, Client, Item, new_id
from ae_creditfix.letters import (
    gen_cover_sheet,
    gen_followup_letters,
    gen_letters,
    state_from_address,
)
from ae_creditfix.templates import BUREAU_ADDRESSES
from cleanup import cleanup_loop
from cypher import encrypt_file_in_memory, generate_session_key
from database import CaseRecord, get_db, init_db
from disclosures import (
    acknowledgement_record,
    disclosure_payload,
    missing_acknowledgements,
)
from dispute_engine import engine_manifest, ladder_summary, tier_for_day
from dispute_engine.categories import DISPUTE_CATEGORIES, all_categories
from email_sender import send_letters_email
from fishbowl import check_beta_eligibility, get_fishbowl_status
from letter_preview import preview_summary, redact_letters
from mail_service import send_all_letters, verify_webhook_signature
from money import money_str, parse_money
from pdf_gen import build_letter_pdf
from report_parser import parse_credit_report_bytes
from terms_token import issue_token, verify_token
from watcher_loop import watcher_loop

stripe.api_key = config.STRIPE_SECRET_KEY

if config.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        environment=config.ENVIRONMENT,
        traces_sample_rate=0.1,
        # PII never leaves the box: no request bodies, no user context.
        send_default_pii=False,
        max_request_body_size="never",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Two background passes. Cleanup destroys expired cases; the watcher loop
    # sends milestone reminders. The watcher has to run out here rather than
    # in a request handler, because the consumer who most needs the reminder
    # is precisely the one who never comes back to trigger it.
    tasks = [
        asyncio.create_task(cleanup_loop()),
        asyncio.create_task(watcher_loop()),
    ]
    yield
    for task in tasks:
        task.cancel()


app = FastAPI(title="AE 5-Min Credit Fix", lifespan=lifespan)
# key_style="endpoint" buckets by (client IP, view function). slowapi's default
# is "url", which buckets by the *concrete* request path — so every limit on a
# route carrying {session_id} was scoped to one session and a caller got a fresh
# budget for each new session id. Measured: 20 subscribes across 20 sessions
# never tripped a declared 10/hour, while 13 on one session tripped at the 11th.
# Only the parameterless routes (/api/terms/accept, /api/case) ever limited.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=config.RATE_LIMIT_STORAGE_URI,
    key_style="endpoint",
)
app.state.limiter = limiter

init_db()
# The audit chain lives in its own SQLite file, so init_db() does not reach it.
# Every provenance.record() call reads the previous hash first, which means a
# missing table throws on the first write rather than degrading — and two of
# those call sites are on the payment path.
provenance.init_audit()
# The outcome ledger is a third SQLite file and needs the same treatment. Until
# this ran, `dispute_outcomes` did not exist, every `outcomes.removal_rate()`
# lookup raised, and `scoring` silently fell back to its hardcoded priors while
# still offering a "measured (n=…)" label it could never produce.
outcomes.init_outcomes()

UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests. Please try again later."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)


# --- Helpers ---

def get_case(session_id: str, db: Session) -> CaseRecord:
    record = db.query(CaseRecord).filter_by(session_id=session_id).first()
    if not record:
        raise HTTPException(404, "Session not found")
    return record


# The three documents a case needs before it can produce letters.
DOC_TYPES: frozenset[str] = frozenset({"id", "address", "report"})


def attachment_names(record: CaseRecord) -> list[str]:
    """
    Uploaded filenames, in upload order.

    Attachments are stored as {"filename", "doc_type"} dicts. Rows written
    before uploads carried a type hold bare strings, so both shapes are read.
    """
    names: list[str] = []
    for entry in record.attachments or []:
        if isinstance(entry, dict):
            name = entry.get("filename")
            if name:
                names.append(str(name))
        elif entry:
            names.append(str(entry))
    return names


def attachment_doc_types(record: CaseRecord) -> set[str]:
    """
    Which of DOC_TYPES this case actually holds.

    An untyped legacy attachment contributes nothing: we cannot claim a file
    proves identity when the record never recorded what it was.
    """
    return {
        entry["doc_type"]
        for entry in record.attachments or []
        if isinstance(entry, dict) and entry.get("doc_type") in DOC_TYPES
    }


def to_engine_case(record: CaseRecord) -> Case:
    """Convert DB record to ae_creditfix Case for letter generation."""
    client = Client(
        name=record.name,
        address=record.address,
        dob=record.dob,
        ssn_last4=record.ssn_last4,
        phone=record.phone,
        email=record.email,
        city=record.city or "",
        state=record.state or "",
        zip_code=record.zip_code or "",
    )
    # Only the fields `Item` declares. A stored item also carries what the
    # parser read (furnisher, dofd, scored categories) for the dispute_engine,
    # which reads `record.items` directly; passing those to this older
    # dataclass raised TypeError and took letter generation out entirely.
    item_fields = {f.name for f in dataclasses.fields(Item)}
    items = [
        Item(**{k: v for k, v in item.items() if k in item_fields})
        for item in (record.items or [])
    ]
    case = Case(client=client, items=items, attachments=attachment_names(record))
    case.phases["p1_docs_complete"] = record.docs_complete
    return case


def build_case_pdf(record: CaseRecord) -> bytes:
    """Regenerate the letter-packet PDF in memory (never stored on disk)."""
    client_dict = {
        "name": record.name, "address": record.address, "dob": record.dob,
        "ssn_last4": record.ssn_last4, "phone": record.phone, "email": record.email,
    }
    return build_letter_pdf(record.session_id, client_dict, record.letters or [],
                            signature_record=record.signature or None)


def _demo_tracking(letters: list) -> list:
    """Realistic-looking tracking data for demo mode."""
    results = []
    for ltr in letters:
        results.append({
            "target": ltr.get("target", "Bureau"),
            "tracking_number": f"9400111899{uuid.uuid4().hex[:12].upper()}",
            "expected_delivery": (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d"),
            "status": "demo — would mail via USPS",
        })
    return results


def _record_dispatched_disputes(record: CaseRecord, tier: int) -> None:
    """
    Log every item in a mailed round to the outcome ledger.

    Called only where real postage was bought. A demo dispatch fabricates its
    tracking numbers, and writing those would put disputes that were never
    mailed into the denominator that every future removal rate is measured
    against — the ledger would be reporting on letters nobody sent.

    `record_dispute` inserts OR IGNORE on (case, item, tier), so re-running a
    dispatch cannot double-count a round.

    A ledger failure must never break a dispatch: by the time this runs the
    letters are already with Lob, and the ledger is an observer, not part of
    the transaction. So it is logged and swallowed rather than raised — losing
    a statistic is recoverable, turning a successful mailing into a 500 on the
    payment path is not.
    """
    # `address` is the street line only now, so the state comes from its own
    # column rather than being mined back out of free text.
    state = (record.state or "") or state_from_address(record.address or "")
    for item in record.items or []:
        try:
            outcomes.record_dispute(
                record.session_id,
                item,
                bureau=item.get("target", ""),
                tier=tier,
                state=state,
            )
        except sqlite3.Error as e:
            print(f"[outcomes] record_dispute failed ({type(e).__name__}); "
                  f"dispatch unaffected")


# --- Validation models ---

US_STATE_CODES = frozenset(["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC", "AS", "GU", "MP", "PR", "VI", "AA", "AE", "AP"])


class CreateCaseRequest(BaseModel):
    name: str
    # Street line only — city/state/zip are collected separately so the mail
    # carrier receives them as the discrete fields it requires.
    address: str
    city: str
    state: str
    zip: str
    dob: str
    ssn_last4: str
    phone: str
    email: str

    @field_validator("ssn_last4")
    @classmethod
    def validate_ssn(cls, v):
        if not re.match(r"^\d{4}$", v):
            raise ValueError("SSN last 4 must be exactly 4 digits")
        return v

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v):
        try:
            dt = datetime.strptime(v, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if dt.year < 1920 or dt > datetime.now(timezone.utc):
                raise ValueError
        except ValueError:
            raise ValueError("DOB must be a valid date in YYYY-MM-DD format")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        digits = re.sub(r"[^\d]", "", v)
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("Phone must be 10-15 digits")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name is required")
        return v.strip()

    @field_validator("address")
    @classmethod
    def validate_address(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Street address is required")
        return v.strip()

    @field_validator("city")
    @classmethod
    def validate_city(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("City is required")
        return v.strip()

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        # Two-letter USPS code. The mail carrier rejects anything else, and a
        # rejected mailing is currently invisible to the customer.
        code = v.strip().upper()
        if code not in US_STATE_CODES:
            raise ValueError("State must be a 2-letter US state code, e.g. TX")
        return code

    @field_validator("zip")
    @classmethod
    def validate_zip(cls, v):
        code = v.strip()
        if not re.fullmatch(r"\d{5}(-\d{4})?", code):
            raise ValueError("ZIP must be 5 digits, or ZIP+4")
        return code


class ManualPayRequest(BaseModel):
    method: str
    # The customer's OWN Cash App cashtag or Chime handle. Matching a random
    # code buried in a payment note is slow and error-prone; knowing who is
    # about to send money makes the admin release a two-second check.
    payer_handle: str = ""

    @field_validator("method")
    @classmethod
    def validate_method(cls, v):
        if v not in ("cashapp", "chime"):
            raise ValueError("Method must be 'cashapp' or 'chime'")
        return v

    @field_validator("payer_handle")
    @classmethod
    def validate_payer_handle(cls, v):
        v = (v or "").strip()
        if not v:
            return ""
        if not v.startswith("$"):
            v = "$" + v.lstrip("@$")
        if len(v) > 32 or not re.match(r"^\$[A-Za-z0-9_.-]{1,30}$", v):
            raise ValueError("Enter a valid cashtag, e.g. $yourname")
        return v


class SignatureRequest(BaseModel):
    """A captured signature from the in-app signing pad."""
    signature: str = ""      # data:image/png;base64,...
    typed_name: str = ""     # full legal name, typed to confirm intent


class AcknowledgeRequest(BaseModel):
    """The consumer's affirmations from the consent screen."""
    acknowledgements: dict = {}

    @field_validator("acknowledgements")
    @classmethod
    def validate_acks(cls, v):
        if not isinstance(v, dict):
            return {}
        return {str(k)[:48]: bool(val) for k, val in v.items()}


class DisputeItem(BaseModel):
    type: str
    target: str
    account: str
    # Decimal, never float. Pydantic parses the decimal string the parsers
    # emit into an exact value; a JSON number would already be a float by the
    # time it arrived. See money.py.
    amount: Decimal | None = None
    opened: str | None = None
    reason: str
    # Dispute category from the engine taxonomy. Unknown values are dropped
    # rather than rejected: the engine re-derives one from the reason text.
    bucket: str = ""

    # ── What the parser read off the file ────────────────────────────────
    # These used to stop here. The review round-trip posted six fields, so
    # everything the parser worked out was thrown away between the upload and
    # the letter: the furnisher's name fell back to `target` and every item in
    # an Experian letter was printed as "Account Name: Experian", and with no
    # scored categories every item reached the letter through the fallback
    # section instead of a matched violation theory.
    furnisher: str = ""
    dofd: str | None = None
    original_creditor: str = ""
    highest_balance: Decimal | None = None
    falloff_status: str = ""
    # Grounds the parser scored on this tradeline, each {category, strength,
    # evidence, derived?}. Entries that do not name a known category are
    # dropped; the analyst re-derives one rather than arguing an unknown.
    categories: list[dict] = []

    # The consumer's own answers for this item. Only recognised affirmation
    # keys survive; anything else is discarded.
    affirmations: dict = {}

    @field_validator("amount", "highest_balance", mode="before")
    @classmethod
    def parse_amount(cls, v):
        """
        Blank means the report showed no figure, which is not zero.

        The parsers write "" for an absent balance — 8 of 20 items on a real
        Experian file — and Pydantic cannot turn that into a Decimal, so the
        whole dispute list was rejected with 422 and no letters could be
        generated. `parse_money` reads what is there and returns None for what
        is not.
        """
        return parse_money(v)

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, v):
        return v if v in DISPUTE_CATEGORIES else ""

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v):
        if not isinstance(v, list):
            return []
        cleaned = []
        for entry in v[:12]:
            if not isinstance(entry, dict):
                continue
            category = str(entry.get("category", ""))
            if category not in DISPUTE_CATEGORIES:
                continue
            strength = str(entry.get("strength", "moderate"))
            cleaned.append({
                "category": category,
                "strength": strength if strength in ("strong", "moderate", "weak") else "moderate",
                "evidence": str(entry.get("evidence", ""))[:400],
                "derived": bool(entry.get("derived", False)),
            })
        return cleaned

    @field_validator("affirmations")
    @classmethod
    def validate_affirmations(cls, v):
        if not isinstance(v, dict):
            return {}
        allowed = {
            "not_recognized", "confirmed_fraud", "uncertain_chain",
            "address_mismatch", "dofd_uncertain", "dates_inconsistent",
            "name_not_mine", "no_validation_received", "ftc_report_number",
            "exclude",
        }
        cleaned = {}
        for key, val in v.items():
            if key not in allowed:
                continue
            if key == "ftc_report_number":
                cleaned[key] = str(val)[:64]
            else:
                cleaned[key] = bool(val)
        return cleaned

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ("bureau", "creditor"):
            raise ValueError("Type must be 'bureau' or 'creditor'")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Dispute reason is required")
        return v.strip()


class ConfirmDisputesRequest(BaseModel):
    items: list[DisputeItem]


# ======================================================================
# Health
# ======================================================================

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ======================================================================
# STEP 1 — Terms, create case, upload docs
# ======================================================================

@app.post("/api/terms/accept")
@limiter.limit("10/minute")
async def accept_terms(request: Request):
    """
    Record terms/disclaimer acceptance. Returns a signed, short-lived token
    (no server state, no PII) to pass with case creation.
    """
    token, accepted_at = issue_token()
    return {"terms_token": token, "accepted_at": accepted_at.isoformat()}


@app.post("/api/case")
@limiter.limit("10/minute")
async def create_case(req: CreateCaseRequest, request: Request, db: Session = Depends(get_db)):
    # Consent gate: no case without a valid terms token
    terms_token = request.headers.get("X-Terms-Token", "")
    accepted_at = verify_token(terms_token)
    if accepted_at is None:
        raise HTTPException(422, "You must accept the terms and disclaimer before proceeding")

    # Trapdoor Fishbowl — check beta region eligibility by zip code
    # The ZIP is now its own validated field, so eligibility no longer has to
    # guess which 5-digit run in a free-text address is the postcode rather
    # than the street number.
    eligibility = check_beta_eligibility(req.zip, db)
    if not eligibility["eligible"]:
        raise HTTPException(403, eligibility["reason"])

    # Per-session upload encryption key
    client_ip = get_remote_address(request)
    _key_id, raw_key = generate_session_key(client_ip)

    session_id = uuid.uuid4().hex[:12]
    record = CaseRecord(
        session_id=session_id,
        name=req.name,
        address=req.address,
        city=req.city,
        state=req.state,
        zip_code=req.zip,
        dob=req.dob,
        ssn_last4=req.ssn_last4,
        phone=req.phone,
        email=req.email,
        region=eligibility["region"],
        cypher_key_enc=base64.b64encode(raw_key).decode("ascii"),
        terms_accepted_at=accepted_at.replace(tzinfo=None),
    )
    db.add(record)
    db.commit()
    return {
        "session_id": session_id,
        "status": "created",
        "region": eligibility["region_name"],
        "queue_position": eligibility["queue_position"],
    }


@app.get("/api/fishbowl/status")
async def fishbowl_status(db: Session = Depends(get_db)):
    """Check current fishbowl queue status for all beta regions."""
    return get_fishbowl_status(db)


@app.post("/api/case/{session_id}/upload")
@limiter.limit("20/minute")
async def upload_doc(
    session_id: str,
    request: Request,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    db: Session = Depends(get_db),
):
    record = get_case(session_id, db)

    # What the document IS has to come over the wire. Without it this endpoint
    # ran every upload through the credit-report parser, and a bank statement
    # sent to prove an address came back as three dispute items built from the
    # account's opening balance, closing balance and monthly service fee — one
    # of them asserting the account was not the customer's. That is a false
    # statement to a bureau manufactured out of a document nobody disputed.
    doc_type = (doc_type or "").strip().lower()
    if doc_type not in DOC_TYPES:
        raise HTTPException(
            422,
            f"doc_type must be one of {', '.join(sorted(DOC_TYPES))} — got {doc_type!r}",
        )

    # Validate file type
    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".csv"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"File type {suffix} not allowed. Accepted: {', '.join(sorted(allowed))}")

    # Validate file size (10MB max)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 10MB.")

    # Parse before persisting, so a file we are going to reject does not leave
    # a stored blob and an attachment row behind it.
    suggestions: list[dict] = []
    if doc_type == "report":
        if suffix not in (".pdf", ".txt", ".csv"):
            raise HTTPException(
                400,
                f"A credit report has to be the bureau's own export — {suffix} cannot be "
                "read as one. Download the report from the bureau and upload that file.",
            )
        suggestions = parse_credit_report_bytes(content, suffix)
        if not suggestions:
            # Name the way out. This fires for a TransUnion export, which no
            # parser reads yet, and for photos and screenshots — and a bare
            # "could not read this" leaves a paying customer with nowhere to
            # go. Equifax is named because it measured best across all three
            # exports of the same file, not as a preference.
            raise HTTPException(
                422,
                "We could not read this file as a credit report. Get a free report at "
                "annualcreditreport.com and choose Equifax — we tested all three and that "
                "export gives your letters the most to work with. Use the site's own "
                "Download or Save-as-PDF option; a photo or screenshot of a report cannot "
                "be read.",
            )

    # Encrypt with the per-session key before writing — plaintext never
    # touches disk. Stored name is opaque (no user-controlled path parts).
    session_key = base64.b64decode(record.cypher_key_enc)
    upload_dir = UPLOADS_DIR / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    encrypted = encrypt_file_in_memory(content, session_key)
    (upload_dir / f"{uuid.uuid4().hex[:8]}{suffix}.enc").write_bytes(encrypted)

    # Copy before append: assigning the same (mutated) list object back would
    # not be detected as a change by SQLAlchemy and the update would be lost
    attachments = list(record.attachments or [])
    attachments.append({"filename": file.filename, "doc_type": doc_type})
    record.attachments = attachments
    # Complete means all three kinds are in hand. Flipping this on the first
    # upload of any kind unsheathed the sword after one file and let a case
    # reach letter generation with no credit report in it at all.
    record.docs_complete = DOC_TYPES.issubset(attachment_doc_types(record))
    db.commit()

    return {
        "filename": file.filename,
        "doc_type": doc_type,
        "attachments": attachment_names(record),
        "docs_complete": record.docs_complete,
        "missing": sorted(DOC_TYPES - attachment_doc_types(record)),
        "suggestions": suggestions,
    }


# ======================================================================
# STEP 2 — Confirm disputes
# ======================================================================

@app.post("/api/case/{session_id}/disputes")
@limiter.limit("10/minute")
async def confirm_disputes(session_id: str, req: ConfirmDisputesRequest, request: Request, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    items = list(record.items or [])
    for item in req.items:
        items.append({
            "id": new_id("ITM"),
            "type": item.type,
            "target": item.target,
            "account": item.account,
            # Exact decimal strings in the JSON column. `Decimal` is not JSON
            # serialisable and the encoder's fallback is float, which is the
            # representation this is here to avoid.
            "amount": money_str(item.amount),
            "opened": item.opened,
            "reason": item.reason,
            "status": "open",
            "letters": [],
            "bucket": item.bucket,
            "affirmations": item.affirmations,
            # Everything the parser read. Rebuilding the item field-by-field
            # without these was the second place the parser's work was lost:
            # the model carried them and this loop dropped them again.
            "furnisher": item.furnisher,
            "dofd": item.dofd,
            "original_creditor": item.original_creditor,
            "highest_balance": money_str(item.highest_balance),
            "falloff_status": item.falloff_status,
            "categories": item.categories,
            "category_count": len(item.categories),
        })
    record.items = items
    db.commit()
    return {"items_count": len(items)}


# ======================================================================
# STEP 3 — Generate & review letters
# ======================================================================

@app.get("/api/disclosures")
async def get_disclosures():
    """What the consumer must be shown before they can generate letters."""
    return disclosure_payload()


@app.post("/api/case/{session_id}/acknowledge")
@limiter.limit("10/minute")
async def acknowledge(session_id: str, req: AcknowledgeRequest, request: Request,
                      db: Session = Depends(get_db)):
    """
    Record the consumer's acknowledgements. Required before letters generate.

    Stores only which statements were affirmed, the version of the text shown,
    and a timestamp — no PII beyond a hashed IP.
    """
    record_row = get_case(session_id, db)
    missing = missing_acknowledgements(req.acknowledgements)
    if missing:
        raise HTTPException(400, f"Missing acknowledgements: {', '.join(missing)}")

    ack = acknowledgement_record(req.acknowledgements, get_remote_address(request))

    record_row.acknowledgements = ack
    record_row.acknowledged_at = datetime.now(timezone.utc)
    db.commit()

    provenance.record(session_id, "acknowledgements_given",
                      {"version": ack["version"], "count": len(ack["acknowledged"])})
    return {"ok": True, "acknowledged": ack["acknowledged"], "version": ack["version"]}


@app.post("/api/case/{session_id}/sign")
@limiter.limit("10/minute")
async def sign_letters(session_id: str, req: SignatureRequest, request: Request,
                       db: Session = Depends(get_db)):
    """
    Capture the consumer's signature once; every letter goes out signed.

    This is what closes the mailing loop — without it the consumer would
    have to print, sign and post the packet back before anything could be
    mailed on their behalf.
    """
    record = get_case(session_id, db)
    try:
        rec = sig.signature_record(
            req.signature,
            req.typed_name,
            client_ip=get_remote_address(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except sig.SignatureError as e:
        raise HTTPException(400, str(e))

    record.signature = rec
    record.signed_at = datetime.now(timezone.utc)
    db.commit()

    provenance.record(session_id, "letters_signed",
                      {"bytes": rec["bytes"], "name_len": len(rec["typed_name"])})

    return {
        "ok": True,
        "signed_at": rec["signed_at"],
        "attestation": sig.attestation_line(rec),
    }


@app.get("/api/case/{session_id}/signature-status")
async def signature_status(session_id: str, db: Session = Depends(get_db)):
    """Whether this case has been signed — drives the gate page's UI."""
    record = get_case(session_id, db)
    rec = record.signature or None
    return {
        "signed": bool(rec),
        "signed_at": rec.get("signed_at") if rec else None,
        "typed_name": rec.get("typed_name") if rec else None,
    }


@app.post("/api/case/{session_id}/letters")
@limiter.limit("5/minute")
async def generate_letters(session_id: str, request: Request, db: Session = Depends(get_db)):
    record = get_case(session_id, db)

    # Disclosures are not optional. A consumer cannot generate letters in
    # their own name without first affirming they know what this is, what it
    # is not, and that they could do it themselves for free.
    ack = record.acknowledgements or {}
    if not ack.get("complete"):
        raise HTTPException(
            428,
            "Required disclosures have not been acknowledged. "
            "GET /api/disclosures, then POST /api/case/{id}/acknowledge.",
        )

    case = to_engine_case(record)

    # Which round is due. Tier 1 until the first mailing goes out; after that
    # the ladder advances on the elapsed days since dispatch.
    tier = 1
    if record.mail_sent and record.mail_dispatched_at:
        elapsed = (datetime.now(timezone.utc) - record.mail_dispatched_at).days
        tier = tier_for_day(elapsed)

    prior_rounds = {
        t.get("target"): t for t in (record.mail_tracking or []) if t.get("target")
    }

    letters_data = gen_letters(case, tier=tier, prior_rounds=prior_rounds)

    # Every letter carries its own provenance: a visible case reference and
    # timestamp, plus an invisible fingerprint that survives copy-paste.
    issued = datetime.now(timezone.utc)
    letters_data = [provenance.stamp_letter(l, session_id, issued) for l in letters_data]

    cover_text = gen_cover_sheet(case)

    # Letters live only in the encrypted column; the PDF is built on demand.
    # The full text is always stored — the gate is on what we hand back.
    record.letters = letters_data
    db.commit()

    provenance.record(session_id, "letters_generated",
                      {"count": len(letters_data), "tier": tier, "paid": record.paid})

    return {
        "letters": redact_letters(letters_data, record.paid),
        "paid": record.paid,
        "summary": preview_summary(letters_data),
        "cover_sheet": cover_text,
        "total": len(letters_data),
        "tier": tier,
        "ladder": ladder_summary(),
    }


@app.get("/api/case/{session_id}/letters")
async def get_letters(session_id: str, db: Session = Depends(get_db)):
    """
    Unpaid callers get a preview: their own audit and the statutes, with the
    theory arguments and demands withheld. Paid callers get the real thing.
    """
    record = get_case(session_id, db)
    letters = record.letters or []
    return {
        "letters": redact_letters(letters, record.paid),
        "paid": record.paid,
        "summary": preview_summary(letters),
    }


# ======================================================================
# STEP 4 — Mail info + send
# ======================================================================

@app.get("/api/case/{session_id}/mail-info")
async def mail_info(session_id: str, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    targets = list({ltr["target"] for ltr in (record.letters or [])})
    mail_targets = [
        {"target": t, "address": BUREAU_ADDRESSES.get(t, "See letter for address")}
        for t in targets
    ]
    return {"mail_targets": mail_targets}


@app.post("/api/case/{session_id}/send-mail")
@limiter.limit("3/minute")
async def send_mail(session_id: str, request: Request, db: Session = Depends(get_db)):
    """Send all dispute letters via Lob (round 1 = First Class)."""
    record = get_case(session_id, db)
    if not record.paid:
        raise HTTPException(402, "Payment required before mailing")

    letters = record.letters or []
    if not letters:
        raise HTTPException(400, "No letters generated yet")

    tier = max((ltr.get("tier", 1) for ltr in letters), default=1)
    results, skipped = send_all_letters(
        record.name, record.address, letters, session_id, round_number=tier,
        client_city=record.city or "", client_state=record.state or "",
        client_zip=record.zip_code or "",
    )

    if not results and config.DEMO_MODE:
        demo_results = _demo_tracking(letters)
        return {
            "sent": len(demo_results),
            "tracking": demo_results,
            "message": f"DEMO MODE: {len(demo_results)} letter(s) staged. Connect Lob API key to send real mail.",
        }

    if results:
        record.mail_tracking = results
        record.mail_sent = True
        record.mail_dispatched_at = record.mail_dispatched_at or datetime.now(timezone.utc)
        record.mail_tier = max(record.mail_tier or 0, tier)
        db.commit()
        _record_dispatched_disputes(record, tier)

    # A partial send is not a send. Report exactly what went out and what did
    # not, so "2 of 3 mailed" can never read as success.
    if skipped and results:
        message = (f"Sent {len(results)} letter(s) via USPS. "
                   f"{len(skipped)} could not be mailed: "
                   + ", ".join(s["target"] for s in skipped))
    elif results:
        message = f"Sent {len(results)} letter(s) via USPS"
    else:
        message = "Lob not configured — print and mail manually (see instructions)"

    return {
        "sent": len(results),
        "skipped": skipped,
        "complete": bool(results) and not skipped,
        "tier": tier,
        "tracking": results,
        "message": message,
    }


@app.post("/api/webhooks/lob")
async def lob_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Lob delivery status webhooks."""
    body = await request.body()
    signature = request.headers.get("lob-signature", "")

    if not verify_webhook_signature(body, signature):
        raise HTTPException(401, "Invalid webhook signature")

    event = json.loads(body)
    event_type = event.get("event_type", {}).get("id", "")
    lob_letter = event.get("body", {})
    metadata = lob_letter.get("metadata", {})
    session_id = metadata.get("session_id", "")

    if session_id:
        record = db.query(CaseRecord).filter_by(session_id=session_id).first()
        if record:
            # Fresh dicts so SQLAlchemy sees the assignment as a change
            letters = [dict(ltr) for ltr in (record.letters or [])]
            target = metadata.get("target", "")
            for ltr in letters:
                if ltr.get("target") == target:
                    ltr["mail_status"] = event_type
                    ltr["tracking_number"] = lob_letter.get("tracking_number", "")
                    break
            record.letters = letters
            db.commit()

    return {"received": True}


# ======================================================================
# STEP 5 — Payment (Stripe Checkout)
# ======================================================================

@app.post("/api/case/{session_id}/checkout")
@limiter.limit("5/minute")
async def create_checkout(session_id: str, request: Request, db: Session = Depends(get_db)):
    """Create a Stripe Checkout session."""
    record = get_case(session_id, db)
    if record.paid:
        return {"already_paid": True, "session_id": session_id}

    if not config.STRIPE_SECRET_KEY:
        # DEMO_MODE allows completing the flow without Stripe (pre-keys launch);
        # dev always completes. Real production charges fail closed without a key.
        if config.IS_PROD and not config.DEMO_MODE:
            raise HTTPException(503, "Payments are not configured")
        record.paid = True
        db.commit()
        _post_payment(record, db)
        return {"demo_mode": True, "paid": True, "session_id": session_id}

    checkout = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "AE 5-Min Credit Fix — Dispute Letter Packet",
                    "description": "FCRA-compliant dispute letters for all 3 credit bureaus",
                },
                "unit_amount": config.STRIPE_PRICE_CENTS,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{config.FRONTEND_URL}/gate?session_id={session_id}&paid=true",
        cancel_url=f"{config.FRONTEND_URL}/stairway?session_id={session_id}",
        metadata={"session_id": session_id},
        customer_email=record.email,
    )
    record.stripe_session_id = checkout.id
    db.commit()
    return {"checkout_url": checkout.url}


@app.post("/api/case/{session_id}/manual-pay")
@limiter.limit("5/minute")
async def manual_pay(session_id: str, body: ManualPayRequest, request: Request, db: Session = Depends(get_db)):
    """
    Cash App / Chime: the customer sends money to our handle directly with a
    confirmation code in the payment note; admin verifies receipt and releases
    the letters via /api/admin/release/{session_id}.
    """
    record = get_case(session_id, db)
    if record.paid:
        return {"already_paid": True, "session_id": session_id}

    # Keep the same code across retries / method switches so the customer
    # never ends up with two codes for one case.
    if not record.manual_pay_code:
        record.manual_pay_code = f"CF-{uuid.uuid4().hex[:6].upper()}"
    record.manual_pay_method = body.method
    record.manual_pay_handle = body.payer_handle or None
    record.manual_pay_requested_at = datetime.now(timezone.utc)
    db.commit()

    provenance.record(session_id, "payment_requested",
                      {"method": body.method, "has_handle": bool(body.payer_handle)})

    handle = config.CASHAPP_CASHTAG if body.method == "cashapp" else config.CHIME_TAG
    return {
        "pending": True,
        "confirmation": record.manual_pay_code,
        "method": body.method,
        "handle": handle,
        "payer_handle": record.manual_pay_handle or "",
        "amount": config.PRICE_DISPLAY,
    }


@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook for payment confirmation."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if config.STRIPE_WEBHOOK_SECRET:
        # Verify the signature only; read fields from the parsed JSON below.
        # (construct_event returns a StripeObject whose dict interface differs
        # across library versions — .get() on it 500'd in production.)
        try:
            stripe.Webhook.construct_event(payload, sig_header, config.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            raise HTTPException(400, "Invalid webhook signature")
    elif config.IS_PROD:
        # Never accept unsigned payment events in production
        raise HTTPException(503, "Stripe webhook secret not configured")

    event = json.loads(payload)

    if event.get("type") == "checkout.session.completed":
        session_data = event["data"]["object"]
        session_id = session_data.get("metadata", {}).get("session_id")
        if session_id:
            record = db.query(CaseRecord).filter_by(session_id=session_id).first()
            if record and not record.paid:
                record.paid = True
                record.stripe_payment_intent = session_data.get("payment_intent")
                db.commit()
                _post_payment(record, db)

    return {"received": True}


def _post_payment(record: CaseRecord, db: Session):
    """Actions after successful payment: mail letters (round 1), email PDF."""
    letters = record.letters or []
    if letters and not record.mail_sent:
        # Postage comes off the letter's own tier, so round 2 goes certified
        # without anyone having to remember to say so.
        tier = max((ltr.get("tier", 1) for ltr in letters), default=1)
        results, skipped = send_all_letters(
            record.name, record.address, letters, record.session_id, round_number=tier,
            client_city=record.city or "", client_state=record.state or "",
            client_zip=record.zip_code or "",
        )
        if skipped:
            # Money has already been taken by this point. A letter that did not
            # go out has to leave a trace someone can act on.
            provenance.record(record.session_id, "mail_partial_failure",
                              {"sent": len(results), "skipped": skipped, "tier": tier})

        if results:
            record.mail_tracking = results
            record.mail_sent = True
        elif config.DEMO_MODE:
            record.mail_tracking = _demo_tracking(letters)
            record.mail_sent = True

        if record.mail_sent:
            record.mail_dispatched_at = record.mail_dispatched_at or datetime.now(timezone.utc)
            record.mail_tier = max(record.mail_tier or 0, tier)

        db.commit()

        # Only a real dispatch reaches the ledger — `results` is empty in demo
        # mode, where the tracking numbers above are generated, not bought.
        if results:
            _record_dispatched_disputes(record, tier)

    # Email PDF copy to client (PDF regenerated in memory)
    if letters and not record.email_sent:
        if config.DEMO_MODE:
            print("DEMO: Would email PDF (SMTP not configured)")
            record.email_sent = True
            db.commit()
        else:
            pdf_bytes = build_case_pdf(record)
            sent = send_letters_email(record.email, record.name, record.session_id, pdf_bytes)
            if sent:
                record.email_sent = True
                db.commit()


# ======================================================================
# Mail status / download (after payment)
# ======================================================================

@app.get("/api/case/{session_id}/mail-status")
async def mail_status(session_id: str, db: Session = Depends(get_db)):
    """Get mail tracking status for a paid case."""
    record = get_case(session_id, db)
    if not record.paid:
        raise HTTPException(402, "Payment required")
    tracking = record.mail_tracking or []
    status = "sent" if record.mail_sent else "processing"
    return {"status": status, "tracking": tracking}


@app.get("/api/case/{session_id}/download")
async def download_letters(session_id: str, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    if not record.paid:
        raise HTTPException(402, "Payment required")
    if not record.letters:
        raise HTTPException(404, "Letters not found — please regenerate")
    pdf_bytes = build_case_pdf(record)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="AE_CreditFix_Letters_{session_id}.pdf"'},
    )


# ======================================================================
# Session resume
# ======================================================================

@app.get("/api/case/{session_id}/status")
async def case_status(session_id: str, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    return {
        "session_id": record.session_id,
        "name": record.name,
        "email": record.email,
        "docs_complete": record.docs_complete,
        "items_count": len(record.items or []),
        "letters_count": len(record.letters or []),
        "paid": record.paid,
        "email_sent": record.email_sent,
        "mail_sent": record.mail_sent,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        # Manual pay (Cash App / Chime) — lets the payment page restore its
        # "pending verification" panel after a refresh.
        "manual_pay_pending": bool(record.manual_pay_requested_at and not record.paid),
        "manual_pay_method": record.manual_pay_method,
        "manual_pay_code": record.manual_pay_code,
    }


# ======================================================================
# The Watcher — 30/60/90-day tracking
# ======================================================================

class WatcherSubscribeRequest(BaseModel):
    notify_method: str = "email"
    notify_handle: str = ""
    # The consumer has to actively agree to their case being kept past the
    # 24-hour purge. Defaulting this to True would make the retention notice
    # decorative, so the endpoint refuses without it.
    accept_retention: bool = False


@app.get("/api/case/{session_id}/watcher")
async def watcher_status(session_id: str, db: Session = Depends(get_db)):
    """
    The tracker's whole state: clock, milestones, channels, retention.

    Assembled here rather than in the browser because the milestone
    arithmetic must have exactly one implementation. The frontend had a
    second one that counted from case creation instead of from delivery, and
    it was wrong in the dangerous direction — it would have told people to
    send a missed-deadline letter while the bureau was still inside its
    thirty days.
    """
    record = get_case(session_id, db)
    return {"ok": True, "tracking": watcher.status_payload(record)}


@app.post("/api/case/{session_id}/watcher/subscribe")
@limiter.limit("10/hour")
async def watcher_subscribe(
    request: Request,
    session_id: str,
    body: WatcherSubscribeRequest,
    db: Session = Depends(get_db),
):
    """
    Turn the Watcher on for this case.

    Order of checks matters and is deliberate: validate the channel *before*
    taking money, so nobody pays for reminders to an address we cannot
    deliver to. Snapchat, TikTok and Instagram are refused by name with the
    reason — see `watcher.CHANNELS`.
    """
    record = get_case(session_id, db)

    if not record.paid:
        raise HTTPException(402, "Complete your first round before turning on tracking.")

    ok, error = watcher.validate_handle(body.notify_method, body.notify_handle)
    if not ok:
        return {"ok": False, "error": error, "channels": watcher.available_channels()}

    if not body.accept_retention:
        return {
            "ok": False,
            "needs_retention_consent": True,
            "retention_notice": watcher.retention_notice(record),
            "error": "Please confirm you want your case kept for the tracking period.",
        }

    if record.watcher_subscribed:
        return {"ok": True, "already": True,
                "tracking": watcher.status_payload(record)}

    # Beta: tracking is included rather than sold separately. When a price is
    # configured, this is where checkout goes — and until then the page must
    # not display a price it does not charge.
    if config.WATCHER_PRICE_CENTS:
        raise HTTPException(
            501,
            "Paid tracking is not wired to checkout yet. Unset "
            "WATCHER_PRICE_CENTS to include it in the base price.",
        )

    record.watcher_subscribed = True
    record.watcher_subscribed_at = datetime.now(timezone.utc)
    record.watcher_notify_method = body.notify_method
    record.watcher_notify_handle = body.notify_handle.strip()
    record.watcher_retain_until = watcher.retention_until(record)
    db.commit()
    db.refresh(record)

    return {"ok": True, "subscribed": True,
            "tracking": watcher.status_payload(record)}


@app.post("/api/case/{session_id}/watcher/cancel")
async def watcher_cancel(session_id: str, db: Session = Depends(get_db)):
    """
    Turn tracking off — and give up the retention that came with it.

    Clearing `watcher_retain_until` puts the case back under the normal
    24-hour purge, so a cancelled case is collected on the next cleanup pass
    rather than lingering. That is the promise made when they subscribed.
    """
    record = get_case(session_id, db)
    record.watcher_subscribed = False
    record.watcher_retain_until = None
    record.watcher_notify_handle = None
    db.commit()
    return {"ok": True, "cancelled": True,
            "purge_note": "Your case returns to the normal schedule and is "
                          "destroyed within 24 hours of its creation time."}


@app.post("/api/case/{session_id}/watcher/followup/{day}")
async def watcher_followup(session_id: str, day: int, db: Session = Depends(get_db)):
    """
    Build the escalation round that has come due at this milestone.

    Refuses to build early. A method-of-verification demand sent on day 12
    tells the bureau the sender does not know the statute, and a file that
    reads as uninformed is a file that gets treated as frivolous. The refusal
    says how many days are left and why.
    """
    record = get_case(session_id, db)

    if not record.paid:
        raise HTTPException(402, "Payment required")
    if not record.watcher_subscribed:
        return {"ok": False, "error": "Turn on the Watcher to generate follow-up rounds."}

    allowed, reason, tier = watcher.can_generate(record, day)
    if not allowed:
        return {"ok": False, "error": reason, "day": day, "tier": tier}

    case = to_engine_case(record)
    prior = {"rounds_sent": sorted(record.watcher_rounds or [])}
    try:
        letters = gen_followup_letters(case, days_since_dispatch=day, prior_rounds=prior)
    except Exception:  # noqa: BLE001 - boundary must degrade, not crash; type logged
        traceback.print_exc()
        raise HTTPException(500, "Could not build the follow-up round.")

    # Record the tier so the same round is never silently rebuilt with
    # different content — a bureau that receives two different "day 30"
    # letters has been handed a reason to call the file frivolous.
    rounds = sorted(set(record.watcher_rounds or []) | {tier})
    record.watcher_rounds = rounds
    db.commit()

    return {
        "ok": True,
        "day": day,
        "tier": tier,
        "letters": letters,
        "next_step": "Print, sign in blue ink, and mail these certified. "
                     "Keep the receipt — from here the mailing record is "
                     "part of your evidence.",
    }


# ======================================================================
# Relief pathways — the routes that are not a dispute letter
# ======================================================================

@app.get("/api/case/{session_id}/relief")
async def case_relief(session_id: str, db: Session = Depends(get_db)):
    """
    Forgiveness, assistance and consolidation routes implied by the file.

    Deliberately **not** behind the paywall. This endpoint hands a consumer
    the addresses of free government and hospital programmes; charging for
    that, or hiding it until they pay, would be indefensible. The paywall is
    on the letters, which is the work this platform actually does.

    Returns `available: false` with empty sections when the report shows no
    student loans and no medical accounts — the frontend renders nothing at
    all in that case rather than an empty panel.
    """
    record = get_case(session_id, db)
    items = record.items or []

    profile = {
        "name": record.name or "",
        # Occupation sharpens which student-loan programmes surface first and
        # is read defensively — absent is the normal case.
        "occupation": getattr(record, "occupation", "") or "",
        "employer": getattr(record, "employer", "") or "",
    }

    try:
        return relief_pathways.find_relief(items, profile)
    except Exception as exc:  # never let this break the review screen  # noqa: BLE001 - boundary must degrade, not crash; type logged
        traceback.print_exc()
        return {
            "available": False,
            "sections": [],
            "error": "Could not check relief routes right now.",
            "detail": "" if config.IS_PROD else str(exc)[:200],
        }


@app.get("/api/case/{session_id}/relief/summary")
async def case_relief_summary(session_id: str, db: Session = Depends(get_db)):
    """Just enough for the review screen to decide whether to show the card."""
    record = get_case(session_id, db)
    try:
        return relief_pathways.entry_point(record.items or [])
    except Exception:  # noqa: BLE001 - boundary must degrade, not crash; type logged
        traceback.print_exc()
        return {"available": False, "label": "", "kinds": []}


# ======================================================================
# Admin endpoints
# ======================================================================

def verify_admin(request: Request):
    """Check X-Admin-Key header against ADMIN_KEY. Fails closed if unset."""
    if not config.ADMIN_KEY:
        raise HTTPException(503, "Admin access is not configured")
    key = request.headers.get("X-Admin-Key", "")
    if not hmac.compare_digest(key, config.ADMIN_KEY):
        raise HTTPException(401, "Invalid admin key")


@app.get("/api/admin/buckets")
async def admin_buckets(request: Request):
    verify_admin(request)
    return all_categories()


@app.get("/api/admin/templates")
async def admin_templates(request: Request):
    """
    What the engine can currently argue — categories, theories and the tier
    ladder. Deliberately does NOT return letter bodies: the composed argument
    is the product, and dumping it behind one shared key is how it walks.
    """
    verify_admin(request)
    return engine_manifest()


@app.get("/api/admin/stats")
async def admin_stats(request: Request, db: Session = Depends(get_db)):
    verify_admin(request)
    total = db.query(CaseRecord).count()
    paid = db.query(CaseRecord).filter_by(paid=True).count()
    today_count = db.query(CaseRecord).filter(
        CaseRecord.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    ).count()
    pending_manual = db.query(CaseRecord).filter(
        CaseRecord.manual_pay_requested_at.isnot(None), CaseRecord.paid.is_(False)
    ).count()
    return {
        "total_cases": total,
        "paid_cases": paid,
        "revenue_estimate": f"${paid * config.STRIPE_PRICE_CENTS / 100:.2f}",
        "today": today_count,
        "pending_manual": pending_manual,
        "fishbowl": get_fishbowl_status(db),
    }


@app.get("/api/admin/pending-payments")
async def admin_pending_payments(request: Request, db: Session = Depends(get_db)):
    """Cases waiting on a Cash App / Chime payment to be verified + released."""
    verify_admin(request)
    records = (
        db.query(CaseRecord)
        .filter(CaseRecord.manual_pay_requested_at.isnot(None), CaseRecord.paid.is_(False))
        .order_by(CaseRecord.manual_pay_requested_at.desc())
        .all()
    )
    return {
        "pending": [
            {
                "session_id": r.session_id,
                "name": r.name,
                "email": r.email,
                "method": r.manual_pay_method,
                # Who is sending the money, in their words. Matching this
                # against the Cash App feed is faster than hunting for the
                # confirmation code in a payment memo.
                "payer_handle": r.manual_pay_handle or "",
                "confirmation": r.manual_pay_code,
                "requested_at": r.manual_pay_requested_at.isoformat() if r.manual_pay_requested_at else None,
                "amount": config.PRICE_DISPLAY,
                "letters_count": len(r.letters or []),
            }
            for r in records
        ]
    }


@app.post("/api/admin/print-token/{session_id}")
async def admin_print_token(session_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Mint a 10-minute token for the print view.

    The print packet has to open in a normal browser tab so it can be sent
    to a printer, and a URL is the only way to do that — but the admin key
    must never ride in a query string where it lands in history and logs.
    A short-lived, single-case token does the job without that exposure.
    """
    verify_admin(request)
    get_case(session_id, db)
    return {
        "token": print_packet.issue_print_token(session_id),
        "expires_in": print_packet.TOKEN_TTL_SECONDS,
        "url": f"/api/admin/print/{session_id}?t={print_packet.issue_print_token(session_id)}",
    }


@app.get("/api/admin/print/{session_id}")
async def admin_print(session_id: str, t: str = "", db: Session = Depends(get_db)):
    """Printable packet: checklist, window covers, letters, stickers, labels."""
    if not print_packet.verify_print_token(session_id, t):
        raise HTTPException(401, "Invalid or expired print link. Reopen it from /admin.")

    record = get_case(session_id, db)
    letters = record.letters or []
    if not letters:
        raise HTTPException(404, "No letters generated for this case yet")

    tier = max((ltr.get("tier", 1) for ltr in letters), default=1)
    tier_name = next((ltr.get("tier_name", "") for ltr in letters if ltr.get("tier_name")), "")

    provenance.record(session_id, "print_packet_opened", {"letters": len(letters), "tier": tier})

    html_doc = print_packet.build_print_packet(
        name=record.name,
        client_address=record.address,
        letters=letters,
        confirmation=record.manual_pay_code or "",
        tier=tier,
        tier_name=tier_name,
    )
    return Response(content=html_doc, media_type="text/html")


@app.post("/api/admin/release/{session_id}")
async def admin_release_payment(session_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Mark a case paid after manually verifying the Cash App / Chime payment
    landed. Triggers the same post-payment actions as the Stripe webhook
    (mail letters round 1, email the PDF packet).
    """
    verify_admin(request)
    record = get_case(session_id, db)
    if record.paid:
        return {"ok": True, "already_paid": True, "session_id": session_id}
    record.paid = True
    record.manual_pay_released_at = datetime.now(timezone.utc)
    db.commit()

    provenance.record(session_id, "payment_released",
                      {"method": record.manual_pay_method,
                       "handle": record.manual_pay_handle or "",
                       "code": record.manual_pay_code or ""})

    _post_payment(record, db)
    return {"ok": True, "released": True, "session_id": session_id}
