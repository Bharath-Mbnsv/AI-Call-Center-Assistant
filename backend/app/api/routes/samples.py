"""Sample transcript routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.api.schemas import SampleItem, SampleTranscriptResponse
from backend.app.services.analysis_service import get_sample_transcript, list_sample_transcripts

router = APIRouter(prefix="/api/samples", tags=["samples"])


@router.get("", response_model=list[SampleItem])
def sample_list_endpoint() -> list[SampleItem]:
    return [SampleItem(**item) for item in list_sample_transcripts()]


@router.get("/{slug}", response_model=SampleTranscriptResponse)
def sample_detail_endpoint(slug: str) -> SampleTranscriptResponse:
    try:
        result = get_sample_transcript(slug)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return SampleTranscriptResponse(**result)
