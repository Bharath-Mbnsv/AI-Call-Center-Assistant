"""
Call Intake Agent
-----------------
Validates incoming call data (audio file or text transcript)
and extracts metadata like call ID, duration, and input type.
"""
import os
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, field_validator
from typing import Optional

from backend.utils.validation import SUPPORTED_AUDIO


class CallMetadata(BaseModel):
    """Structured metadata extracted from a call input."""
    call_id: str
    input_type: str          # "audio" or "transcript"
    timestamp: str
    filename: Optional[str] = None
    duration_estimate: Optional[str] = None
    char_count: Optional[int] = None
    valid: bool = True
    error: Optional[str] = None

    @field_validator("input_type")
    @classmethod
    def validate_input_type(cls, v):
        if v not in ("audio", "transcript"):
            raise ValueError("input_type must be 'audio' or 'transcript'")
        return v


SUPPORTED_TEXT = {".txt", ".json"}


def intake_agent(input_data: str | bytes, filename: str = "") -> CallMetadata:
    """
    Validate and extract metadata from call input.

    Args:
        input_data: Either a text transcript (str) or raw audio bytes.
        filename:   Original filename (used to detect type).

    Returns:
        CallMetadata with validation result and extracted fields.
    """
    call_id   = f"CALL-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6]}"
    timestamp = datetime.now().isoformat()
    ext       = os.path.splitext(filename)[1].lower()

    # ── Detect input type ───────────────────────────────────────────
    if isinstance(input_data, bytes):
        if ext not in SUPPORTED_AUDIO:
            return CallMetadata(
                call_id=call_id, input_type="audio", timestamp=timestamp,
                filename=filename, valid=False,
                error=f"Unsupported audio format '{ext}'. Supported: {SUPPORTED_AUDIO}"
            )
        # Rough duration estimate: ~1 min per 1MB for typical call audio
        size_mb = len(input_data) / (1024 * 1024)
        duration = f"~{max(1, int(size_mb))} min (estimated)"
        return CallMetadata(
            call_id=call_id, input_type="audio", timestamp=timestamp,
            filename=filename, duration_estimate=duration, valid=True
        )

    elif isinstance(input_data, str):
        if not input_data.strip():
            return CallMetadata(
                call_id=call_id, input_type="transcript", timestamp=timestamp,
                filename=filename, valid=False,
                error="Transcript is empty. Please provide call content."
            )
        if len(input_data.strip()) < 50:
            return CallMetadata(
                call_id=call_id, input_type="transcript", timestamp=timestamp,
                filename=filename, valid=False,
                error="Transcript too short (< 50 characters). Please provide a full transcript."
            )
        return CallMetadata(
            call_id=call_id, input_type="transcript", timestamp=timestamp,
            filename=filename, char_count=len(input_data),
            duration_estimate=f"~{max(1, len(input_data.split()) // 150)} min (estimated)",
            valid=True
        )

    return CallMetadata(
        call_id=call_id, input_type="transcript", timestamp=timestamp,
        valid=False, error="Unknown input type."
    )
