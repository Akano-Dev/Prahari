"""Stage 6 — semantic similarity to known scam exemplars.

Compares each utterance to the exemplar bank in ``knowledge/scam_patterns.json``.
The default backend is a dependency-free token-overlap (Jaccard) similarity so the
stage runs anywhere; inject a Sentence-Transformers encoder for true semantic
matching in production (same interface, just a better ``similarity`` function).
"""
from __future__ import annotations

import json
import re
from importlib import resources

from ..context import ConversationState

_WORD = re.compile(r"\w+", re.UNICODE)


def _load_exemplars() -> list[dict]:
    data = json.loads(
        resources.files("scamshield_ai.knowledge").joinpath("scam_patterns.json").read_text("utf-8"))
    return data.get("exemplars", [])


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _WORD.findall(text)}


class SemanticSimilarityStage:
    """Token-overlap fallback; swap ``_similarity`` for embeddings in prod."""

    name = "semantic_similarity"

    def __init__(self, threshold: float = 0.18):
        self.threshold = threshold
        self.exemplars = _load_exemplars()
        self._exemplar_tokens = [(_tokens(e["text"]), e) for e in self.exemplars]

    def _similarity(self, a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def process(self, utterance: str, state: ConversationState) -> None:
        toks = _tokens(utterance)
        best = 0.0
        best_ex = None
        for ex_toks, ex in self._exemplar_tokens:
            sim = self._similarity(toks, ex_toks)
            if sim > best:
                best, best_ex = sim, ex
        if best_ex and best >= self.threshold:
            state.semantic_hits.append((best_ex["category"], round(best, 3)))
            # Nudge the matched scam type using the semantic evidence.
            cat = best_ex["category"]
            state.scam_type_scores[cat] = max(
                state.scam_type_scores.get(cat, 0.0), round(0.5 * best + 0.2, 4))
