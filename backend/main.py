import uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models import SessionLocal, init_db, CreditSession
from cypher import create_letters, generate_cypher_token

app = FastAPI()
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()

@app.post("/session")
def create_session(user_data: dict, db: Session = Depends(db)):
    external_id = uuid.uuid4().hex
    cypher_token = generate_cypher_token()

    letters_path, preview = create_letters(external_id, user_data)

    s = CreditSession(
        external_id=external_id,
        cypher_token=cypher_token,
        letters_path=letters_path,
        preview_summary=preview,
        locked=True,
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    return {
        "session_id": s.external_id,
        "preview": s.preview_summary,
    }

@app.get("/session/status/{session_id}")
def session_status(session_id: str, db: Session = Depends(db)):
    s = db.query(CreditSession).filter_by(external_id=session_id).first()
    if not s:
        raise HTTPException(404)
    return {
        "locked": s.locked,
        "preview": s.preview_summary
    }

@app.get("/session/download/{session_id}")
def download(session_id: str, db: Session = Depends(db)):
    s = db.query(CreditSession).filter_by(external_id=session_id).first()
    if not s:
        raise HTTPException(404)

    if s.locked:
        raise HTTPException(402, "Locked (waiting for payment)")

    return FileResponse(s.letters_path, filename=f"{session_id}.txt")
