"""Realtime message broker interface.

The Android WS pushes transcripts; the API analyses and **publishes** assessments
to a channel; dashboards **subscribe** to that channel for live fan-out. The
default :class:`MemoryBroker` works in a single process; :class:`RedisBroker`
scales across processes/pods. Routes depend only on this Protocol.
"""
from __future__ import annotations

from typing import AsyncIterator, Protocol


class Broker(Protocol):
    async def publish(self, channel: str, message: str) -> None: ...
    def subscribe(self, channel: str) -> AsyncIterator[str]: ...
    async def close(self) -> None: ...
