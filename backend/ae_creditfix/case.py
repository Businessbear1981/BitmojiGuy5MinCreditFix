
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


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
    amount: float | None = None
    opened: str | None = None
    reason: str = ""
    status: str = "open"
    letters: list[str] = field(default_factory=list)
    # Dispute category id from dispute_engine.categories. Drives which
    # violation theories the analyst tests and which statutes get cited.
    bucket: str = ""
    # Consumer's answers to the review questions for this item, keyed by
    # affirmation name (not_recognized, dofd_uncertain, confirmed_fraud, …).
    affirmations: dict[str, Any] = field(default_factory=dict)

@dataclass
class Letter:
    id: str
    type: str            # 'bureau' or 'creditor'
    target: str
    path: str
    date: str            # YYYY-MM-DD
    item_ids: list[str]
    tracking: str | None = None

@dataclass
class Case:
    client: Client
    attachments: list[str] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    letters: list[Letter] = field(default_factory=list)
    logs: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {"mail": [], "responses": []})
    phases: dict[str, Any] = field(default_factory=lambda: {"p1_docs_complete": False})

    def to_dict(self) -> dict[str, Any]:
        return {
            "client": asdict(self.client),
            "attachments": list(self.attachments),
            "items": [asdict(i) for i in self.items],
            "letters": [asdict(ltr) for ltr in self.letters],
            "logs": self.logs,
            "phases": self.phases
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Case:
        c = Client(**d["client"])
        items = [Item(**x) for x in d.get("items", [])]
        letters = [Letter(**x) for x in d.get("letters", [])]
        return Case(client=c, attachments=d.get("attachments", []), items=items, letters=letters, logs=d.get("logs", {"mail": [], "responses": []}), phases=d.get("phases", {"p1_docs_complete": False}))
