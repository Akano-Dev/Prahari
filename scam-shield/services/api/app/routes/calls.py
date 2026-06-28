"""Call lifecycle + stats routes (auth-protected)."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.deps import Container, get_analysis, get_container, get_current_user
from ..domain.models import Call, CallStatus, User
from ..schemas.api import (
    CallResponse,
    CreateCallRequest,
    IncidentResponse,
    StatsResponse,
    UtteranceRequest,
)
from ..services.analysis_service import AnalysisService

router = APIRouter(prefix="/calls", tags=["calls"])


def _to_response(call: Call) -> CallResponse:
    return CallResponse(
        id=call.id, caller_number=call.caller_number, contact_name=call.contact_name,
        is_known_contact=call.is_known_contact, status=call.status.value,
        peak_risk=call.peak_risk, n_utterances=len(call.utterances),
        last_assessment=call.last_assessment,
    )


async def _owned_call(call_id: str, container: Container, user: User) -> Call:
    call = await container.repo.calls.get(call_id)
    if not call or call.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "call not found")
    return call


@router.post("", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def create_call(req: CreateCallRequest, container: Container = Depends(get_container),
                      user: User = Depends(get_current_user)):
    call = Call(owner_id=user.id, caller_number=req.caller_number,
                contact_name=req.contact_name, is_known_contact=req.is_known_contact)
    await container.repo.calls.add(call)
    return _to_response(call)


@router.get("", response_model=list[CallResponse])
async def list_calls(container: Container = Depends(get_container),
                     user: User = Depends(get_current_user)):
    return [_to_response(c) for c in await container.repo.calls.list_for_owner(user.id)]


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(call_id: str, container: Container = Depends(get_container),
                   user: User = Depends(get_current_user)):
    return _to_response(await _owned_call(call_id, container, user))


@router.post("/{call_id}/utterance")
async def push_utterance(call_id: str, req: UtteranceRequest,
                         container: Container = Depends(get_container),
                         analysis: AnalysisService = Depends(get_analysis),
                         user: User = Depends(get_current_user)):
    """HTTP fallback for the WS stream (useful for testing / non-WS clients)."""
    call = await _owned_call(call_id, container, user)
    assessment = await analysis.ingest_utterance(call, req.text)
    return assessment.model_dump(mode="json")


@router.post("/{call_id}/end", response_model=CallResponse)
async def end_call(call_id: str, container: Container = Depends(get_container),
                   analysis: AnalysisService = Depends(get_analysis),
                   user: User = Depends(get_current_user)):
    call = await _owned_call(call_id, container, user)
    call.status = CallStatus.ENDED
    call.ended_at = datetime.now(timezone.utc)
    await container.repo.calls.update(call)
    analysis.drop_state(call.id)
    return _to_response(call)


@router.get("/{call_id}/incidents", response_model=list[IncidentResponse])
async def call_incidents(call_id: str, container: Container = Depends(get_container),
                         user: User = Depends(get_current_user)):
    await _owned_call(call_id, container, user)
    items = await container.repo.incidents.list_for_owner(user.id)
    return [IncidentResponse(id=i.id, call_id=i.call_id, risk_score=i.risk_score,
                             scam_type=i.scam_type, caller_number=i.caller_number,
                             created_at=i.created_at.isoformat())
            for i in items if i.call_id == call_id]


# Mounted at the app level too (see main) for the dashboard's overview panels.
stats_router = APIRouter(tags=["stats"])


@stats_router.get("/incidents", response_model=list[IncidentResponse])
async def list_incidents(container: Container = Depends(get_container),
                         user: User = Depends(get_current_user)):
    items = await container.repo.incidents.list_for_owner(user.id)
    return [IncidentResponse(id=i.id, call_id=i.call_id, risk_score=i.risk_score,
                             scam_type=i.scam_type, caller_number=i.caller_number,
                             created_at=i.created_at.isoformat()) for i in items]


@stats_router.get("/stats", response_model=StatsResponse)
async def stats(container: Container = Depends(get_container),
                user: User = Depends(get_current_user)):
    calls = await container.repo.calls.list_for_owner(user.id, limit=1000)
    incidents = await container.repo.incidents.list_for_owner(user.id, limit=1000)
    scam_calls = sum(1 for c in calls if c.peak_risk >= 50)
    avg_peak = round(sum(c.peak_risk for c in calls) / len(calls), 1) if calls else 0.0
    by_type = Counter(i.scam_type or "unknown" for i in incidents)
    return StatsResponse(total_calls=len(calls), total_incidents=len(incidents),
                         scam_calls=scam_calls, avg_peak_risk=avg_peak,
                         by_scam_type=dict(by_type))
