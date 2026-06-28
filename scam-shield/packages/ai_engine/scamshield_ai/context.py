"""Rolling per-call conversation state shared across pipeline stages.

A single :class:`ConversationState` accumulates everything the stages produce as
utterances stream in, so risk is computed over the *whole* conversation so far —
not just the latest sentence. The pipeline reads this state to emit a
:class:`~scamshield_ai.schemas.RiskAssessment` snapshot after every utterance.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import Entity, OfficerClaim, Signal, TimelineEvent


@dataclass
class ConversationState:
    call_id: str
    utterances: list[str] = field(default_factory=list)

    languages: set[str] = field(default_factory=set)
    # Signals deduped by id; evidence spans accumulate across utterances.
    signals: dict[str, Signal] = field(default_factory=dict)
    entities: list[Entity] = field(default_factory=list)
    intents: set[str] = field(default_factory=set)

    # behaviour bucket -> 0..1 intensity (max across utterances)
    behaviour: dict[str, float] = field(default_factory=dict)
    # scam category id -> 0..1 accumulated match strength
    scam_type_scores: dict[str, float] = field(default_factory=dict)

    officer: OfficerClaim = field(default_factory=OfficerClaim)
    timeline: list[TimelineEvent] = field(default_factory=list)

    risk_score: int = 0
    confidence: float = 0.0
    semantic_hits: list[tuple[str, float]] = field(default_factory=list)
    kb_notes: list[str] = field(default_factory=list)
    reasoning: str = ""

    @property
    def full_text(self) -> str:
        return " ".join(self.utterances)

    @property
    def current_index(self) -> int:
        return len(self.utterances) - 1

    def bump_behaviour(self, bucket: str, value: float) -> None:
        self.behaviour[bucket] = max(self.behaviour.get(bucket, 0.0), value)

    def add_timeline(self, kind: str, label: str, detail: str | None = None) -> None:
        self.timeline.append(TimelineEvent(
            index=max(self.current_index, 0), kind=kind, label=label,
            detail=detail, risk_after=self.risk_score,
        ))
