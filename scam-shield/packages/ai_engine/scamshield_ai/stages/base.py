"""The Stage protocol — the unit of the hybrid pipeline.

Each stage receives the latest utterance and the rolling
:class:`~scamshield_ai.context.ConversationState`, and mutates the state in
place (adds signals, entities, behaviour intensities, scam-type scores, timeline
notes…). Stages are dependency-injected into the pipeline, so heavy ones can be
swapped for real-model adapters without touching the orchestrator.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..context import ConversationState


@runtime_checkable
class Stage(Protocol):
    name: str

    def process(self, utterance: str, state: ConversationState) -> None:
        ...
