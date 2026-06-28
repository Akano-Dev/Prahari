"""In-process pub/sub broker (asyncio), the zero-dependency default.

Each subscriber gets its own ``asyncio.Queue``; ``publish`` fans a message out to
every queue on the channel. Good for a single API process (and all tests).
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import AsyncIterator


class MemoryBroker:
    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)

    async def publish(self, channel: str, message: str) -> None:
        for q in list(self._subs.get(channel, ())):
            q.put_nowait(message)

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        q: asyncio.Queue[str] = asyncio.Queue()
        self._subs[channel].add(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subs[channel].discard(q)

    async def close(self) -> None:
        self._subs.clear()
