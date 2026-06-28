"""LLM-reasoning stage: the LLM explains but never decides, and degrades safely.

These tests make NO network calls — the Claude path is exercised via a key-less
provider and a monkeypatched client, so they run in CI with no API key.
"""
from __future__ import annotations

from scamshield_ai import AnalysisPipeline
from scamshield_ai.llm import DeterministicStubProvider, get_provider
from scamshield_ai.llm.providers import ClaudeProvider

SCAM = ("This is the CBI. You are under digital arrest. Transfer Rs 50,000 to the "
        "safe account and share the OTP immediately or face arrest.")


def test_default_provider_is_the_stub_and_deterministic():
    p = get_provider()
    assert p.name == "deterministic-stub"
    ctx = {"risk_score": 80, "top_scam_type": "Digital Arrest", "signals": ["x"], "behaviours": []}
    assert p.reason("p", ctx) == p.reason("p", ctx)  # reproducible, no network


def test_claude_provider_without_key_falls_back_to_stub():
    p = ClaudeProvider(api_key="")               # no key
    assert p.available is False
    ctx = {"risk_score": 80, "top_scam_type": "Digital Arrest", "signals": [], "behaviours": []}
    # Identical to the stub's output — and made no network call.
    assert p.reason("prompt", ctx) == DeterministicStubProvider().reason("prompt", ctx)


def test_claude_provider_falls_back_on_sdk_error(monkeypatch):
    p = ClaudeProvider(api_key="sk-test-not-real")
    assert p.available is True
    monkeypatch.setattr(p, "_client_or_none", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    ctx = {"risk_score": 80, "top_scam_type": "Digital Arrest", "signals": [], "behaviours": []}
    assert p.reason("prompt", ctx) == DeterministicStubProvider().reason("prompt", ctx)


def test_llm_cannot_change_the_verdict():
    """A provider returning wildly different prose must not move the score."""
    class LoudProvider:
        name = "loud"
        def reason(self, prompt, context):
            return "TOTALLY DIFFERENT EXPLANATION that mentions nothing real."

    stub_pipe = AnalysisPipeline()                       # deterministic stub
    loud_pipe = AnalysisPipeline(llm_provider=LoudProvider())

    a = stub_pipe.analyze_text(SCAM)
    b = loud_pipe.analyze_text(SCAM)

    assert a.risk_score == b.risk_score                  # verdict identical
    assert a.is_scam == b.is_scam is True
    assert a.reasoning != b.reasoning                    # only the wording differs
    assert b.reasoning.startswith("TOTALLY DIFFERENT")
