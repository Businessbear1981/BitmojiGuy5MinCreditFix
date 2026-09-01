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
    body = dict(TEST_CASE, address="9 Elm St", city="Portland", state="ME", zip="04101")
    resp = client.post("/api/case", json=body, headers={"X-Terms-Token": terms_token})
    assert resp.status_code == 403
    assert "04101" in resp.json()["detail"]


def test_case_uses_zip_field_not_street_number(client, terms_token):
    """A 5-digit street number must not be mistaken for the postcode."""
    body = dict(TEST_CASE, address="15255 Main St")
    resp = client.post("/api/case", json=body, headers={"X-Terms-Token": terms_token})
    assert resp.status_code == 200
    assert resp.json()["region"] == "Texas"


def test_case_requires_a_mailable_address(client, terms_token):
    """
    Every field the mail carrier needs is validated at intake.

    A letter that cannot be addressed cannot be mailed, and the failure used
    to be invisible: Lob rejected the payload, the error was swallowed, and
    the customer was told their dispute had been posted.
    """
    for bad in (
        dict(TEST_CASE, state="Texas"),      # full name, not the 2-letter code
        dict(TEST_CASE, state="ZZ"),         # not a real state
        dict(TEST_CASE, zip="ABCDE"),        # not digits
        dict(TEST_CASE, zip="752"),          # too short
        dict(TEST_CASE, city=" "),           # whitespace only
    ):
        resp = client.post("/api/case", json=bad, headers={"X-Terms-Token": terms_token})
        assert resp.status_code == 422, f"accepted an unmailable address: {bad}"

    # ZIP+4 is a valid postcode and must be accepted.
    ok = dict(TEST_CASE, zip="75201-1234")
    resp = client.post("/api/case", json=ok, headers={"X-Terms-Token": terms_token})
    assert resp.status_code == 200


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

    # Required disclosures gate letter generation (428 without them). Affirm
    # every id the server requires rather than a fixed list, so adding a
    # disclosure fails the endpoint rather than silently skipping it here.
    from disclosures import REQUIRED_IDS

    resp = client.post(
        f"/api/case/{session_id}/acknowledge",
        json={"acknowledgements": {aid: True for aid in REQUIRED_IDS}},
    )
    assert resp.status_code == 200

    # Generate letters: 1 bureau letter (Experian) + 1 creditor letter
    resp = client.post(f"/api/case/{session_id}/letters")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert "MASTER COVER SHEET" in data["cover_sheet"]

    # Unpaid: metadata only. This assertion used to read the letter text and
    # look for the FCRA citation in it — which passed only because unpaid
    # callers were being served the whole letter. The paywall is the product.
    assert {ltr["target"] for ltr in data["letters"]} == {"Experian", "Capital One"}
    for ltr in data["letters"]:
        assert ltr["locked"] is True
        assert "1681s-2" not in ltr["text"]
        assert "SECTION" not in ltr["text"]
        assert "Sincerely" not in ltr["text"]

    # Payment required before download / mail-status
    assert client.get(f"/api/case/{session_id}/download").status_code == 402
    assert client.get(f"/api/case/{session_id}/mail-status").status_code == 402

    # Checkout in dev mode (no Stripe key) marks paid + runs post-payment
    resp = client.post(f"/api/case/{session_id}/checkout")
    assert resp.status_code == 200
    assert resp.json()["paid"] is True

    # Paid: the real letters, with the statutory basis on each.
    resp = client.get(f"/api/case/{session_id}/letters")
    assert resp.status_code == 200
    texts = [ltr["text"] for ltr in resp.json()["letters"]]
    assert any("Experian" in t for t in texts)
    assert any("1681s-2" in t for t in texts)  # FCRA 623 citation

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


def test_outcome_ledger_records_a_dispatched_round(client, case_session):
    """
    The ledger has to actually receive a row, and scoring has to be able to
    read it back.

    Until `init_outcomes()` was called at startup, `dispute_outcomes` did not
    exist: every lookup raised, the error was swallowed, and `scoring` served
    hardcoded priors while advertising a "measured" label it could never
    produce. A green suite proved nothing, because nothing wrote to the ledger.

    Lob is unconfigured under test, so `send_all_letters` returns no results
    and the mail route never reaches a real dispatch. This drives the recording
    helper directly — the unit that a real dispatch calls.
    """
    import main
    import outcomes
    from database import CaseRecord, SessionLocal

    items = [
        {"type": "bureau", "target": "Experian", "account": "12345678",
         "bucket": "collection", "amount": 1240.0, "reason": "Not mine"},
    ]
    resp = client.post(f"/api/case/{case_session}/disputes", json={"items": items})
    assert resp.status_code == 200

    before = outcomes.ledger_stats()["disputes_logged"]

    db = SessionLocal()
    try:
        record = db.query(CaseRecord).filter_by(session_id=case_session).first()
        main._record_dispatched_disputes(record, tier=1)
    finally:
        db.close()

    after = outcomes.ledger_stats()
    assert after["disputes_logged"] == before + 1, "a dispatched item did not reach the ledger"

    # Re-dispatching the same round must not double-count it.
    db = SessionLocal()
    try:
        record = db.query(CaseRecord).filter_by(session_id=case_session).first()
        main._record_dispatched_disputes(record, tier=1)
    finally:
        db.close()
    assert outcomes.ledger_stats()["disputes_logged"] == after["disputes_logged"]

    # Closing the loop makes the row countable, and the rate is readable
    # rather than raising the way it did before.
    stored = {"account": "12345678", "target": "Experian"}
    assert outcomes.record_result(case_session, stored, "Experian", "deleted") is True

    rate = outcomes.removal_rate(category="collection", bureau="Experian")
    assert rate["n"] >= 1
    # One observation is not a measurement: below MIN_SAMPLE_FOR_RATE the
    # ledger must refuse to call it confident, so scoring keeps using priors.
    assert rate["confident"] is False
