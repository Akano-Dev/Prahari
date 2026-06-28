"""Provider-agnostic LLM reasoning (explanation only; off by default)."""
from .base import DeterministicStubProvider, LLMProvider
from .providers import get_provider

__all__ = ["LLMProvider", "DeterministicStubProvider", "get_provider"]
