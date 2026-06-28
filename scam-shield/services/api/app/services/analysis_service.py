"""Analysis orchestration — the bridge between transport and the AI engine.

Holds one rolling :class:`ConversationState` per active call, runs the hybrid
:class:`AnalysisPipeline` on each streamed utterance, persists the call + any
high-risk incident, and **publishes** every assessment to the broker so
dashboards update live. Also supports one-shot analysis of uploaded blocks
(SMS / screenshot OCR / WhatsApp export / voice transcript).
"""
from __future__ import annotations

from scamshield_ai import AnalysisPipeline, RiskAssessment
from scamshield_ai.context import ConversationState

from ..domain.models import Call, Incident
from ..realtime.broker import Broker
from ..repositories.base import Repository

INCIDENT_THRESHOLD = 75


class AnalysisService:
    def __init__(self, repo: Repository, broker: Broker, pipeline: AnalysisPipeline):
        self.repo = repo
        self.broker = broker
        self.pipeline = pipeline
        self._states: dict[str, ConversationState] = {}

    def _state_for(self, call_id: str) -> ConversationState:
        state = self._states.get(call_id)
        if state is None:
            state = self.pipeline.new_state(call_id)
            self._states[call_id] = state
        return state

    async def ingest_utterance(self, call: Call, text: str) -> RiskAssessment:
        prev_peak = call.peak_risk
        state = self._state_for(call.id)
        assessment = self.pipeline.analyze_utterance(text, state)

        call.utterances.append(text)
        call.last_assessment = assessment.model_dump(mode="json")
        call.peak_risk = max(call.peak_risk, assessment.risk_score)
        await self.repo.calls.update(call)

        # Record an incident the first time a call crosses the critical threshold.
        if assessment.risk_score >= INCIDENT_THRESHOLD and prev_peak < INCIDENT_THRESHOLD:
            await self.repo.incidents.add(Incident(
                call_id=call.id, owner_id=call.owner_id,
                risk_score=assessment.risk_score,
                scam_type=assessment.top_scam_type.category if assessment.top_scam_type else None,
                caller_number=call.caller_number,
                assessment=assessment.model_dump(mode="json"),
            ))

        payload = assessment.model_dump_json()
        await self.broker.publish(f"call:{call.id}", payload)
        await self.broker.publish(f"owner:{call.owner_id}", payload)
        return assessment

    async def analyze_block(self, text: str, call_id: str = "adhoc") -> RiskAssessment:
        """One-shot analysis of a text block (no persisted call)."""
        return self.pipeline.analyze_text(text, call_id=call_id)

    def drop_state(self, call_id: str) -> None:
        self._states.pop(call_id, None)
