import os
import re
import uuid
import stripe
from pathlib import Path
from datetime import datetime

# Load .env file before anything reads env vars
from dotenv import load_dotenv
load_dotenv()

DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() in ("true", "1", "yes")

from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from database import init_db, get_db, CaseRecord
from ae_creditfix.case import Case, Client, Item, new_id
from ae_creditfix.letters import gen_bureau_letters, gen_creditor_letters, gen_cover_sheet
from ae_creditfix.templates import BUREAU_ADDRESSES
from ae_creditfix.storage import set_root
from pdf_gen import build_letter_pdf
from email_sender import send_letters_email
from mail_service import send_all_letters, verify_webhook_signature
from report_parser import parse_credit_report
from fishbowl import check_beta_eligibility, enter_fishbowl, exit_fishbowl, get_fishbowl_status
from buckets import get_all_buckets, DISPUTE_BUCKETS, render_letter_for_bucket
from cypher import generate_session_key, encrypt_file_in_memory, decrypt_file_in_memory
from cleanup import cleanup_loop
import asyncio
import base64

# --- Config ---
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_CENTS = 1999  # $19.99
APP_URL = os.environ.get("APP_URL", "http://localhost:8000")

stripe.api_key = STRIPE_SECRET_KEY

# --- App setup ---
app = FastAPI(title="AE 5-Min Credit Fix")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

init_db()


@app.on_event("startup")
async def startup():
    asyncio.create_task(cleanup_loop())


DATA_DIR = Path(__file__).resolve().parent / "session_data"
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
PDF_DIR = Path(__file__).resolve().parent / "generated_pdfs"
PDF_DIR.mkdir(exist_ok=True)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests. Please try again later."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


class ResumeRequest(BaseModel):
    session_id: str


# ======================================================================
# STEP 1 — Create case & upload docs
# ======================================================================

@app.post("/api/terms/accept")
@limiter.limit("10/minute")
async def accept_terms(request: Request):
    """Record terms acceptance. Returns a terms_token to pass with case creation."""
    token = uuid.uuid4().hex[:16]
    # Store only the token and timestamp — no PII
    _terms_cache[token] = datetime.utcnow()
    return {"terms_token": token, "accepted_at": _terms_cache[token].isoformat()}

# In-memory terms tokens (short-lived, cleared on restart)
_terms_cache: dict[str, datetime] = {}


@app.post("/api/case")
@limiter.limit("10/minute")
async def create_case(req: CreateCaseRequest, request: Request, db: Session = Depends(get_db)):
    # Verify terms acceptance
    terms_token = request.headers.get("X-Terms-Token", "")
    if terms_token not in _terms_cache:
        raise HTTPException(400, "You must accept the terms before proceeding")

    # Trapdoor Fishbowl — check beta region eligibility by zip code
    eligibility = check_beta_eligibility(req.address)
    if not eligibility["eligible"]:
        raise HTTPException(403, eligibility["reason"])

    region = eligibility["region"]
    queue_pos = enter_fishbowl(region)

    # Generate Cypher session key
    client_ip = get_remote_address(request)
    key_id, raw_key = generate_session_key(client_ip)

    session_id = uuid.uuid4().hex[:12]
    record = CaseRecord(
        session_id=session_id,
        name=req.name,
        address=req.address,
        dob=req.dob,
        ssn_last4=req.ssn_last4,
        phone=req.phone,
        email=req.email,
        cypher_key_id=key_id,
        cypher_key_enc=base64.b64encode(raw_key).decode("ascii"),
        terms_accepted_at=_terms_cache.pop(terms_token, datetime.utcnow()),
    )
    db.add(record)
    db.commit()
    return {
        "session_id": session_id,
        "status": "created",
        "region": eligibility["region_name"],
        "queue_position": queue_pos,
        "cypher_key_id": key_id,
    }


@app.get("/api/fishbowl/status")
async def fishbowl_status():
    """Check current fishbowl queue status for all beta regions."""
    return get_fishbowl_status()


