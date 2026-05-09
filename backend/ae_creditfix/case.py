
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from pathlib import Path
import uuid

def new_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:6].upper()}"

@dataclass
class Client:
    name: str
    address: str
    dob: str
    ssn_last4: str
    phone: str
    email: str

@dataclass
class Item:
    id: str
    type: str            # 'bureau' or 'creditor'
    target: str
    account: str
    amount: Optional[float] = None
    opened: Optional[str] = None
    reason: str = ""
    status: str = "open"
    letters: List[str] = field(default_factory=list)

@dataclass
class Letter:
    id: str
    type: str            # 'bureau' or 'creditor'
    target: str
    path: str
    date: str            # YYYY-MM-DD
    item_ids: List[str]
    tracking: Optional[str] = None

@dataclass
class Case:
    client: Client
    attachments: List[str] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    letters: List[Letter] = field(default_factory=list)
    logs: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: {"mail": [], "responses": []})
    phases: Dict[str, Any] = field(default_factory=lambda: {"p1_docs_complete": False})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client": asdict(self.client),
            "attachments": list(self.attachments),
            "items": [asdict(i) for i in self.items],
            "letters": [asdict(l) for l in self.letters],
            "logs": self.logs,
            "phases": self.phases
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Case":
        c = Client(**d["client"])
        items = [Item(**x) for x in d.get("items", [])]
        letters = [Letter(**x) for x in d.get("letters", [])]
        return Case(client=c, attachments=d.get("attachments", []), items=items, letters=letters, logs=d.get("logs", {"mail": [], "responses": []}), phases=d.get("phases", {"p1_docs_complete": False}))
