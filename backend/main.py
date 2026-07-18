import asyncio
import base64
import hmac
import json
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import stripe
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

import config
from ae_creditfix.case import Case, Client, Item, new_id
from ae_creditfix.letters import gen_bureau_letters, gen_cover_sheet, gen_creditor_letters
from ae_creditfix.templates import BUREAU_ADDRESSES
from buckets import DISPUTE_BUCKETS, get_all_buckets
from cleanup import cleanup_loop
from cypher import encrypt_file_in_memory, generate_session_key
from database import CaseRecord, get_db, init_db
from email_sender import send_letters_email
from fishbowl import check_beta_eligibility, get_fishbowl_status
from mail_service import send_all_letters, verify_webhook_signature
from pdf_gen import build_letter_pdf
from report_parser import parse_credit_report_bytes
from terms_token import issue_token, verify_token

stripe.api_key = config.STRIPE_SECRET_KEY


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()


app = FastAPI(title="AE 5-Min Credit Fix", lifespan=lifespan)
limiter = Limiter(key_func=get_remote_address, storage_uri=config.RATE_LIMIT_STORAGE_URI)
app.state.limiter = limiter

init_db()

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


def to_engine_case(record: CaseRecord) -> Case:
    """Convert DB record to ae_creditfix Case for letter generation."""
    client = Client(
        name=record.name,
        address=record.address,
        dob=record.dob,
        ssn_last4=record.ssn_last4,
        phone=record.phone,
        email=record.email,
    )
    items = [Item(**item) for item in (record.items or [])]
    case = Case(client=client, items=items, attachments=record.attachments or [])
    case.phases["p1_docs_complete"] = record.docs_complete
    return case


def build_case_pdf(record: CaseRecord) -> bytes:
    """Regenerate the letter-packet PDF in memory (never stored on disk)."""
    client_dict = {
        "name": record.name, "address": record.address, "dob": record.dob,
        "ssn_last4": record.ssn_last4, "phone": record.phone, "email": record.email,
    }
    return build_letter_pdf(record.session_id, client_dict, record.letters or [])


def _demo_tracking(letters: list) -> list:
    """Realistic-looking tracking data for demo mode."""
    results = []
    for ltr in letters:
        results.append({
            "target": ltr.get("target", "Bureau"),
            "tracking_number": f"9400111899{uuid.uuid4().hex[:12].upper()}",
            "expected_delivery": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "status": "demo — would mail via USPS",
        })
    return results


# --- Validation models ---

class CreateCaseRequest(BaseModel):
    name: str
    address: str
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
            dt = datetime.strptime(v, "%Y-%m-%d")
            if dt.year < 1920 or dt > datetime.now():
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
            raise ValueError("Valid mailing address is required")
        return v.strip()


class DisputeItem(BaseModel):
    type: str
    target: str
    account: str
    amount: Optional[float] = None
    opened: Optional[str] = None
    reason: str

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
    items: List[DisputeItem]


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
    eligibility = check_beta_eligibility(req.address, db)
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
async def upload_doc(session_id: str, request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    record = get_case(session_id, db)

    # Validate file type
    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".csv"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"File type {suffix} not allowed. Accepted: {', '.join(sorted(allowed))}")

    # Validate file size (10MB max)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 10MB.")

    # Encrypt with the per-session key before writing — plaintext never
    # touches disk. Stored name is opaque (no user-controlled path parts).
    session_key = base64.b64decode(record.cypher_key_enc)
    upload_dir = UPLOADS_DIR / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    encrypted = encrypt_file_in_memory(content, session_key)
    (upload_dir / f"{uuid.uuid4().hex[:8]}{suffix}.enc").write_bytes(encrypted)

    attachments = record.attachments or []
    attachments.append(file.filename)
    record.attachments = attachments
    record.docs_complete = True
    db.commit()

    # Parse the credit report fully in memory
    suggestions = []
    if suffix in (".pdf", ".txt", ".csv"):
        suggestions = parse_credit_report_bytes(content, suffix)

    return {
        "filename": file.filename,
        "attachments": attachments,
        "suggestions": suggestions,
    }


