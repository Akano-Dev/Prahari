"""Provider-agnostic LLM interface for the reasoning stage.

The LLM **only explains** — it never decides risk (see ARCHITECTURE.md §2). The
default :class:`DeterministicStubProvider` produces a solid, reproducible
explanation from the deterministic signals with **no external calls**, so the
engine runs with no API keys. Real providers (Claude/OpenAI/Gemini) implement the
same :class:`LLMProvider` protocol and are injected only when configured.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def reason(self, prompt: str, context: dict) -> str:
        """Return a short natural-language explanation of the scam assessment."""
        ...


class DeterministicStubProvider:
    """Default provider: templated, reproducible reasoning, zero network calls."""

    name = "deterministic-stub"

    def reason(self, prompt: str, context: dict) -> str:
        score = context.get("risk_score", 0)
        top = context.get("top_scam_type")
        signals = context.get("signals", [])
        behaviours = context.get("behaviours", [])

        if score >= 75:
            head = "This call shows the fingerprint of a scam."
        elif score >= 50:
            head = "This call shows several strong scam indicators."
        elif score >= 25:
            head = "This call shows some suspicious indicators; stay cautious."
        else:
            head = "No strong scam indicators were detected so far."

        parts = [head]
        if top:
            parts.append(f"The pattern most closely matches a {top} scam.")
        if signals:
            named = ", ".join(signals[:4])
            parts.append(f"Triggered red flags: {named}.")
        if behaviours:
            parts.append("Manipulation tactics observed: " + ", ".join(behaviours[:4]) + ".")
        parts.append(
            "Decision basis is the deterministic rule, pattern and behaviour "
            "signals; this explanation is advisory only."
        )
        return " ".join(parts)
