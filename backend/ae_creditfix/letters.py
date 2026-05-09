
from __future__ import annotations
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import List, Tuple
from .case import Case, Item, Letter, new_id
from .templates import HEADER, BUREAU_BODY, CREDITOR_BODY, COVER_SHEET, FCRA, BUREAU_ADDRESSES
from .storage import OUT

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def make_items_block(items: List[Item]) -> str:
    lines = []
    for it in items:
        parts = [f"- {it.target} | {it.account or 'N/A'}"]
        if it.amount is not None: parts.append(f"${it.amount:.2f}")
        if it.opened: parts.append(f"opened {it.opened}")
        parts.append(f"reason: {it.reason or 'N/A'}")
        lines.append("  " + " | ".join(parts))
    return "\n".join(lines) if lines else "  (none)"

def write_text(prefix: str, body: str) -> Path:
    fn = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = OUT / fn
    with open(path, "w", encoding="utf-8") as f:
        f.write(body + "\n")
    return path

def gen_bureau_letters(case: Case) -> List[Tuple[str,str,Path]]:
    client = case.client
    groups = {}
    for it in case.items:
        if it.type == "bureau" and it.status == "open":
            groups.setdefault(it.target, []).append(it)

    created = []
    for bureau, items in groups.items():
        ltr_id = new_id("LTR")
        header = HEADER.format(name=client.name, address=client.address, phone=client.phone, email=client.email, dob=client.dob, ssn_last4=client.ssn_last4, today=today_str())
        body = header + "\n" + BUREAU_BODY.format(name=client.name, target=bureau, items_block=make_items_block(items), cit_609=FCRA["609"], cit_611=FCRA["611"])
        body += f"\n\nMail to: {bureau} — {BUREAU_ADDRESSES.get(bureau, '(address TBD)')}"
        path = write_text(f"{ltr_id}_{bureau.replace(' ','_')}", body)
        case.letters.append(Letter(id=ltr_id, type="bureau", target=bureau, path=str(path), date=today_str(), item_ids=[i.id for i in items]))
        for it in items:
            it.letters.append(ltr_id)
        created.append((ltr_id, bureau, path))
    return created

def gen_creditor_letters(case: Case) -> List[Tuple[str,str,Path]]:
    client = case.client
    created = []
    for it in case.items:
        if it.type == "creditor" and it.status == "open":
            ltr_id = new_id("LTR")
            header = HEADER.format(name=client.name, address=client.address, phone=client.phone, email=client.email, dob=client.dob, ssn_last4=client.ssn_last4, today=today_str())
            body = header + "\n" + CREDITOR_BODY.format(name=client.name, target=it.target, account=it.account or "N/A", reason=it.reason or "N/A", cit_623=FCRA["623"])
            path = write_text(f"{ltr_id}_{it.target.replace(' ','_')}", body)
            case.letters.append(Letter(id=ltr_id, type="creditor", target=it.target, path=str(path), date=today_str(), item_ids=[it.id]))
            it.letters.append(ltr_id)
            created.append((ltr_id, it.target, path))
    return created

def gen_cover_sheet(case: Case) -> Path:
    c = case.client
    p2 = sum(1 for it in case.items if it.type=="bureau" and it.status=="open")
    p3 = sum(1 for it in case.items if it.type=="creditor" and it.status=="open")
    body = COVER_SHEET.format(name=c.name, dob=c.dob, ssn_last4=c.ssn_last4, phone=c.phone, email=c.email, address=c.address, today=today_str(), p1="Yes" if case.phases.get("p1_docs_complete") else "No", p2_count=p2, p3_count=p3, p4="Pending", attachments=", ".join(case.attachments) or "(none)")
    path = write_text("COVER", body)
    return path
