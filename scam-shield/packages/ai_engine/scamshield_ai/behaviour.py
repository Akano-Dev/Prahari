"""Build the typed :class:`BehaviourAnalysis` from the rolling state.

The rule-engine stage records behaviour intensities as it fires; this helper
projects them onto the explicit behaviour schema and derives the composite
``emotional_manipulation`` and ``confidence`` read.
"""
from __future__ import annotations

from .context import ConversationState
from .schemas import BehaviourAnalysis


def build_behaviour(state: ConversationState) -> BehaviourAnalysis:
    b = state.behaviour
    emotional = max(
        b.get("emotional_manipulation", 0.0),
        0.5 * b.get("fear", 0.0) + 0.5 * b.get("secrecy", 0.0),
    )
    return BehaviourAnalysis(
        urgency=round(b.get("urgency", 0.0), 3),
        fear=round(b.get("fear", 0.0), 3),
        authority_impersonation=round(b.get("authority_impersonation", 0.0), 3),
        money_request=round(b.get("money_request", 0.0), 3),
        credential_request=round(b.get("credential_request", 0.0), 3),
        secrecy=round(b.get("secrecy", 0.0), 3),
        threat=round(b.get("threat", 0.0), 3),
        emotional_manipulation=round(min(1.0, emotional), 3),
        video_call_pressure=round(b.get("video_call_pressure", 0.0), 3),
        confidence=state.confidence,
    )
