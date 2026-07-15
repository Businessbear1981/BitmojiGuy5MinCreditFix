# 5 Minutes to Credit Wellness — Hash-Chain Immutable Ledger
# AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital
# AE.CC.001
#
# Every significant action (enroll, letter generation, notification, payment)
# is appended to a hash chain. Each block references the previous block's hash.
# Tamper-evident: if any block is modified, verification fails downstream.

import json
import hashlib
from datetime import datetime

from sqlalchemy.orm import Session

from api.database import LedgerBlock, AgentLog, utcnow


GENESIS_HASH = "0" * 64


def _compute_hash(prev_hash: str, timestamp: str, session_id: str, action: str, data: str) -> str:
    raw = f"{prev_hash}|{timestamp}|{session_id}|{action}|{data}"
    return hashlib.sha256(raw.encode()).hexdigest()


def init_chain(db: Session):
    """Write genesis block if chain is empty."""
    count = db.query(LedgerBlock).count()
    if count > 0:
        return
    ts = utcnow().isoformat()
    data = json.dumps({"action": "genesis", "message": "AE Labs Watcher Chain initialized"}, sort_keys=True)
    block_hash = _compute_hash(GENESIS_HASH, ts, "SYSTEM", "genesis", data)
    block = LedgerBlock(
        prev_hash=GENESIS_HASH,
        timestamp=datetime.fromisoformat(ts),
        session_id="SYSTEM",
        action="genesis",
        data=data,
        block_hash=block_hash,
    )
    db.add(block)
    db.commit()


def write_block(db: Session, session_id: str, action: str, data_dict: dict) -> str:
    """Append a block to the chain. Returns the new block hash."""
    prev = db.query(LedgerBlock).order_by(LedgerBlock.id.desc()).first()
    prev_hash = prev.block_hash if prev else GENESIS_HASH
    ts = utcnow().isoformat()
    data_str = json.dumps(data_dict, sort_keys=True)
    block_hash = _compute_hash(prev_hash, ts, session_id, action, data_str)
    block = LedgerBlock(
        prev_hash=prev_hash,
        timestamp=datetime.fromisoformat(ts),
        session_id=session_id,
        action=action,
        data=data_str,
        block_hash=block_hash,
    )
    db.add(block)
    db.commit()
    return block_hash


def verify_chain(db: Session) -> tuple[bool, int, list[str]]:
    """Verify integrity of the entire chain. Returns (valid, block_count, errors)."""
    blocks = db.query(LedgerBlock).order_by(LedgerBlock.id.asc()).all()
    errors = []
    prev_hash = GENESIS_HASH
    for block in blocks:
        if block.prev_hash != prev_hash:
            errors.append(f"Block {block.id}: prev_hash mismatch")
        expected = _compute_hash(
            block.prev_hash,
            block.timestamp.isoformat() if isinstance(block.timestamp, datetime) else block.timestamp,
            block.session_id,
            block.action,
            block.data,
        )
        if block.block_hash != expected:
            errors.append(f"Block {block.id}: hash mismatch — tampered")
        prev_hash = block.block_hash
    return len(errors) == 0, len(blocks), errors


def get_chain(db: Session, session_id: str | None = None, limit: int = 50) -> list[dict]:
    """Get chain blocks, optionally filtered by session_id."""
    q = db.query(LedgerBlock)
    if session_id:
        q = q.filter(LedgerBlock.session_id == session_id)
    blocks = q.order_by(LedgerBlock.id.desc()).limit(limit).all()
    return [
        {
            "id": b.id,
            "prev_hash": b.prev_hash,
            "timestamp": b.timestamp.isoformat() if isinstance(b.timestamp, datetime) else b.timestamp,
            "session_id": b.session_id,
            "action": b.action,
            "data": b.data,
            "block_hash": b.block_hash,
        }
        for b in blocks
    ]


# ═════════════════════════════════════════════════════════════════════════════
# AGENT LOG — lightweight action log (not chain-linked)
# ═════════════════════════════════════════════════════════════════════════════

def log_action(db: Session, session_id: str, agent: str, action: str, detail: str = ""):
    """Log an agent action and write it to the chain."""
    entry = AgentLog(
        session_id=session_id,
        agent=agent,
        action=action,
        detail=detail,
    )
    db.add(entry)

    try:
        data_dict = json.loads(detail) if detail else {}
    except (json.JSONDecodeError, TypeError):
        data_dict = {"detail": detail}
    data_dict["agent"] = agent

    write_block(db, session_id, action, data_dict)
    db.commit()


def get_recent_log(db: Session, limit: int = 50) -> list[dict]:
    """Get recent agent log entries."""
    rows = db.query(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit).all()
    return [
        {
            "session_id": r.session_id,
            "agent": r.agent,
            "action": r.action,
            "detail": r.detail,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
