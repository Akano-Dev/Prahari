"""Analysis + call lifecycle + reports tests."""
from __future__ import annotations

SCAM = ("This is the CBI. You are under digital arrest. Transfer Rs 50,000 to the "
        "safe account and share the OTP immediately or face arrest.")


def test_analyze_block_detects_scam(client, auth):
    headers, _ = auth
    r = client.post("/analyze", json={"text": SCAM, "source": "sms"}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["is_scam"] is True
    assert body["risk_score"] >= 75
    assert body["top_scam_type"]["category"] in {"digital_arrest", "fake_cbi"}
    assert body["signals"] and body["recommendation"]


def test_call_lifecycle_and_rising_risk(client, auth):
    headers, _ = auth
    call_id = client.post("/calls", json={"caller_number": "+919900112233"},
                          headers=headers).json()["id"]

    sentences = [
        "Hello, this is Inspector Sharma from the CBI.",
        "A parcel in your name was seized by customs with MDMA inside.",
        "You are under digital arrest, do not tell anyone.",
        "Transfer Rs 50,000 to the safe account and share the OTP now.",
    ]
    scores = []
    for s in sentences:
        r = client.post(f"/calls/{call_id}/utterance", json={"text": s}, headers=headers)
        assert r.status_code == 200
        scores.append(r.json()["risk_score"])

    assert scores == sorted(scores)        # non-decreasing as tactics stack
    assert scores[-1] >= 75

    call = client.get(f"/calls/{call_id}", headers=headers).json()
    assert call["peak_risk"] >= 75
    assert call["n_utterances"] == 4

    # An incident should have been recorded.
    incidents = client.get("/incidents", headers=headers).json()
    assert any(i["call_id"] == call_id for i in incidents)

    # Stats reflect the call.
    stats = client.get("/stats", headers=headers).json()
    assert stats["total_calls"] == 1 and stats["scam_calls"] == 1


def test_report_html_after_assessment(client, auth):
    headers, _ = auth
    call_id = client.post("/calls", json={}, headers=headers).json()["id"]
    client.post(f"/calls/{call_id}/utterance", json={"text": SCAM}, headers=headers)
    r = client.get(f"/calls/{call_id}/report.html", headers=headers)
    assert r.status_code == 200
    assert "ScamShield Incident Report" in r.text
    assert "<mark>" in r.text  # highlighted evidence


def test_health_reports_in_memory_mode(client):
    h = client.get("/health").json()
    assert h["status"] == "ok"
    assert h["storage"] == "in-memory" and h["broker"] == "in-memory"
    assert h["scam_categories"] >= 20
