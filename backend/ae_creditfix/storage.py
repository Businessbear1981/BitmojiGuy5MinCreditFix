
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, Any

ROOT = Path.cwd()  # default to current working directory
WORK = Path("creditfix_data")
CASE_FILE = WORK / "case.json"
OUT = WORK / "outputs"
LOGS = WORK / "logs"
WORK.mkdir(exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

def set_root(path: str|None):
    global ROOT, WORK, CASE_FILE, OUT, LOGS
    ROOT = Path(path) if path else Path.cwd()
    WORK = ROOT / "creditfix_data"
    CASE_FILE = WORK / "case.json"
    OUT = WORK / "outputs"
    LOGS = WORK / "logs"
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

def save_json(path: Path, data: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
