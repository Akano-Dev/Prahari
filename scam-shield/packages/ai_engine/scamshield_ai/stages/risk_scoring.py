"""Stage 9 — risk fusion (the only stage that sets the score).

Fuses the deterministic signals into a 0..100 call-level risk score plus a
confidence. Inputs: red-flag rule weight, scam-type match strength, behaviour
intensities, and semantic corroboration. A domain **safety floor** guarantees the
scam's signature combinations can't be buried (a missed scam is the costly error).
The LLM never participates here — it only explains afterwards.
"""
from __future__ import annotations

from ..context import ConversationState
from ..rules.red_flags import MAX_WEIGHT

# Signature combinations that imply a minimum score regardless of other signals.
_SIGNATURE = "digital_arrest"
_COERCION = {"money_demand", "credential_request", "authority_impersonation"}


class RiskScoringStage:
    name = "risk_scoring"

    def process(self, utterance: str, state: ConversationState) -> None:
        fired = list(state.signals.values())
        rule_w = sum(f.weight for f in fired)
        rule_component = rule_w / (rule_w + 3.5) if rule_w else 0.0

        top_type = max(state.scam_type_scores.values(), default=0.0)
        behaviour_component = (sum(state.behaviour.values()) / max(len(state.behaviour), 1)
                               if state.behaviour else 0.0)
        semantic_component = max((s for _, s in state.semantic_hits), default=0.0)

        fused = (0.45 * rule_component +
                 0.25 * min(top_type, 1.0) +
                 0.20 * behaviour_component +
                 0.10 * semantic_component)
        score = int(round(100 * fused))

        fired_ids = set(state.signals)
        score = max(score, self._safety_floor(fired_ids))
        state.risk_score = max(0, min(100, score))

        # Confidence: more corroborating, independent signals ⇒ more confident.
        breadth = len({f.behaviour for f in fired})
        state.confidence = round(min(1.0,
            0.2 + 0.18 * breadth + 0.25 * min(top_type, 1.0) +
            0.2 * (rule_w / MAX_WEIGHT if MAX_WEIGHT else 0)), 3)

        state.add_timeline("risk", f"risk updated to {state.risk_score}")

    @staticmethod
    def _safety_floor(fired_ids: set[str]) -> int:
        if _SIGNATURE in fired_ids and (fired_ids & _COERCION):
            return 75
        if _SIGNATURE in fired_ids:
            return 60
        return 0
