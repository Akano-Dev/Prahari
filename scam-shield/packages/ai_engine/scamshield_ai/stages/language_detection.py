"""Stage 1 — language detection (English / Hindi / Hinglish).

Light, dependency-free heuristic: Devanagari code points ⇒ Hindi; a lexicon of
common romanized-Hindi tokens ⇒ Hinglish; else English. An optional
``langdetect`` adapter can be injected for broader coverage, but the heuristic is
enough to tag the transcript and is fully deterministic.
"""
from __future__ import annotations

import re

from ..context import ConversationState

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_HINGLISH = re.compile(
    r"\b(?:aap|hai|hain|karo|kar|bhej|paise|paisa|mat|nahi|kisi|ko|mein|"
    r"turant|warna|giraftari|bhejo|batao|raho|jaldi|abhi)\b", re.IGNORECASE)


class LanguageDetectionStage:
    name = "language_detection"

    def process(self, utterance: str, state: ConversationState) -> None:
        lang = self._detect(utterance)
        state.languages.add(lang)

    @staticmethod
    def _detect(text: str) -> str:
        if _DEVANAGARI.search(text):
            return "hi"
        if _HINGLISH.search(text):
            return "hi-Latn"  # Hinglish
        return "en"
