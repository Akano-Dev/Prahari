"""The hybrid detection pipeline — orchestrator.

Wires the dependency-injected stages in order and exposes two entry points:

* :meth:`AnalysisPipeline.analyze_utterance` — feed one streamed sentence; get an
  updated, fully-explainable :class:`RiskAssessment` snapshot. This powers live
  call analysis.
* :meth:`AnalysisPipeline.analyze_text` — split a block of text (SMS, screenshot
  OCR, WhatsApp export, voice transcript) into sentences and analyse them in one
  shot.

The default stage stack runs with **zero external models or API keys**. Swap any
stage for a heavier adapter (spaCy NER, Sentence-Transformers, a real LLM) without
touching this orchestrator.
"""
from __future__ import annotations

import re

from .behaviour import build_behaviour
from .categories import CATEGORIES_BY_ID
from .context import ConversationState
from .llm.base import LLMProvider
from .schemas import RiskAssessment, ScamTypeScore, band_for_score
from .stages.base import Stage
from .stages.intent import IntentStage
from .stages.knowledge_base import KnowledgeBaseStage
from .stages.language_detection import LanguageDetectionStage
from .stages.llm_reasoning import LLMReasoningStage
from .stages.ner import NerStage
from .stages.officer_verification import OfficerVerificationStage
from .stages.pattern_matching import PatternMatchingStage
from .stages.risk_scoring import RiskScoringStage
from .stages.rule_engine import RuleEngineStage
from .stages.semantic_similarity import SemanticSimilarityStage

DECISION_THRESHOLD = 50
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。])\s+|\n+|।\s*")

RECOMMENDATIONS = {
    "critical": (
        "Hang up immediately. This is almost certainly a scam. Do not transfer "
        "money, share OTPs or stay on the call. Report at cybercrime.gov.in or "
        "call 1930."),
    "high": (
        "Treat this call as dangerous. Do not share any codes or money. Hang up "
        "and verify independently using an official number you look up yourself."),
    "suspicious": (
        "Be cautious. Do not act on instructions from this call. Verify the "
        "caller through an official channel before doing anything."),
    "safe": "No strong scam indicators yet. Stay alert and never share OTPs.",
}


def default_stages(llm_provider: LLMProvider | None = None) -> list[Stage]:
    """The standard hybrid stack, in pipeline order."""
    return [
        LanguageDetectionStage(),
        NerStage(),
        IntentStage(),
        RuleEngineStage(),
        PatternMatchingStage(),
        SemanticSimilarityStage(),
        KnowledgeBaseStage(),
        OfficerVerificationStage(),
        RiskScoringStage(),          # the only stage that sets the score
        LLMReasoningStage(llm_provider),  # explanation only, runs last
    ]


class AnalysisPipeline:
    def __init__(self, stages: list[Stage] | None = None,
                 llm_provider: LLMProvider | None = None):
        self.stages = stages if stages is not None else default_stages(llm_provider)

    # -- live, sentence-by-sentence ----------------------------------------- #
    def new_state(self, call_id: str) -> ConversationState:
        return ConversationState(call_id=call_id)

    def analyze_utterance(self, utterance: str, state: ConversationState) -> RiskAssessment:
        utterance = (utterance or "").strip()
        if utterance:
            state.utterances.append(utterance)
            for stage in self.stages:
                stage.process(utterance, state)
        return self._assess(state)

    # -- one-shot block of text --------------------------------------------- #
    def analyze_text(self, text: str, call_id: str = "adhoc") -> RiskAssessment:
        state = self.new_state(call_id)
        sentences = [s for s in _SENTENCE_SPLIT.split(text or "") if s.strip()]
        assessment = self._assess(state)
        for sent in sentences:
            assessment = self.analyze_utterance(sent, state)
        return assessment

    # -- snapshot the state into the explainable contract ------------------- #
    def _assess(self, state: ConversationState) -> RiskAssessment:
        scam_types = sorted(
            (ScamTypeScore(category=cid, label=CATEGORIES_BY_ID[cid].label, score=round(sc, 4))
             for cid, sc in state.scam_type_scores.items() if cid in CATEGORIES_BY_ID),
            key=lambda s: s.score, reverse=True)
        top = scam_types[0] if scam_types else None

        score = state.risk_score
        if score >= 75:
            rec = RECOMMENDATIONS["critical"]
        elif score >= 50:
            rec = RECOMMENDATIONS["high"]
        elif score >= 25:
            rec = RECOMMENDATIONS["suspicious"]
        else:
            rec = RECOMMENDATIONS["safe"]

        return RiskAssessment(
            call_id=state.call_id,
            risk_score=score,
            band=band_for_score(score),
            is_scam=score >= DECISION_THRESHOLD,
            confidence=state.confidence,
            languages=sorted(state.languages),
            top_scam_type=top,
            scam_types=scam_types,
            behaviour=build_behaviour(state),
            signals=list(state.signals.values()),
            entities=list(state.entities),
            officer_claim=state.officer if state.officer.claimed else None,
            reasoning=state.reasoning,
            recommendation=rec,
            timeline=list(state.timeline),
            n_utterances=len(state.utterances),
        )