# ======================================================================
# STEP 2 — Confirm disputes
# ======================================================================

@app.post("/api/case/{session_id}/disputes")
@limiter.limit("10/minute")
async def confirm_disputes(session_id: str, req: ConfirmDisputesRequest, request: Request, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    items = record.items or []
    for item in req.items:
        items.append({
            "id": new_id("ITM"),
            "type": item.type,
            "target": item.target,
            "account": item.account,
            "amount": item.amount,
            "opened": item.opened,
            "reason": item.reason,
            "status": "open",
            "letters": [],
        })
    record.items = items
    db.commit()
    return {"items_count": len(items)}


# ======================================================================
# STEP 3 — Generate & review letters
# ======================================================================

@app.post("/api/case/{session_id}/letters")
@limiter.limit("5/minute")
async def generate_letters(session_id: str, request: Request, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    case = to_engine_case(record)

    bureau = gen_bureau_letters(case)
    creditor = gen_creditor_letters(case)
    cover_text = gen_cover_sheet(case)

    letters_data = [
        {"id": ltr_id, "target": target, "text": text}
        for ltr_id, target, text in bureau + creditor
    ]

    # Letters live only in the encrypted column; the PDF is built on demand
    record.letters = letters_data
    db.commit()

    return {"letters": letters_data, "cover_sheet": cover_text, "total": len(letters_data)}


@app.get("/api/case/{session_id}/letters")
async def get_letters(session_id: str, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    return {"letters": record.letters or []}


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

    results = send_all_letters(record.name, record.address, letters, session_id, round_number=1)

    if not results and config.DEMO_MODE:
        demo_results = _demo_tracking(letters)
        return {
            "sent": len(demo_results),
            "tracking": demo_results,
            "message": f"DEMO MODE: {len(demo_results)} letter(s) staged. Connect Lob API key to send real mail.",
        }

    return {
        "sent": len(results),
        "tracking": results,
        "message": f"Sent {len(results)} letter(s) via USPS" if results
                   else "Lob not configured — print and mail manually (see instructions)",
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
            letters = record.letters or []
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
        if config.IS_PROD:
            raise HTTPException(503, "Payments are not configured")
        # Dev/demo mode — mark as paid without Stripe
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
        success_url=f"{config.FRONTEND_URL}/?session_id={session_id}&paid=true",
        cancel_url=f"{config.FRONTEND_URL}/?session_id={session_id}&step=4",
        metadata={"session_id": session_id},
        customer_email=record.email,
    )
    record.stripe_session_id = checkout.id
    db.commit()
    return {"checkout_url": checkout.url}


@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook for payment confirmation."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if config.STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, config.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            raise HTTPException(400, "Invalid webhook signature")
    elif config.IS_PROD:
        # Never accept unsigned payment events in production
        raise HTTPException(503, "Stripe webhook secret not configured")
    else:
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
        results = send_all_letters(record.name, record.address, letters, record.session_id, round_number=1)

        if results:
            record.mail_tracking = results
            record.mail_sent = True
        elif config.DEMO_MODE:
            record.mail_tracking = _demo_tracking(letters)
            record.mail_sent = True

        db.commit()

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
    }


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
    return get_all_buckets()


@app.get("/api/admin/templates")
async def admin_templates(request: Request):
    verify_admin(request)
    return [
        {"bucket": k, "label": v["label"], "body": v["letter_body"]}
        for k, v in DISPUTE_BUCKETS.items()
    ]


@app.get("/api/admin/stats")
async def admin_stats(request: Request, db: Session = Depends(get_db)):
    verify_admin(request)
    total = db.query(CaseRecord).count()
    paid = db.query(CaseRecord).filter_by(paid=True).count()
    today_count = db.query(CaseRecord).filter(
        CaseRecord.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).count()
    return {
        "total_cases": total,
        "paid_cases": paid,
        "revenue_estimate": f"${paid * config.STRIPE_PRICE_CENTS / 100:.2f}",
        "today": today_count,
        "fishbowl": get_fishbowl_status(db),
    }
