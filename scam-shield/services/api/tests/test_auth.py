"""Auth flow tests — register, login, JWT-protected access."""
from __future__ import annotations


def test_register_and_login_and_me(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "password1"})
    assert r.status_code == 201

    r = client.post("/auth/login", json={"email": "a@b.com", "password": "password1"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.com"


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "password1"})
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "wrongpass1"})
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_duplicate_registration_conflicts(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "password1"})
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "password1"})
    assert r.status_code == 409


def test_invalid_email_rejected(client):
    r = client.post("/auth/register", json={"email": "not-an-email", "password": "password1"})
    assert r.status_code == 422


def _auth_headers(client, email="p@b.com"):
    client.post("/auth/register", json={"email": email, "password": "password1"})
    tok = client.post("/auth/login", json={"email": email, "password": "password1"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_update_profile_name_and_avatar(client):
    h = _auth_headers(client)
    av = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGMAAQAABQAB"
    r = client.patch("/auth/me", json={"display_name": "Agent Smith", "avatar": av}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["display_name"] == "Agent Smith"
    assert body["avatar"] == av
    assert body["created_at"]  # ISO timestamp present

    # Persists across a fresh /auth/me read.
    assert client.get("/auth/me", headers=h).json()["avatar"] == av

    # Empty string clears the picture; omitted display_name is left unchanged.
    r = client.patch("/auth/me", json={"avatar": ""}, headers=h)
    assert r.status_code == 200 and r.json()["avatar"] is None
    assert r.json()["display_name"] == "Agent Smith"


def test_update_profile_rejects_non_image_avatar(client):
    h = _auth_headers(client, "q@b.com")
    r = client.patch("/auth/me", json={"avatar": "javascript:alert(1)"}, headers=h)
    assert r.status_code == 422
