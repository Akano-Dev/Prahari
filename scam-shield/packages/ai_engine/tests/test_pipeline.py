"""Tests for the hybrid analysis pipeline."""
from __future__ import annotations

from scamshield_ai import AnalysisPipeline, RiskBand

ENGLISH_SCAM = [
    "Hello, this is Inspector Sharma from the CBI Cyber Crime branch.",
    "A parcel in your name was seized by customs and it contains MDMA.",
    "You are now under digital arrest. Do not disconnect this call and do not tell anyone.",
    "Transfer Rs 50,000 to the RBI safe account immediately and share the OTP to verify.",
]
HINGLISH_SCAM = (
    "CBI se bol raha hoon. Aap digital arrest mein hain. Phone band mat karo. "
    "Rs 50000 safe account mein turant transfer karo aur OTP bhejo warna giraftari ho jayegi."
)
LEGIT = "Hi Anita, running late for dinner, reach the restaurant by 8:30. Order starters!"


def test_live_scam_escalates_and_explains():
    pipe = AnalysisPipeline()
    state = pipe.new_state("call-1")
    scores = []
    for sent in ENGLISH_SCAM:
        a = pipe.analyze_utterance(sent, state)
        scores.append(a.risk_score)
    final = pipe.analyze_utterance("", state)

    assert final.is_scam is True
    assert final.risk_score >= 75
    assert final.band == RiskBand.CRITICAL
    # Risk should be non-decreasing as tactics stack up.
    assert scores == sorted(scores)
    # Explainability: signals with evidence, a scam type, a recommendation, reasoning.
    assert {s.id for s in final.signals} >= {"digital_arrest", "money_demand", "credential_request"}
    assert all(s.evidence for s in final.signals)
    assert final.top_scam_type is not None
    assert final.reasoning and final.recommendation
    assert final.timeline


def test_hinglish_scam_detected():
    pipe = AnalysisPipeline()
    a = pipe.analyze_text(HINGLISH_SCAM, call_id="call-hi")
    assert a.is_scam is True
    assert a.risk_score >= 50
    assert "hi-Latn" in a.languages or "hi" in a.languages


def test_legit_message_is_safe():
    pipe = AnalysisPipeline()
    a = pipe.analyze_text(LEGIT, call_id="call-legit")
    assert a.is_scam is False
    assert a.risk_score < 25
    assert a.band == RiskBand.SAFE


def test_scam_types_cover_categories():
    pipe = AnalysisPipeline()
    a = pipe.analyze_text("Your computer is infected, install anydesk so tech support can fix it.")
    assert any(t.category == "tech_support_scam" for t in a.scam_types)


def test_assessment_is_json_serialisable():
    pipe = AnalysisPipeline()
    a = pipe.analyze_text(HINGLISH_SCAM)
    blob = a.model_dump_json()
    assert '"risk_score"' in blob and '"signals"' in blob
