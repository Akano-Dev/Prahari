"""Self-contained auth primitives — JWT (HS256) + PBKDF2 password hashing.

Implemented on the standard library so authentication works with zero extra
dependencies. The token/format are standard HS256 JWTs, so this is a drop-in for
PyJWT / a managed identity provider later (same wire format).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time


# --------------------------------------------------------------------------- #
# base64url helpers
# --------------------------------------------------------------------------- #
def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(seg: str) -> bytes:
    return base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4))


# --------------------------------------------------------------------------- #
# JWT
# --------------------------------------------------------------------------- #
class TokenError(Exception):
    """Raised when a token is missing, malformed, tampered or expired."""


def create_access_token(subject: str, secret: str, expires_seconds: int = 3600,
                        **claims) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {"sub": subject, "iat": now, "exp": now + expires_seconds, **claims}
    signing_input = f"{_b64e(json.dumps(header).encode())}.{_b64e(json.dumps(payload).encode())}"
    sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64e(sig)}"


def decode_access_token(token: str, secret: str) -> dict:
    try:
        signing_input, sig_b64 = token.rsplit(".", 1)
        expected = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64d(sig_b64), expected):
            raise TokenError("signature mismatch")
        _, payload_b64 = signing_input.split(".")
        payload = json.loads(_b64d(payload_b64))
    except TokenError:
        raise
    except Exception as exc:  # malformed
        raise TokenError("malformed token") from exc
    if payload.get("exp", 0) < time.time():
        raise TokenError("token expired")
    return payload


# --------------------------------------------------------------------------- #
# Password hashing (PBKDF2-HMAC-SHA256)
# --------------------------------------------------------------------------- #
_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _algo, iters, salt_hex, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
    except Exception:
        return False
    return hmac.compare_digest(dk.hex(), dk_hex)
