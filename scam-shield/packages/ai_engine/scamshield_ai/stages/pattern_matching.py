"""Stage 5 — scam-type pattern matching.

Scores every registered :class:`ScamCategory` against the full conversation so
far and keeps a running max strength per category. The strongest become the
"detected scam type(s)" in the assessment. Categories are data (see
``categories.py``), so this stage never changes when new scam types are added.
"""
from __future__ import annotations

from ..categories import CATEGORIES
from ..context import ConversationState


class PatternMatchingStage:
    name = "pattern_matching"

    def process(self, utterance: str, state: ConversationState) -> None:
        text = state.full_text  # match over the whole call, not one sentence
        for cat in CATEGORIES:
            strength = cat.match_strength(text)
            if strength <= 0:
                continue
            prev = state.scam_type_scores.get(cat.id, 0.0)
            score = max(prev, round(strength * cat.weight, 4))
            if score > prev:
                state.scam_type_scores[cat.id] = score
                if prev == 0.0:
                    state.add_timeline("note", f"scam type candidate: {cat.label}")
