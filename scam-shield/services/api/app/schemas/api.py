"""HTTP request/response schemas for the API surface."""
from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class _EmailModel(BaseModel):
    """Base carrying the email validator (must be a BaseModel for Pydantic v2)."""

    @field_validator("email", check_fields=False)
    @classmethod
    def _validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("invalid email address")
        return v.lower()


class RegisterRequest(_EmailModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    display_name: str = ""


class LoginRequest(_EmailModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    avatar: Optional[str] = None
    created_at: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    """Patch the current user's profile. Omitted fields are left unchanged;
    pass avatar="" to clear the picture."""
    display_name: Optional[str] = Field(default=None, max_length=80)
    # ~1.9MB base64 ceiling keeps a profile picture reasonable for in-memory/JSON.
    avatar: Optional[str] = Field(default=None, max_length=2_600_000)

    @field_validator("avatar")
    @classmethod
    def _validate_avatar(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not v.startswith("data:image/"):
            raise ValueError("avatar must be a data:image/* URL or empty to clear")
        return v


class CreateCallRequest(BaseModel):
    caller_number: str = "unknown"
    contact_name: Optional[str] = None
    is_known_contact: bool = False


class CallResponse(BaseModel):
    id: str
    caller_number: str
    contact_name: Optional[str]
    is_known_contact: bool
    status: str
    peak_risk: int
    n_utterances: int
    last_assessment: Optional[dict] = None


class UtteranceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class AnalyzeBlockRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    source: str = Field("sms", description="sms | screenshot | whatsapp | voice | other")


class IncidentResponse(BaseModel):
    id: str
    call_id: str
    risk_score: int
    scam_type: Optional[str]
    caller_number: str
    created_at: str


class StatsResponse(BaseModel):
    total_calls: int
    total_incidents: int
    scam_calls: int
    avg_peak_risk: float
    by_scam_type: dict[str, int]