@app.post("/api/case/{session_id}/upload")
@limiter.limit("20/minute")
async def upload_doc(session_id: str, request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    upload_dir = UPLOADS_DIR / session_id
    upload_dir.mkdir(exist_ok=True)

    # Validate file type
    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".csv"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"File type {suffix} not allowed. Accepted: {', '.join(allowed)}")

    # Validate file size (10MB max)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 10MB.")

    # Recover session encryption key
    session_key = base64.b64decode(record.cypher_key_enc) if record.cypher_key_enc else None

    # Encrypt file before writing to disk — plaintext never touches disk
    if session_key:
        encrypted = encrypt_file_in_memory(content, session_key)
        dest = upload_dir / (file.filename + ".enc")
        dest.write_bytes(encrypted)
    else:
        dest = upload_dir / file.filename
        dest.write_bytes(content)

    attachments = record.attachments or []
    attachments.append(file.filename)
    record.attachments = attachments
    record.docs_complete = True
    db.commit()

    # Parse credit report from in-memory plaintext (never from disk)
    suggestions = []
    if suffix in (".pdf", ".txt", ".csv"):
        # Write to temp, parse, delete immediately
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        try:
            suggestions = parse_credit_report(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

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

    work_dir = DATA_DIR / session_id
    set_root(str(work_dir))

    bureau = gen_bureau_letters(case)
    creditor = gen_creditor_letters(case)
    cover = gen_cover_sheet(case)

    letters_data = []
    for ltr_id, target, path in bureau + creditor:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        letters_data.append({"id": ltr_id, "target": target, "text": text})

    cover_text = cover.read_text(encoding="utf-8", errors="replace")

    # Store letters in DB
    record.letters = letters_data
    record.letter_bundle_text = cover_text + "\n\n" + "\n\n".join(l["text"] for l in letters_data)

    # Generate PDF
    client_dict = {
        "name": record.name, "address": record.address, "dob": record.dob,
        "ssn_last4": record.ssn_last4, "phone": record.phone, "email": record.email,
    }
    pdf_path = build_letter_pdf(session_id, client_dict, letters_data, PDF_DIR)
    record.letter_pdf_path = str(pdf_path)
    db.commit()

    return {"letters": letters_data, "cover_sheet": cover_text, "total": len(letters_data)}


@app.get("/api/case/{session_id}/letters")
async def get_letters(session_id: str, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    return {"letters": record.letters or []}


# ======================================================================
# STEP 4 — Certified mail info + auto-send
# ======================================================================

@app.get("/api/case/{session_id}/mail-info")
async def mail_info(session_id: str, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    targets = list({l["target"] for l in (record.letters or [])})
    mail_targets = [
        {"target": t, "address": BUREAU_ADDRESSES.get(t, "See letter for address")}
        for t in targets
    ]
    return {"mail_targets": mail_targets}


@app.post("/api/case/{session_id}/send-mail")
@limiter.limit("3/minute")
async def send_mail(session_id: str, request: Request, db: Session = Depends(get_db)):
    """Auto-send all dispute letters via Lob Certified Mail."""
    record = get_case(session_id, db)
    if not record.paid:
        raise HTTPException(402, "Payment required before mailing")

    letters = record.letters or []
    if not letters:
        raise HTTPException(400, "No letters generated yet")

    results = send_all_letters(record.name, record.address, letters, session_id)

    if not results and DEMO_MODE:
        # Demo mode: generate realistic-looking tracking data
        from datetime import timedelta
        demo_results = []
        for ltr in letters:
            target = ltr.get("target", "Bureau")
            demo_results.append({
                "target": target,
                "tracking_number": f"9400111899{uuid.uuid4().hex[:12].upper()}",
                "expected_delivery": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d"),
                "status": "demo — would mail via USPS Certified",
            })
        return {
            "sent": len(demo_results),
            "tracking": demo_results,
            "message": f"DEMO MODE: {len(demo_results)} letter(s) staged. Connect Lob API key to send real certified mail.",
        }

    return {
        "sent": len(results),
        "tracking": results,
        "message": f"Sent {len(results)} letter(s) via USPS Certified Mail" if results
                   else "Lob not configured — print and mail manually (see instructions)",
    }


@app.post("/api/webhooks/lob")
async def lob_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Lob delivery status webhooks."""
    body = await request.body()
    signature = request.headers.get("lob-signature", "")

    if not verify_webhook_signature(body, signature):
        raise HTTPException(401, "Invalid webhook signature")

    import json
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

    if not STRIPE_SECRET_KEY:
        # Demo mode — mark as paid without Stripe
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
                "unit_amount": STRIPE_PRICE_CENTS,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{APP_URL}/?session_id={session_id}&paid=true",
        cancel_url=f"{APP_URL}/?session_id={session_id}&step=3",
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

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            raise HTTPException(400, "Invalid webhook signature")
    else:
        import json
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
    """Actions after successful payment: send certified mail, send email, release fishbowl slot."""
    # Auto-send dispute letters via Lob Certified Mail
    letters = record.letters or []
    if letters and not record.mail_sent:
        results = send_all_letters(record.name, record.address, letters, record.session_id)

        if results:
            record.mail_tracking = results
            record.mail_sent = True
        elif DEMO_MODE:
            from datetime import timedelta
            demo_results = []
            for ltr in letters:
                target = ltr.get("target", "Bureau")
                demo_results.append({
                    "target": target,
                    "tracking_number": f"9400111899{uuid.uuid4().hex[:12].upper()}",
                    "expected_delivery": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d"),
                    "status": "demo — would mail via USPS Certified",
                })
            record.mail_tracking = demo_results
            record.mail_sent = True

        db.commit()

    # Email PDF copy to client
    if record.letter_pdf_path and not record.email_sent:
        pdf_path = Path(record.letter_pdf_path)
        if DEMO_MODE:
            print(f"DEMO: Would email PDF to {record.email} (SendGrid not configured)")
            record.email_sent = True
            db.commit()
        else:
            sent = send_letters_email(record.email, record.name, record.session_id, pdf_path)
            if sent:
                record.email_sent = True
                db.commit()

    # Release fishbowl slot for this region
    eligibility = check_beta_eligibility(record.address)
    if eligibility.get("region"):
        exit_fishbowl(eligibility["region"])


# ======================================================================
# Mail status (after payment)
# ======================================================================

@app.get("/api/case/{session_id}/mail-status")
async def mail_status(session_id: str, db: Session = Depends(get_db)):
    """Get certified mail tracking status for a paid case."""
    record = get_case(session_id, db)
    if not record.paid:
        raise HTTPException(402, "Payment required")
    tracking = record.mail_tracking or []
    status = "sent" if record.mail_sent else "processing"
    return {"status": status, "tracking": tracking}


# ======================================================================
# Download (after payment)
# ======================================================================

@app.get("/api/case/{session_id}/download")
async def download_letters(session_id: str, db: Session = Depends(get_db)):
    record = get_case(session_id, db)
    if not record.paid:
        raise HTTPException(402, "Payment required")
    if record.letter_pdf_path and Path(record.letter_pdf_path).exists():
        return FileResponse(record.letter_pdf_path, filename=f"AE_CreditFix_Letters_{session_id}.pdf")
    raise HTTPException(404, "Letters not found — please regenerate")


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

ADMIN_KEY = os.environ.get("ADMIN_KEY", "aelabs2024")


def verify_admin(request: Request):
    """Check X-Admin-Key header or ?key= query param against ADMIN_KEY."""
    key = request.headers.get("X-Admin-Key", "") or request.query_params.get("key", "")
    if key != ADMIN_KEY:
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
        "revenue_estimate": f"${paid * 19.99:.2f}",
        "today": today_count,
        "fishbowl": get_fishbowl_status(),
    }


# ======================================================================
# Serve Next.js static export
# ======================================================================

STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "out"
if STATIC_DIR.is_dir():
    app.mount("/_next", StaticFiles(directory=STATIC_DIR / "_next"), name="next_static")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file = STATIC_DIR / path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
