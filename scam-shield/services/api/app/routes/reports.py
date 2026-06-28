"""Downloadable incident reports (HTML always; PDF when reportlab present)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response

from scamshield_ai import RiskAssessment

from ..core.deps import Container, get_container, get_current_user
from ..domain.models import User
from ..services.report_service import render_html, render_pdf

router = APIRouter(prefix="/calls", tags=["reports"])


async def _load(call_id: str, container: Container, user: User):
    call = await container.repo.calls.get(call_id)
    if not call or call.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "call not found")
    if not call.last_assessment:
        raise HTTPException(status.HTTP_409_CONFLICT, "call has no assessment yet")
    return call, RiskAssessment.model_validate(call.last_assessment)


@router.get("/{call_id}/report.html", response_class=HTMLResponse)
async def report_html(call_id: str, container: Container = Depends(get_container),
                      user: User = Depends(get_current_user)):
    call, assessment = await _load(call_id, container, user)
    return HTMLResponse(render_html(assessment, call))


@router.get("/{call_id}/report.pdf")
async def report_pdf(call_id: str, container: Container = Depends(get_container),
                     user: User = Depends(get_current_user)):
    call, assessment = await _load(call_id, container, user)
    body, content_type = render_pdf(assessment, call)
    filename = f"scamshield_{call_id}.{'pdf' if 'pdf' in content_type else 'html'}"
    return Response(content=body, media_type=content_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
