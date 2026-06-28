"""Stage 7 — knowledge-base lookup.

Turns the strongest detected scam type into a concrete, citable advisory from the
knowledge base, and surfaces the universal "red lines" that a real official never
crosses. These notes feed the recommendation and the LLM reasoning prompt.
"""
from __future__ import annotations

import json
from importlib import resources

from ..context import ConversationState


def _load(name: str) -> dict:
    return json.loads(
        resources.files("scamshield_ai.knowledge").joinpath(name).read_text("utf-8"))


class KnowledgeBaseStage:
    name = "knowledge_base"

    def __init__(self):
        patterns = _load("scam_patterns.json")
        self._advisory = {e["category"]: e["advisory"] for e in patterns.get("exemplars", [])}
        self._red_lines = _load("agencies.json").get("universal_red_lines", [])

    def process(self, utterance: str, state: ConversationState) -> None:
        if not state.scam_type_scores:
            return
        top = max(state.scam_type_scores, key=state.scam_type_scores.get)
        advisory = self._advisory.get(top)
        if advisory and advisory not in state.kb_notes:
            state.kb_notes.append(advisory)
        # Once authority + a coercion behaviour appear, attach a red-line note.
        if state.behaviour.get("authority_impersonation", 0) >= 0.5 and self._red_lines:
            note = self._red_lines[0]
            if note not in state.kb_notes:
                state.kb_notes.append(note)
