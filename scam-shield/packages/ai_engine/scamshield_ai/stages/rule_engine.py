"""Stage 4 — the deterministic red-flag rule engine (reused from Prahari).

Runs the multilingual rule set against the utterance, records each fired rule as
an explainable :class:`Signal` (deduped across the call, accumulating evidence
spans), and bumps the matching behaviour intensity. This stage is the
decision-grade backbone; everything downstream refines or explains it.
"""
from __future__ import annotations

from ..context import ConversationState
from ..rules.red_flags import scan
from ..schemas import EvidenceSpan, Signal


class RuleEngineStage:
    name = "rule_engine"

    def process(self, utterance: str, state: ConversationState) -> None:
        idx = state.current_index
        for fired in scan(utterance):
            span = EvidenceSpan(text=fired.match, utterance_index=idx)
            existing = state.signals.get(fired.id)
            if existing:
                existing.evidence.append(span)
            else:
                state.signals[fired.id] = Signal(
                    id=fired.id, label=fired.label, description=fired.description,
                    weight=fired.weight, behaviour=fired.behaviour, evidence=[span],
                )
                state.add_timeline("signal", fired.label, detail=fired.match)
            # Behaviour intensity scales with rule severity (weight 1..3 -> ~.4..1).
            state.bump_behaviour(fired.behaviour, min(1.0, 0.3 + 0.25 * fired.weight))
