"""One-shot analysis routes for uploaded content.

Covers the Android app's non-live inputs: SMS scanning, screenshot upload (text
already OCR'd client- or server-side), WhatsApp chat export, and voice-recording
transcripts. All share the same hybrid pipeline and the same explainable schema.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.deps import get_analysis, get_current_user
from ..domain.models import User
from ..schemas.api import AnalyzeBlockRequest
from ..services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("")
async def analyze_block(req: AnalyzeBlockRequest,
                        analysis: AnalysisService = Depends(get_analysis),
                        user: User = Depends(get_current_user)):
    assessment = await analysis.analyze_block(req.text, call_id=f"{req.source}:{user.id}")
    return assessment.model_dump(mode="json")
