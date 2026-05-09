# 5 Minutes to Credit Wellness — FastAPI Application
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# Migrated from Flask. All routes preserved. Bug fixes applied.

import os
import uuid
import json
import hashlib
import tempfile
from datetime import datetime, timedelta

import stripe
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

from api.database import (
    init_db, get_db_dependency, save_client, load_client,
    load_client_by_confirmation, get_all_clients_admin, get_stats,
    delete_expired_clients, mark_followup_sent, Client, utcnow,
)
from api.encryption import encrypt, decrypt, decrypt_json
from api.auth import ensure_admin_exists, authenticate, get_current_admin
from api.ledger import init_chain, write_block, verify_chain, get_chain, get_recent_log
from api.parser import parse_uploaded_files, extract_structured_accounts
from api.classifier import classify_dispute_items, sort_by_gilmore_order, group_items_by_box, DISPUTE_BOX_LABELS
from api.letters import generate_letters, BUREAU_ADDRESSES
from api.followup import generate_followup_letters
from api.pdf_generator import letters_to_zip
from api.agents import (
    enroll_client as enroll_watcher, run_all_agents, enroll_from_db, get_pipeline_stats,
)


# ═══ CONFIG ═══════════════════════════════════════════════════════════════════

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUB_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PRICE_CENTS = 2499
WATCHER_PRICE_CENTS = 1099
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

UPLOAD_FOLDER = tempfile.mkdtemp(prefix="aecf_")
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "txt", "csv", "docx", "html", "htm"}

# In-memory session store (maps session_id -> encrypted profile bytes)
# Persisted to DB on every save — this is the hot cache only.
sessions: dict[str, bytes] = {}


# ═══ APP ══════════════════════════════════════════════════════════════════════

