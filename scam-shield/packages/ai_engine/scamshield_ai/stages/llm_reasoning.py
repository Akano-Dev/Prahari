"""Stage (advisory) — LLM reasoning / explanation.

Builds a compact, factual prompt from the deterministic findings and asks the
injected :class:`LLMProvider` to phrase a 2-3 sentence explanation. The default
provider is the no-network deterministic stub, so this stage always produces
useful reasoning. The LLM output is **explanation only** — it cannot change the
score (risk_scoring already ran).
"""
from __future__ import annotations

from ..categories import CATEGORIES_BY_ID
from ..context import ConversationState
from ..llm.base import DeterministicStubProvider, LLMProvider


class LLMReasoningStage:
    name = "llm_reasoning"

    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider or DeterministicStubProvider()

    def process(self, utterance: str, state: ConversationState) -> None:
        top_id = max(state.scam_type_scores, key=state.scam_type_scores.get,
                     default=None) if state.scam_type_scores else None
        top_label = CATEGORIES_BY_ID[top_id].label if top_id else None
        signals = [s.label for s in state.signals.values()]
        behaviours = [b for b, v in sorted(state.behaviour.items(), key=lambda kv: -kv[1]) if v >= 0.5]

        context = {
            "risk_score": state.risk_score,
            "top_scam_type": top_label,
            "signals": signals,
            "behaviours": behaviours,
            "kb_notes": state.kb_notes,
        }
        prompt = self._build_prompt(state, top_label, signals, behaviours)
        try:
            state.reasoning = self.provider.reason(prompt, context)
        except Exception as exc:  # never let an LLM error break detection
            state.reasoning = DeterministicStubProvider().reason(prompt, context)
            state.add_timeline("note", "llm fallback", detail=str(exc)[:80])

    @staticmethod
    def _build_prompt(state: ConversationState, top_label, signals, behaviours) -> str:
        lines = [
            "Deterministic scam analysis of a live call transcript:",
            f"- Risk score (already computed): {state.risk_score}/100",
            f"- Most likely scam type: {top_label or 'none'}",
            f"- Red flags fired: {', '.join(signals) or 'none'}",
            f"- Manipulation behaviours: {', '.join(behaviours) or 'none'}",
        ]
        if state.kb_notes:
            lines.append(f"- Advisories: {' | '.join(state.kb_notes[:2])}")
        lines.append("Transcript so far: " + state.full_text[:800])
        lines.append("Explain in 2-3 sentences why this is or isn't a scam.")
        return "\n".join(lines)
