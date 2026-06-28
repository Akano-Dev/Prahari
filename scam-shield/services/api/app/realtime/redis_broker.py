"""Redis pub/sub broker — production fan-out across processes/pods.

Guarded import: ``redis.asyncio`` is only required when this broker is selected
(``REDIS_URL`` set). Same Protocol as :class:`MemoryBroker`.
"""
from __future__ import annotations

from typing import AsyncIterator


class RedisBroker:
    def __init__(self, redis_url: str):
        try:
            import redis.asyncio as redis  # lazy
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("redis not installed; `pip install redis` or unset REDIS_URL") from exc
        self._redis = redis.from_url(redis_url, decode_responses=True)

    async def publish(self, channel: str, message: str) -> None:
        await self._redis.publish(channel, message)

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for msg in pubsub.listen():
                if msg.get("type") == "message":
                    yield msg["data"]
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    async def close(self) -> None:
        await self._redis.aclose()
