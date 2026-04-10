"""
Validation utilities for call input preprocessing.
"""
import os
import json

SUPPORTED_AUDIO = {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg"}
MAX_TRANSCRIPT_CHARS = 50_000   # ~30 min of speech


def validate_file_extension(filename: str) -> tuple[bool, str]:
    """Check if file extension is supported. Returns (is_valid, message)."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in SUPPORTED_AUDIO:
        return True, f"Valid audio file: {ext}"
    if ext in {".txt", ".json"}:
        return True, f"Valid transcript file: {ext}"
    return False, f"Unsupported file type: '{ext}'"


def validate_transcript_text(text: str) -> tuple[bool, str]:
    """Validate a plain text transcript."""
    if not text or not text.strip():
        return False, "Transcript is empty."
    if len(text.strip()) < 50:
        return False, "Transcript too short (< 50 chars)."
    if len(text) > MAX_TRANSCRIPT_CHARS:
        return False, f"Transcript too long (> {MAX_TRANSCRIPT_CHARS} chars). Please trim."
    return True, "Valid transcript."


def validate_json_transcript(json_text: str) -> tuple[bool, str, str]:
    """
    Validate and extract text from a JSON transcript.
    Expected format: {"transcript": "..."} or [{"speaker": "...", "text": "..."}]
    Returns (is_valid, message, extracted_text).
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}", ""

    # Format 1: {"transcript": "full text"}
    if isinstance(data, dict) and "transcript" in data:
        transcript = data["transcript"]
        if not isinstance(transcript, str):
            return False, "JSON field 'transcript' must be a string.", ""
        return True, "Valid JSON transcript.", transcript

    # Format 2: [{"speaker": "Agent", "text": "Hello..."}, ...]
    if isinstance(data, list):
        lines = []
        for item in data:
            if not isinstance(item, dict):
                return False, "Each transcript entry must be an object with speaker/text fields.", ""
            speaker = item.get("speaker", "Speaker")
            text = item.get("text", item.get("content", ""))
            if text:
                lines.append(f"{speaker}: {text}")
        if lines:
            return True, "Valid JSON transcript (speaker format).", "\n".join(lines)

    return False, "JSON format not recognized. Use {'transcript': '...'} or [{speaker, text}]", ""


def clean_transcript(text: str) -> str:
    """Remove excessive whitespace and normalize line endings."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)
