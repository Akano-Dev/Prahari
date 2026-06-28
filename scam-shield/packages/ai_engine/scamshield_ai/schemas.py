"""The explainable analysis contract.

Every component — API, dashboard, and PDF report — consumes these Pydantic
models. A scam decision is *never* a bare score: a :class:`RiskAssessment`
always carries the behaviour breakdown, the fired signals with their evidence
spans, the detected entities, the scam-type scores, the officer-claim check,
the reasoning text, a confidence, a recommendation, and a timeline.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskBand(str, Enum):
    SAFE = "Safe"
    SUSPICIOUS = "Suspicious"
    HIGH_RISK = "High Risk"
    CRITICAL = "Almost Certainly a Scam"


def band_for_score(score: float) -> RiskBand:
    s = max(0.0, min(100.0, float(score)))
    if s < 25:
        return RiskBand.SAFE
    if s < 50:
        return RiskBand.SUSPICIOUS
    if s < 75:
        return RiskBand.HIGH_RISK
    return RiskBand.CRITICAL


class EvidenceSpan(BaseModel):
    """The exact text that triggered a signal (for highlighting in the UI)."""
    text: str
    utterance_index: int = 0
    start: Optional[int] = None
    end: Optional[int] = None


class Signal(BaseModel):
    """A fired detection signal — the atom of explainability."""
    id: str
    label: str
    description: str
    weight: int = Field(ge=1, le=3)
    behaviour: str  # which behaviour bucket this maps to
    evidence: list[EvidenceSpan] = Field(default_factory=list)


class Entity(BaseModel):
    """A named entity extracted from the conversation."""
    type: str  # PERSON | AGENCY | DESIGNATION | LOCATION | MONEY | PHONE | OTP | BANK | LINK | CASE_REF
    value: str
    normalized: Optional[str] = None
    utterance_index: int = 0


class BehaviourAnalysis(BaseModel):
    """0..1 intensity per manipulation behaviour the spec calls out."""
    urgency: float = 0.0
    fear: float = 0.0
    authority_impersonation: float = 0.0
    money_request: float = 0.0
    credential_request: float = 0.0
    secrecy: float = 0.0
    threat: float = 0.0
    emotional_manipulation: float = 0.0
    video_call_pressure: float = 0.0
    confidence: float = 0.0  # how confident the behaviour read is


class ScamTypeScore(BaseModel):
    category: str   # stable id, e.g. "digital_arrest"
    label: str      # human label, e.g. "Digital Arrest"
    score: float    # 0..1 match strength


class OfficerClaim(BaseModel):
    """Extracted government-official claim + a consistency verdict.

    We do NOT assert identity. We judge whether the *requests and behaviour* are
    consistent with how a real official operates, and flag impossible claims.
    """
    claimed: bool = False
    name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    consistency: str = "unknown"  # consistent | suspicious | impossible | unknown
    notes: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    index: int          # utterance index (proxy for time)
    kind: str           # signal | risk | entity | officer | note
    label: str
    detail: Optional[str] = None
    risk_after: Optional[int] = None


class SentenceAnalysis(BaseModel):
    """Per-utterance result, used for the live conversation timeline."""
    index: int
    text: str
    language: str
    risk_delta: float
    signals: list[Signal] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    intents: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """The fused, call-level, fully-explainable verdict."""
    call_id: str
    risk_score: int = Field(ge=0, le=100)
    band: RiskBand
    is_scam: bool
    confidence: float
    languages: list[str] = Field(default_factory=list)

    top_scam_type: Optional[ScamTypeScore] = None
    scam_types: list[ScamTypeScore] = Field(default_factory=list)

    behaviour: BehaviourAnalysis = Field(default_factory=BehaviourAnalysis)
    signals: list[Signal] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    officer_claim: Optional[OfficerClaim] = None

    reasoning: str = ""
    recommendation: str = ""
    timeline: list[TimelineEvent] = Field(default_factory=list)

    n_utterances: int = 0
