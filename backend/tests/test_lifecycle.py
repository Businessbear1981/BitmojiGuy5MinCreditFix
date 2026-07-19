"""
End-to-end case lifecycle: terms -> case -> upload -> disputes -> letters ->
checkout (dev mode) -> download/status, plus consent-gate and fishbowl rules.
"""
import io

from tests.conftest import TEST_CASE

SAMPLE_REPORT = b"""CREDIT REPORT - TEST
Experian
MIDLAND CREDIT MGMT
Account: 12345678
Status: placed for collection
Balance: $1,240.00

CAPITAL ONE
Account: 99887766
30 days late reported 2024-08
past due amount $56.00
"""


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_case_requires_terms_token(client):
    resp = client.post("/api/case", json=TEST_CASE)
    assert resp.status_code == 422

    resp = client.post("/api/case", json=TEST_CASE, headers={"X-Terms-Token": "123.deadbeef"})
    assert resp.status_code == 422


def test_case_rejects_non_beta_zip(client, terms_token):
    body = dict(TEST_CASE, address="9 Elm St, Portland, ME 04101")
    resp = client.post("/api/case", json=body, headers={"X-Terms-Token": terms_token})
    assert resp.status_code == 403


def test_case_validates_pii_fields(client, terms_token):
    bad = dict(TEST_CASE, ssn_last4="12345")
    resp = client.post("/api/case", json=bad, headers={"X-Terms-Token": terms_token})
    assert resp.status_code == 422


def test_full_lifecycle(client, terms_token):
    # Create case (TX zip -> eligible)
    resp = client.post("/api/case", json=TEST_CASE, headers={"X-Terms-Token": terms_token})
    assert resp.status_code == 200
    data = resp.json()
    session_id = data["session_id"]
    assert data["region"] == "Texas"

    # Upload a report — keyword scanner should find collection + late payment
    resp = client.post(
        f"/api/case/{session_id}/upload",
        files={"file": ("report.txt", io.BytesIO(SAMPLE_REPORT), "text/plain")},
    )
    assert resp.status_code == 200
    suggestions = resp.json()["suggestions"]
    assert len(suggestions) >= 1
    buckets = {s["bucket"] for s in suggestions}
    assert "collection" in buckets

    # Confirm disputes
    items = [
        {"type": "bureau", "target": "Experian", "account": "12345678",
         "amount": 1240.0, "reason": "Not my account — no contract with collector"},
        {"type": "creditor", "target": "Capital One", "account": "99887766",
         "reason": "Late payment reported in error"},
    ]
    resp = client.post(f"/api/case/{session_id}/disputes", json={"items": items})
    assert resp.status_code == 200
    assert resp.json()["items_count"] == 2

    # Generate letters: 1 bureau letter (Experian) + 1 creditor letter
    resp = client.post(f"/api/case/{session_id}/letters")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    texts = [ltr["text"] for ltr in data["letters"]]
    assert any("Experian" in t for t in texts)
    assert any("1681s-2" in t for t in texts)  # FCRA 623 citation on creditor letter
    assert "MASTER COVER SHEET" in data["cover_sheet"]

    # Payment required before download / mail-status
    assert client.get(f"/api/case/{session_id}/download").status_code == 402
    assert client.get(f"/api/case/{session_id}/mail-status").status_code == 402

    # Checkout in dev mode (no Stripe key) marks paid + runs post-payment
    resp = client.post(f"/api/case/{session_id}/checkout")
    assert resp.status_code == 200
    assert resp.json()["paid"] is True

    # Download the PDF (regenerated in memory)
    resp = client.get(f"/api/case/{session_id}/download")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")

    # Status reflects the full journey
    resp = client.get(f"/api/case/{session_id}/status")
    assert resp.status_code == 200
    status = resp.json()
    assert status["paid"] is True
    assert status["letters_count"] == 2
    assert status["name"] == TEST_CASE["name"]


def test_multiple_uploads_all_persist(client, case_session):
    """Regression: appending to a non-empty attachments list must persist."""
    for name in ("id.png", "address.png", "report.txt"):
        resp = client.post(
            f"/api/case/{case_session}/upload",
            files={"file": (name, io.BytesIO(b"data"), "application/octet-stream")},
        )
        assert resp.status_code == 200
    # Re-read from the DB via the API — all three must survive
    resp = client.post(
        f"/api/case/{case_session}/upload",
        files={"file": ("extra.txt", io.BytesIO(b"x"), "text/plain")},
    )
    assert resp.json()["attachments"] == ["id.png", "address.png", "report.txt", "extra.txt"]


def test_upload_rejects_bad_type_and_unknown_session(client, case_session):
    resp = client.post(
        f"/api/case/{case_session}/upload",
        files={"file": ("evil.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
    )
    assert resp.status_code == 400

    resp = client.post(
        "/api/case/nope123/upload",
        files={"file": ("report.txt", io.BytesIO(b"x"), "text/plain")},
    )
    assert resp.status_code == 404


def test_fishbowl_status(client):
    resp = client.get("/api/fishbowl/status")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"TX", "CA", "WA"}
    assert all("available" in v for v in body.values())
