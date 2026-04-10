"""Analysis routes for transcripts and audio."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.api.schemas import AnalyzeJsonRequest, AnalyzeResponse, AnalyzeTextRequest
from backend.app.services.analysis_service import analyze_audio_bytes, analyze_transcript_json, analyze_transcript_text

router = APIRouter(prefix="/api/analyze", tags=["analysis"])


@router.post("/text", response_model=AnalyzeResponse)
def analyze_text_endpoint(request: AnalyzeTextRequest) -> AnalyzeResponse:
    try:
        result = analyze_transcript_text(request.transcript, request.filename)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AnalyzeResponse(**result)


@router.post("/json", response_model=AnalyzeResponse)
def analyze_json_endpoint(request: AnalyzeJsonRequest) -> AnalyzeResponse:
    try:
        result = analyze_transcript_json(request.payload, request.filename)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AnalyzeResponse(**result)


@router.post("/audio", response_model=AnalyzeResponse)
async def analyze_audio_endpoint(file: UploadFile = File(...)) -> AnalyzeResponse:
    try:
        contents = await file.read()
    except Exception as error:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.") from error

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            None, analyze_audio_bytes, contents, file.filename or "call_audio.mp3"
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AnalyzeResponse(**result)
