"""WebSocket ingest + broker fan-out tests."""
from __future__ import annotations

import anyio
import pytest

from app.realtime.memory_broker import MemoryBroker


def test_call_ws_round_trip(client, auth):
    headers, token = auth
    call_id = client.post("/calls", json={}, headers=headers).json()["id"]

    sentences = [
        "This is the CBI cyber crime branch.",
        "You are under digital arrest, do not disconnect.",
        "Transfer Rs 50,000 to the safe account and share the OTP.",
    ]
    scores = []
    with client.websocket_connect(f"/ws/calls/{call_id}?token={token}") as ws:
        for s in sentences:
            ws.send_json({"text": s})
            scores.append(ws.receive_json()["risk_score"])

    assert scores == sorted(scores)
    assert scores[-1] >= 75


def test_ws_rejects_bad_token(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/calls/whatever?token=bad") as ws:
            ws.receive_json()


def test_memory_broker_pub_sub():
    async def scenario():
        broker = MemoryBroker()
        received: list[str] = []

        async def subscriber():
            async for msg in broker.subscribe("owner:1"):
                received.append(msg)
                break

        async with anyio.create_task_group() as tg:
            tg.start_soon(subscriber)
            await anyio.sleep(0.05)          # let the subscriber register
            await broker.publish("owner:1", "hello")

        assert received == ["hello"]

    anyio.run(scenario)
