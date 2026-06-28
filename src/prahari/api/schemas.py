"""Pydantic request/response models for the Prahari API.

These mirror the dict returned by :func:`prahari.models.predict.predict`, so
the HTTP contract and the CLI stay in lock-step.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=20_000,
        description="The message or call transcript to score.",
        examples=[
            "This is CBI. You are under digital arrest. Transfer Rs 50,000 to "
            "the safe account immediately and share the OTP."
        ],
    )


class RedFlagOut(BaseModel):
    id: str
    label: str
    description: str
    weight: int
    match: str


class ScoreResponse(BaseModel):
    input: str
    score: int = Field(..., ge=0, le=100, description="Fused risk score 0-100.")
    band: str = Field(..., description="Risk band for the score.")
    is_scam: bool
    ml_probability: float
    rule_score: float
    red_flags: list[RedFlagOut]
    safe_action: str
    explanation: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
    trained_at: str | None = None
