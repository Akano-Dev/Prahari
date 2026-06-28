"""Domain models — the persistence-agnostic entities.

Plain Pydantic models so they serialize cleanly over HTTP/WS and are independent
of whether the repository is in-memory or SQLAlchemy/Postgres.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(BaseModel):
    id: str = Field(default_factory=_uuid)
    email: str
    password_hash: str
    display_name: str = ""
    avatar: Optional[str] = None          # data-URL (data:image/...;base64,...) or None
    created_at: datetime = Field(default_factory=_now)


class CallStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"


class Call(BaseModel):
    id: str = Field(default_factory=_uuid)
    owner_id: str
    caller_number: str = "unknown"
    contact_name: Optional[str] = None
    is_known_contact: bool = False
    status: CallStatus = CallStatus.ACTIVE
    started_at: datetime = Field(default_factory=_now)
    ended_at: Optional[datetime] = None
    utterances: list[str] = Field(default_factory=list)
    # Latest assessment snapshot (RiskAssessment.model_dump()), kept for fast reads.
    last_assessment: Optional[dict] = None
    peak_risk: int = 0


class Incident(BaseModel):
    """A persisted high-risk detection, for the 'Past Incidents' panel."""
    id: str = Field(default_factory=_uuid)
    call_id: str
    owner_id: str
    risk_score: int
    scam_type: Optional[str] = None
    caller_number: str = "unknown"
    created_at: datetime = Field(default_factory=_now)
    assessment: dict = Field(default_factory=dict)
