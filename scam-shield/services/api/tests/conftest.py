"""Test fixtures — a fresh app (fresh in-memory state) per test + an auth helper."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    # A new app => a new Container => isolated in-memory repo/broker per test.
    app = create_app(Settings())
    return TestClient(app)


@pytest.fixture()
def auth(client: TestClient):
    """Register + login a user; return (headers, token)."""
    email, pw = "agent@scamshield.test", "supersecret1"
    client.post("/auth/register", json={"email": email, "password": pw})
    tok = client.post("/auth/login", json={"email": email, "password": pw}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}, tok
