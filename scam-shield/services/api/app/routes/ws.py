"""WebSocket endpoints — the live spine of ScamShield.

* ``/ws/calls/{call_id}``  — the Android app streams transcript chunks as JSON
  ``{"text": "..."}``; the server analyses each, replies with the explainable
  assessment, and publishes it to the broker for dashboards.
* ``/ws/dashboard``        — a dashboard subscribes to the owner's channel and
  receives every assessment in real time.

Auth: a JWT is passed as the ``token`` query parameter (browsers/clients can't set
WebSocket headers reliably). The token is decoded to the owning user before any
data flows.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..core.config import get_settings
from ..core.deps import Container
from ..core.security import TokenError, decode_access_token
from ..domain.models import User

router = APIRouter(tags=["realtime"])


async def _authenticate(websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token", "")
    settings = get_settings()
    container: Container = websocket.app.state.container
    try:
        payload = decode_access_token(token, settings.jwt_secret)
    except TokenError:
        return None
    return await container.repo.users.get(payload.get("sub", ""))


@router.websocket("/ws/calls/{call_id}")
async def ws_call(websocket: WebSocket, call_id: str):
    user = await _authenticate(websocket)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    container: Container = websocket.app.state.container
    call = await container.repo.calls.get(call_id)
    if not call or call.owner_id != user.id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                text = json.loads(raw).get("text", "") if raw.strip().startswith("{") else raw
            except json.JSONDecodeError:
                text = raw
            if not text.strip():
                continue
            # Re-fetch the call so persisted utterances/peak stay consistent.
            call = await container.repo.calls.get(call_id) or call
            assessment = await container.analysis.ingest_utterance(call, text)
            await websocket.send_text(assessment.model_dump_json())
    except WebSocketDisconnect:
        return


@router.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    user = await _authenticate(websocket)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    container: Container = websocket.app.state.container
    await websocket.accept()
    channel = f"owner:{user.id}"
    try:
        async for message in container.broker.subscribe(channel):
            await websocket.send_text(message)
    except WebSocketDisconnect:
        return
