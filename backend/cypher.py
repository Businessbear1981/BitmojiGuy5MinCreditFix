import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "generated_docs"
DOCS_DIR.mkdir(exist_ok=True)

def generate_cypher_token():
    return uuid.uuid4().hex

def create_letters(external_id: str, user_data: dict):
    preview = {
        "id_errors": 3,
        "factual_errors": 5,
        "obsolete_items": 2,
        "unverifiable_items": 4,
    }

    session_folder = DOCS_DIR / external_id
    session_folder.mkdir(exist_ok=True)
    letters = session_folder / "dispute_letters.txt"

    content = [
        "AE Impact—Dispute Letters",
        f"Generated {datetime.utcnow().isoformat()}Z",
        "",
        "This is where the full letter packet goes.",
        "User data:",
        str(user_data),
    ]
    letters.write_text("\n".join(content), encoding="utf-8")

    return str(letters), str(preview)
