"""Pydantic schemas for the call center API."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyzeTextRequest(BaseModel):
    transcript: str = Field(min_length=1)
    filename: str = "transcript.txt"


class AnalyzeJsonRequest(BaseModel):
    payload: dict[str, Any] | list[dict[str, Any]]
    filename: str = "transcript.json"


class AnalyzeResponse(BaseModel):
    metadata: dict[str, Any] | None = None
    transcript: str | None = None
    summary: dict[str, Any] | None = None
    qa_score: dict[str, Any] | None = None
    current_stage: str
    errors: list[str] = Field(default_factory=list)
    fallback_used: bool = False


class SampleItem(BaseModel):
    slug: str
    label: str


class SampleTranscriptResponse(BaseModel):
    slug: str
    label: str
    transcript: str


class ApiStatus(BaseModel):
    status: Literal["ok"]
