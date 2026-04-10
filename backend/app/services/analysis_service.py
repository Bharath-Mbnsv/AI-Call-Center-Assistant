"""Backend service helpers that wrap the existing call center pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "backend" / "data"
SAMPLE_TRANSCRIPTS_DIR = DATA_DIR / "sample_transcripts"

from backend.agents.routing_agent import run_pipeline
from backend.utils.validation import clean_transcript, validate_json_transcript, validate_transcript_text


def analyze_transcript_text(transcript: str, filename: str = "transcript.txt") -> dict[str, Any]:
    cleaned = clean_transcript(transcript)
    ok, message = validate_transcript_text(cleaned)
    if not ok:
        raise ValueError(message)
    return run_pipeline(cleaned, filename)


def analyze_transcript_json(payload: dict[str, Any] | list[dict[str, Any]], filename: str = "transcript.json") -> dict[str, Any]:
    ok, message, transcript = validate_json_transcript(json.dumps(payload))
    if not ok:
        raise ValueError(message)
    return analyze_transcript_text(transcript, filename)


def analyze_audio_bytes(audio_bytes: bytes, filename: str) -> dict[str, Any]:
    if not audio_bytes:
        raise ValueError("Audio file is empty.")
    return run_pipeline(audio_bytes, filename or "call_audio.mp3")


def list_sample_transcripts() -> list[dict[str, str]]:
    if not SAMPLE_TRANSCRIPTS_DIR.exists():
        return []

    items: list[dict[str, str]] = []
    for path in sorted(SAMPLE_TRANSCRIPTS_DIR.glob("*.txt")):
        items.append({
            "slug": path.stem,
            "label": path.stem.replace("_", " ").title(),
        })
    return items


def get_sample_transcript(slug: str) -> dict[str, str]:
    path = SAMPLE_TRANSCRIPTS_DIR / f"{slug}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Sample transcript '{slug}' was not found.")
    return {
        "slug": slug,
        "label": slug.replace("_", " ").title(),
        "transcript": path.read_text(encoding="utf-8"),
    }
