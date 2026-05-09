
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .case import Case
from .storage import load_json, CASE_FILE

def parse_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d")

def compute_deadlines(case: Case) -> List[Dict[str, Any]]:
    rows = []
    mail_idx = {m["letter_id"]: m for m in case.logs.get("mail", [])}
    for l in case.letters:
        start = mail_idx.get(l.id, {}).get("date", l.date)
        due = (parse_date(start) + timedelta(days=30)).strftime("%Y-%m-%d")
        rows.append({"letter_id": l.id, "type": l.type, "target": l.target, "mailed": start, "due": due, "tracking": l.tracking})
    return sorted(rows, key=lambda r: r["due"])
