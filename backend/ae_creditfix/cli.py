
from __future__ import annotations
import argparse, csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .storage import set_root, WORK, CASE_FILE, OUT, LOGS, save_json, load_json
from .case import Case, Client, Item
from .letters import gen_bureau_letters, gen_creditor_letters, gen_cover_sheet
from .deadlines import compute_deadlines

def today():
    return datetime.now().strftime("%Y-%m-%d")

def load_case() -> Case:
    if not CASE_FILE.exists():
        raise SystemExit("No case found. Run: setup-case")
    return Case.from_dict(load_json(CASE_FILE))

def save_case(case: Case):
    save_json(CASE_FILE, case.to_dict())

def cmd_setup(args):
    set_root(args.root)
    case = Case(client=Client(name=args.name, address=args.address, dob=args.dob, ssn_last4=str(args.ssn_last4), phone=args.phone, email=args.email))
    save_case(case)
    print(f"Case initialized at {CASE_FILE}")

def cmd_add_item(args):
    case = load_case()
    item = Item(id=f"ITM{datetime.now().strftime('%H%M%S')}", type=args.type, target=args.target, account=args.account, amount=args.amount, opened=args.opened, reason=args.reason)
    case.items.append(item)
    save_case(case)
    print(f"Item added: {item.id} -> {item.target}")

def cmd_add_attachment(args):
    case = load_case()
    case.attachments.append(args.path)
    save_case(case)
    print("Attachment logged.")

def cmd_gen_letters(args):
    case = load_case()
    made = gen_bureau_letters(case) if args.phase==2 else gen_creditor_letters(case)
    save_case(case)
    if not made:
        print("No open items to generate letters for.")
    else:
        print("Generated letters:")
        for ltr_id, target, path in made:
            print(f"  {ltr_id} -> {target} :: {path}")

def cmd_log_mail(args):
    case = load_case()
    letter = next((l for l in case.letters if l.id==args.letter_id), None)
    if not letter:
        raise SystemExit("Letter not found.")
    letter.tracking = args.tracking
    case.logs.setdefault("mail", []).append({"letter_id": letter.id, "date": args.date or today(), "tracking": args.tracking})
    save_case(case)
    # CSV
    csvp = LOGS / "certified_mail_log.csv"
    header = not csvp.exists()
    with open(csvp, "a", newline="", encoding="utf-8") as f:
        import csv as _csv
        w = _csv.writer(f)
        if header: w.writerow(["date","letter_id","target","tracking","path"])
        w.writerow([args.date or today(), letter.id, letter.target, args.tracking, letter.path])
    print("Mail logged.")

def cmd_log_response(args):
    case = load_case()
    it = next((x for x in case.items if x.id==args.item_id), None)
    if not it: raise SystemExit("Item not found.")
    it.status = "closed" if args.outcome.lower() in {"deleted","corrected","resolved"} else "open"
    case.logs.setdefault("responses", []).append({"item_id": it.id, "date": args.date or today(), "outcome": args.outcome, "notes": args.notes or ""})
    save_case(case)
    print("Response logged.")

def cmd_deadlines(args):
    case = load_case()
    rows = compute_deadlines(case)
    if not rows:
        print("No deadlines yet. Use log-mail to start the clock.")
        return
    print("Deadlines (30 days from mailed):")
    for r in rows:
        print(f"  {r['due']} | {r['letter_id']} -> {r['target']} ({r['type']}) | mailed {r['mailed']} | tracking {r['tracking'] or '-'}")


def cmd_summary(args):
    case = load_case()
    c = case.client
    print(f"Client: {c.name} ({c.dob})  SSN last4: {c.ssn_last4}")
    print(f"Contact: {c.phone} | {c.email}")
    print(f"Address: {c.address}")
    print(f"Attachments: {len(case.attachments)}  Items: {len(case.items)}  Letters: {len(case.letters)}")
    for l in case.letters[-5:]:
        print(f"  {l.date} {l.id} -> {l.target} ({l.type})  {l.path}")

def main(argv=None):
    p = argparse.ArgumentParser(prog="aecreditfix", description="AE CreditFix Platform (Arden Edge)")
    p.add_argument("--root", help="Project root (default: current directory)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("setup-case"); 
    s1.add_argument("--name", required=True)
    s1.add_argument("--address", required=True)
    s1.add_argument("--dob", required=True)
    s1.add_argument("--ssn-last4", required=True)
    s1.add_argument("--phone", required=True)
    s1.add_argument("--email", required=True)
    s1.set_defaults(func=cmd_setup)

    s2 = sub.add_parser("add-item"); 
    s2.add_argument("--type", choices=["bureau","creditor"], required=True)
    s2.add_argument("--target", required=True)
    s2.add_argument("--account", required=True)
    s2.add_argument("--amount", type=float)
    s2.add_argument("--opened")
    s2.add_argument("--reason", required=True)
    s2.set_defaults(func=cmd_add_item)

    s3 = sub.add_parser("add-attachment")
    s3.add_argument("--path", required=True)
    s3.set_defaults(func=cmd_add_attachment)

    s4 = sub.add_parser("gen-letters")
    s4.add_argument("--phase", type=int, choices=[2,3], required=True)
    s4.set_defaults(func=cmd_gen_letters)

    s5 = sub.add_parser("log-mail")
    s5.add_argument("--letter-id", required=True)
    s5.add_argument("--tracking", required=True)
    s5.add_argument("--date")
    s5.set_defaults(func=cmd_log_mail)

    s6 = sub.add_parser("log-response")
    s6.add_argument("--item-id", required=True)
    s6.add_argument("--outcome", required=True)
    s6.add_argument("--notes")
    s6.add_argument("--date")
    s6.set_defaults(func=cmd_log_response)

    s7 = sub.add_parser("deadlines"); s7.set_defaults(func=cmd_deadlines)
    s8 = sub.add_parser("summary");   s8.set_defaults(func=cmd_summary)

    args = p.parse_args(argv)
    # set root if provided
    from .storage import set_root as _set
    _set(args.root)
    args.func(args)

if __name__ == "__main__":
    main()
