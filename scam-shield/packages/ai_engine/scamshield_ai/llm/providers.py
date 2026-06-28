"""Concrete LLM provider adapters (explanation only; opt-in at deploy time).

Each adapter implements :class:`~scamshield_ai.llm.base.LLMProvider`. The LLM
**only phrases** the explanation — the deterministic stages already decided the
risk (see ARCHITECTURE.md §2), so a provider can never change a verdict.

Adapters lazy-import their SDK and **degrade gracefully**: with no API key, no
network, an SDK error, or a model refusal, they fall back to the deterministic
stub so detection never breaks. Selection is via configuration; until a real
provider is configured *with credentials*, the engine uses the stub.
"""
from __future__ import annotations

import os

from .base import DeterministicStubProvider

_SYSTEM = (
    "You are a defensive fraud-analysis assistant for an anti-scam tool. You are "
    "given deterministic scam signals already extracted from a call transcript. "
    "Explain in 2-3 short, plain sentences why the call is or isn't a scam and what "
    "the person should do. Explain only — never invent facts, never state a numeric "
    "score, and never tell the user to comply with the caller."
)

_DEFAULT_CLAUDE_MODEL = "claude-opus-4-8"
_DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class ClaudeProvider:
    """Anthropic Claude adapter (the real LLM-reasoning provider).

    Requires the optional ``anthropic`` SDK and an API key. Falls back to the
    deterministic stub on any problem, so it is always safe to select.
    """

    name = "claude"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model = model or os.environ.get("SCAMSHIELD_LLM_MODEL") or _DEFAULT_CLAUDE_MODEL
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or None
        self._fallback = DeterministicStubProvider()
        self._client = None

    @property
    def available(self) -> bool:
        """True only when a key is present — lets the container avoid selecting
        a real provider that would just fall back on every call."""
        return bool(self._api_key)

    def _client_or_none(self):
        if self._client is None:
            import anthropic  # lazy: only needed when this provider actually runs
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def reason(self, prompt: str, context: dict) -> str:
        if not self._api_key:
            return self._fallback.reason(prompt, context)
        try:
            # No temperature / top_p / thinking params — they are rejected on
            # claude-opus-4-8 and the explanation is short, so adaptive thinking
            # is unnecessary. Keep max_tokens small for a 2-3 sentence answer.
            msg = self._client_or_none().messages.create(
                model=self.model, max_tokens=320, system=_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            if getattr(msg, "stop_reason", None) == "refusal":
                return self._fallback.reason(prompt, context)
            text = "".join(
                b.text for b in msg.content if getattr(b, "type", "") == "text"
            ).strip()
            return text or self._fallback.reason(prompt, context)
        except Exception:
            # Auth/network/SDK error → deterministic explanation; never break detection.
            return self._fallback.reason(prompt, context)


class OpenAIProvider:
    """OpenAI adapter. Requires the optional ``openai`` SDK + an API key."""

    name = "openai"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model = model or os.environ.get("SCAMSHIELD_LLM_MODEL") or _DEFAULT_OPENAI_MODEL
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY") or None
        self._fallback = DeterministicStubProvider()

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def reason(self, prompt: str, context: dict) -> str:
        if not self._api_key:
            return self._fallback.reason(prompt, context)
        try:
            from openai import OpenAI  # lazy
            client = OpenAI(api_key=self._api_key)
            resp = client.chat.completions.create(
                model=self.model, max_tokens=320,
                messages=[{"role": "system", "content": _SYSTEM},
                          {"role": "user", "content": prompt}],
            )
            return (resp.choices[0].message.content or "").strip() or self._fallback.reason(prompt, context)
        except Exception:
            return self._fallback.reason(prompt, context)


# Registry so configuration can select a provider by name.
PROVIDERS = {
    "deterministic-stub": DeterministicStubProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}


def get_provider(name: str = "deterministic-stub", **kwargs):
    """Instantiate a provider by name; defaults to the no-network stub.

    Extra kwargs (``model``, ``api_key``) are forwarded to real providers; the
    stub takes none, so a ``TypeError`` there falls back to a bare construction.
    """
    factory = PROVIDERS.get(name, DeterministicStubProvider)
    try:
        return factory(**kwargs) if kwargs else factory()
    except TypeError:
        return factory()
