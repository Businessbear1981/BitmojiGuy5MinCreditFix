"""
Manual pay (Cash App / Chime): customer requests a confirmation code, admin
verifies the money landed and releases the letters.
"""
ADMIN = {"X-Admin-Key": "test-admin-key"}


def test_manual_pay_issues_code_and_keeps_it_stable(client, case_session):
    resp = client.post(f"/api/case/{case_session}/manual-pay", json={"method": "cashapp"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["pending"] is True
    assert data["confirmation"].startswith("CF-")
    assert data["handle"] == "$5mincreditfix"
    assert data["amount"] == "$24.99"
    code = data["confirmation"]

    # Switching method keeps the same code (one code per case)
    resp = client.post(f"/api/case/{case_session}/manual-pay", json={"method": "chime"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["confirmation"] == code
    assert data["method"] == "chime"
    assert data["handle"] == "$AELabsPay"

    # Status exposes the pending state so the payment page can restore itself
    status = client.get(f"/api/case/{case_session}/status").json()
    assert status["manual_pay_pending"] is True
    assert status["manual_pay_code"] == code
    assert status["manual_pay_method"] == "chime"


def test_manual_pay_rejects_bad_method_and_unknown_session(client, case_session):
    resp = client.post(f"/api/case/{case_session}/manual-pay", json={"method": "venmo"})
    assert resp.status_code == 422

    resp = client.post("/api/case/nope123/manual-pay", json={"method": "cashapp"})
    assert resp.status_code == 404


def test_admin_release_unlocks_the_case(client, case_session):
    client.post(f"/api/case/{case_session}/manual-pay", json={"method": "cashapp"})

    # Shows up in the release queue
    resp = client.get("/api/admin/pending-payments", headers=ADMIN)
    assert resp.status_code == 200
    queue = resp.json()["pending"]
    entry = next(p for p in queue if p["session_id"] == case_session)
    assert entry["method"] == "cashapp"
    assert entry["confirmation"].startswith("CF-")
    assert entry["name"] == "Jane Testcase"

    # Still locked until released
    assert client.get(f"/api/case/{case_session}/download").status_code == 402

    # Release requires the admin key
    assert client.post(f"/api/admin/release/{case_session}").status_code == 401
    resp = client.post(f"/api/admin/release/{case_session}", headers={"X-Admin-Key": "wrong"})
    assert resp.status_code == 401

    resp = client.post(f"/api/admin/release/{case_session}", headers=ADMIN)
    assert resp.status_code == 200
    assert resp.json()["released"] is True

    # Case is paid and gone from the queue; releasing twice is a no-op
    status = client.get(f"/api/case/{case_session}/status").json()
    assert status["paid"] is True
    assert status["manual_pay_pending"] is False

    queue = client.get("/api/admin/pending-payments", headers=ADMIN).json()["pending"]
    assert all(p["session_id"] != case_session for p in queue)

    resp = client.post(f"/api/admin/release/{case_session}", headers=ADMIN)
    assert resp.json()["already_paid"] is True

    # Paid case no longer offers manual pay
    resp = client.post(f"/api/case/{case_session}/manual-pay", json={"method": "cashapp"})
    assert resp.json()["already_paid"] is True


def test_admin_stats_counts_pending_manual(client, case_session):
    client.post(f"/api/case/{case_session}/manual-pay", json={"method": "chime"})
    stats = client.get("/api/admin/stats", headers=ADMIN).json()
    assert stats["pending_manual"] >= 1
