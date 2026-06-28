"""Tests for the FastAPI server."""
from __future__ import annotations

from fastapi.testclient import TestClient

from prahari.api.server import app

client = TestClient(app)


def test_health_reports_model_loaded():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_root_blurb():
    r = client.get("/")
    assert r.status_code == 200
    assert "safe_action" in r.json()


def test_web_ui_served():
    r = client.get("/app")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    body = r.text
    # The single-file UI must carry its own input and call the /score endpoint.
    assert "<textarea" in body
    assert "/score" in body


def test_score_scam_message():
    r = client.post("/score", json={
        "text": "CBI: you are under digital arrest, transfer Rs 50000 and "
                "share the OTP immediately or face arrest.",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["is_scam"] is True
    assert body["score"] >= 50
    assert len(body["red_flags"]) >= 3


def test_score_rejects_empty_text():
    r = client.post("/score", json={"text": ""})
    assert r.status_code == 422  # pydantic min_length violation