app = FastAPI(title="5 Minutes to Credit Wellness", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:3001",
        FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    with next(get_db_dependency()) as db:
        init_chain(db)
    ensure_admin_exists()
    print("[STARTUP] 5 Minutes to Credit Wellness — FastAPI ready")


# ═══ HELPERS ══════════════════════════════════════════════════════════════════

def _get_session_id(request: Request) -> str | None:
    return request.cookies.get("session_id")


def _set_session_cookie(response: Response, session_id: str):
    response.set_cookie("session_id", session_id, httponly=True, samesite="lax", max_age=7200)


def _store(sid: str, data: dict, db: Session):
    """Encrypt profile into memory cache and persist to DB."""
    from api.encryption import session_encrypt
    sessions[sid] = session_encrypt(data, sid)
    save_client(db, data, encrypt)


def _load(sid: str, db: Session) -> dict | None:
    """Load profile from memory cache, fall back to DB."""
    from api.encryption import session_decrypt
    if sid in sessions:
        result = session_decrypt(sessions[sid], sid)
        if result:
            return result
    return load_client(db, sid, decrypt_json)


def _gen_confirmation() -> str:
    """Generate a clean confirmation code — no tool identifiers."""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    rand_part = uuid.uuid4().hex[:6].upper()
    return f"{date_part}-{rand_part}"


def _create_client_profile(sid, name, email, phone, state, referral_source="", address=""):
    now = utcnow().isoformat()
    return {
        "id": sid, "name": name, "email": email, "phone": phone,
        "address": address, "state": state, "referral_source": referral_source,
        "created_at": now, "updated_at": now, "status": "started",
        "confirmation": None, "paid": False, "paid_at": None, "payment_method": None,
        "files": [], "parsed_disputes": {}, "dispute_items": [],
        "dispute_types": [], "dispute_order": [], "letters": [],
        "status_per_item": {},
        "follow_up_dates": {"day_30": None, "day_60": None, "day_90": None},
        "follow_up_history": [], "follow_up_letters": {},
        "mov_letters_sent": [], "dispatched_at": None,
        "watcher_subscribed": False, "watcher_paid_at": None,
        "notify_method": "", "notify_handle": "", "notifications_sent": [],
    }


# ═══ PYDANTIC MODELS ═════════════════════════════════════════════════════════

class StartRequest(BaseModel):
    name: str
    email: str
    phone: str = ""
    address: str = ""
    state: str = ""
    referral_source: str = ""

class ReviewRequest(BaseModel):
    items: list[dict] = []
    custom_items: list[dict] = []

class ManualPayRequest(BaseModel):
    method: str = "cashapp"

class WatcherSubscribeRequest(BaseModel):
    notify_method: str = "email"
    notify_handle: str = ""
    payment_method: str = "card"

class AdminLoginRequest(BaseModel):
    username: str = "admin"
    password: str


# ═══ ROUTES ═══════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "ok", "service": "5 Minutes to Credit Wellness", "version": "2.0.0"}


# ─── Step 1: Start ───────────────────────────────────────────────────────────

@app.post("/api/start")
def api_start(body: StartRequest, request: Request, response: Response, db: Session = Depends(get_db_dependency)):
    name = body.name.strip()
    email = body.email.strip()
    if not name or not email:
        raise HTTPException(400, "Name and email are required")
    state = body.state.strip().upper()
    sid = str(uuid.uuid4())
    confirmation = _gen_confirmation()
    sub = _create_client_profile(sid, name, email, body.phone.strip(), state, body.referral_source.strip().lower(), body.address.strip())
    sub["confirmation"] = confirmation
    _store(sid, sub, db)
    _set_session_cookie(response, sid)
    return {"ok": True, "session_id": sid, "name": name, "confirmation": confirmation}


# ─── Step 2: Upload & Parse ──────────────────────────────────────────────────

@app.post("/api/upload")
async def api_upload(request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found. Please start over.")
    form = await request.form()
    filepaths = []
    files_info = []
    for key in form:
        f = form[key]
        if hasattr(f, "filename") and f.filename:
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext not in ALLOWED_EXTENSIONS:
                continue
            fn = secure_filename(f"{sid}_{f.filename}")
            fp = os.path.join(UPLOAD_FOLDER, fn)
            contents = await f.read()
            with open(fp, "wb") as out:
                out.write(contents)
            files_info.append({"name": f.filename, "saved_as": fn})
            filepaths.append((fp, f.filename))
    if not filepaths:
        raise HTTPException(400, "No valid files uploaded")
    parsed, raw_text = parse_uploaded_files(filepaths)
    for fp, _ in filepaths:
        try:
            os.remove(fp)
        except OSError:
            pass
    sub["files"] = files_info
    sub["parsed_disputes"] = parsed
    sub["status"] = "parsed"
    all_items = []
    for dtype, info in parsed.items():
        for item in info["items"]:
            all_items.append({"type": dtype, "label": info["label"], "text": item})
    structured = extract_structured_accounts(raw_text)
    classified = classify_dispute_items(structured, sub.get("state", ""))
    sub["dispute_items"] = classified if classified else all_items
    boxes = group_items_by_box(classified) if classified else {}
    if boxes:
        sub["parsed_disputes"] = boxes
    _store(sid, sub, db)
    return {"ok": True, "files_received": len(files_info), "parsed_disputes": sub["parsed_disputes"], "dispute_items": sub["dispute_items"]}


# ─── Step 2.5: Get Disputes ──────────────────────────────────────────────────

@app.get("/api/disputes")
def api_disputes(request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    return {"ok": True, "dispute_items": sub.get("dispute_items", []), "parsed_disputes": sub.get("parsed_disputes", {})}


# ─── Step 3: Review & Generate Letters ────────────────────────────────────────

@app.post("/api/review")
def api_review(body: ReviewRequest, request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    all_items = body.items + body.custom_items
    sub["dispute_items"] = all_items
    types_set = set()
    for item in all_items:
        types_set.add(item.get("type", "unknown_accounts") if isinstance(item, dict) else "unknown_accounts")
    sub["dispute_types"] = sort_by_gilmore_order(list(types_set))
    sub["dispute_order"] = sub["dispute_types"][:]
    sub["status"] = "reviewed"
    sub["updated_at"] = utcnow().isoformat()
    confirmation = _gen_confirmation()
    sub["confirmation"] = confirmation
    items_by_type = {}
    for item in all_items:
        if isinstance(item, dict):
            items_by_type.setdefault(item.get("type", "unknown_accounts"), []).append(item.get("text", ""))
        else:
            items_by_type.setdefault("unknown_accounts", []).append(str(item))
    sub["letters"] = generate_letters(sub["dispute_types"], items_by_type, {"name": sub["name"], "confirmation": confirmation, "state": sub.get("state", "")})
    _store(sid, sub, db)
    return {"ok": True, "confirmation": confirmation, "dispute_types": sub["dispute_types"], "letter_count": len(sub["letters"]), "items": all_items}


# ─── Step 4: Payment ─────────────────────────────────────────────────────────

@app.post("/api/create-checkout")
def api_create_checkout(request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    if not stripe.api_key:
        sub["paid"] = True
        sub["status"] = "paid"
        sub["paid_at"] = utcnow().isoformat()
        _store(sid, sub, db)
        return {"ok": True, "dev_mode": True, "message": "Payment skipped (dev mode)"}
    base_url = str(request.base_url).rstrip("/")
    cs = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price_data": {"currency": "usd", "product_data": {"name": "5 Minutes to Credit Wellness — Dispute Letter Package"}, "unit_amount": PRICE_CENTS}, "quantity": 1}],
        mode="payment",
        success_url=f"{base_url}/api/payment-success?sid={sid}&ss={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/stairway",
        metadata={"submission_id": sid},
    )
    return {"ok": True, "checkout_url": cs.url, "session_id": cs.id}


@app.post("/api/manual-pay")
def api_manual_pay(body: ManualPayRequest, request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    sub["payment_method"] = body.method
    sub["status"] = "pending_payment"
    sub["updated_at"] = utcnow().isoformat()
    if not sub.get("confirmation"):
        sub["confirmation"] = _gen_confirmation()
    _store(sid, sub, db)
    return {"ok": True, "pending": True, "confirmation": sub["confirmation"]}


@app.get("/api/payment-success")
def api_payment_success(sid: str = "", response: Response = None, db: Session = Depends(get_db_dependency)):
    if sid:
        sub = _load(sid, db)
        if sub:
            now = utcnow()
            sub["paid"] = True
            sub["status"] = "paid"
            sub["paid_at"] = now.isoformat()
            sub["follow_up_dates"] = {
                "day_30": (now + timedelta(days=30)).isoformat(),
                "day_60": (now + timedelta(days=60)).isoformat(),
                "day_90": (now + timedelta(days=90)).isoformat(),
            }
            _store(sid, sub, db)
    return RedirectResponse(f"{FRONTEND_URL}/gate", status_code=302)


# ─── Step 5: Letters ──────────────────────────────────────────────────────────

@app.get("/api/letters")
def api_letters(request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    if not sub.get("paid"):
        raise HTTPException(403, "Payment required")
    return {"ok": True, "confirmation": sub.get("confirmation"), "name": sub.get("name"), "letters": sub.get("letters", []), "dispute_types": sub.get("dispute_types", [])}


@app.get("/api/letters/{index}")
def api_letter_by_id(index: int, request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    letters = sub.get("letters", [])
    if index < 0 or index >= len(letters):
        raise HTTPException(404, "Letter not found")
    letter = letters[index]
    bureau_addr = BUREAU_ADDRESSES.get(letter.get("bureau", ""), {})
    return {"ok": True, "letter": {**letter, "index": index, "bureau_full_address": bureau_addr, "client_name": sub.get("name", ""), "client_address": sub.get("address", ""), "confirmation": sub.get("confirmation", "")}}


# ─── Download ZIP of PDFs ────────────────────────────────────────────────────

@app.get("/api/download-letters")
def api_download_letters(request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    if not sub.get("paid"):
        raise HTTPException(403, "Payment required")
    letters = sub.get("letters", [])
    if not letters:
        raise HTTPException(400, "No letters generated")
    zip_bytes = letters_to_zip(letters, sub.get("name", ""), sub.get("address", ""))
    conf = sub.get("confirmation", "letters")
    import io
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{conf}_dispute_letters.zip"'},
    )


# ─── Mark Mailed (user self-reports) ─────────────────────────────────────────

@app.post("/api/mark-mailed")
def api_mark_mailed(request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    now = utcnow()
    sub["dispatched_at"] = now.isoformat()
    sub["status"] = "dispatched"
    sub["follow_up_dates"] = {
        "day_30": (now + timedelta(days=30)).isoformat(),
        "day_60": (now + timedelta(days=60)).isoformat(),
        "day_90": (now + timedelta(days=90)).isoformat(),
    }
    _store(sid, sub, db)
    return {"ok": True, "dispatched_at": sub["dispatched_at"]}


# ─── Follow-up letters ───────────────────────────────────────────────────────

@app.get("/api/followup-letters/{day}")
def api_followup_letters(day: int, request: Request, db: Session = Depends(get_db_dependency)):
    if day not in (30, 60, 90):
        raise HTTPException(400, "Invalid day")
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    if not sub.get("paid"):
        raise HTTPException(403, "Payment required")
    letters = generate_followup_letters(sub, day)
    return {"ok": True, "letters": letters, "day": day}


# ─── Watcher ──────────────────────────────────────────────────────────────────

@app.post("/api/watcher/subscribe")
def api_watcher_subscribe(body: WatcherSubscribeRequest, request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    if not sub.get("paid"):
        raise HTTPException(403, "Must complete main payment first")
    if sub.get("watcher_subscribed"):
        return {"ok": True, "already": True}
    # Dev mode — activate immediately
    sub["watcher_subscribed"] = True
    sub["watcher_paid_at"] = utcnow().isoformat()
    sub["notify_method"] = body.notify_method
    sub["notify_handle"] = body.notify_handle or sub.get("email", "")
    _store(sid, sub, db)
    enroll_watcher(db, sub)
    return {"ok": True, "subscribed": True, "notify_method": body.notify_method}


@app.get("/api/watcher/status")
def api_watcher_status(request: Request, db: Session = Depends(get_db_dependency)):
    sid = _get_session_id(request)
    sub = _load(sid, db) if sid else None
    if not sub:
        raise HTTPException(400, "Session not found")
    dispatched_at = sub.get("dispatched_at")
    now = utcnow()
    tracking = {"dispatched": False, "subscribed": sub.get("watcher_subscribed", False)}
    if dispatched_at:
        dispatch_dt = datetime.fromisoformat(dispatched_at)
        days_since = (now - dispatch_dt).days
        tracking.update({
            "dispatched": True, "dispatched_at": dispatched_at,
            "days_since_dispatch": days_since,
            "confirmation": sub.get("confirmation", ""),
            "letter_count": len(sub.get("letters", [])),
            "notify_method": sub.get("notify_method", ""),
            "milestones": {
                f"day_{d}": {"days_remaining": max(0, d - days_since), "reached": days_since >= d}
                for d in [30, 60, 90]
            },
        })
    return {"ok": True, "tracking": tracking}


# ─── Status lookup ────────────────────────────────────────────────────────────

@app.get("/api/status/{confirmation}")
def api_status(confirmation: str, db: Session = Depends(get_db_dependency)):
    info = load_client_by_confirmation(db, confirmation)
    if not info:
        raise HTTPException(404, "Not found")
    return {"found": True, **info}


# ═══ ADMIN ════════════════════════════════════════════════════════════════════

@app.post("/admin/api/login")
def admin_login(body: AdminLoginRequest):
    token = authenticate(body.username, body.password)
    if not token:
        raise HTTPException(401, "Invalid credentials")
    response = JSONResponse({"ok": True, "token": token})
    response.set_cookie("admin_token", token, httponly=True, samesite="lax", max_age=28800)
    return response


def _require_admin(request: Request) -> str:
    token = request.cookies.get("admin_token", "")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    username = get_current_admin(token)
    if not username:
        raise HTTPException(401, "Admin authentication required")
    return username


@app.get("/admin/api/submissions")
def admin_submissions(request: Request, db: Session = Depends(get_db_dependency)):
    _require_admin(request)
    stats = get_stats(db)
    clients = get_all_clients_admin(db, decrypt)
    return {"entries": clients, "stats": stats}


@app.post("/admin/api/approve-payment")
def admin_approve_payment(request: Request, db: Session = Depends(get_db_dependency)):
    _require_admin(request)
    import json as _json
    body = _json.loads(request._body) if hasattr(request, '_body') else {}
    target_sid = body.get("session_id", "")
    sub = _load(target_sid, db) if target_sid else None
    if not sub:
        raise HTTPException(404, "Submission not found")
    if sub.get("paid"):
        return {"ok": True, "already": True}
    now = utcnow()
    sub["paid"] = True
    sub["status"] = "paid"
    sub["paid_at"] = now.isoformat()
    _store(target_sid, sub, db)
    return {"ok": True, "confirmed": True, "confirmation": sub.get("confirmation")}


@app.post("/admin/api/run-agents")
def admin_run_agents(request: Request, db: Session = Depends(get_db_dependency)):
    _require_admin(request)
    enrolled = enroll_from_db(db)
    results = run_all_agents(db)
    return {"ok": True, "enrolled": enrolled, "agent_results": results}


@app.post("/admin/api/run-purge")
def admin_run_purge(request: Request, db: Session = Depends(get_db_dependency)):
    _require_admin(request)
    deleted = delete_expired_clients(db)
    return {"ok": True, "deleted": deleted}


@app.get("/admin/api/pipeline")
def admin_pipeline(request: Request, db: Session = Depends(get_db_dependency)):
    _require_admin(request)
    stats = get_pipeline_stats(db)
    log = get_recent_log(db, limit=30)
    return {"ok": True, "pipeline": stats, "agent_log": log}


@app.get("/admin/api/chain")
def admin_chain(request: Request, db: Session = Depends(get_db_dependency)):
    _require_admin(request)
    valid, count, errors = verify_chain(db)
    blocks = get_chain(db, limit=50)
    return {"ok": True, "valid": valid, "block_count": count, "errors": errors, "blocks": blocks}
