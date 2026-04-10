"""
Transcription Agent
-------------------
Converts audio bytes to text using OpenAI Whisper.
Model name is read from config/mcp.yaml (backend.config).
If audio is unavailable or fails, falls back gracefully.
"""
import os
import tempfile
from openai import OpenAI
from dotenv import load_dotenv

from backend.config import get_transcription_model

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcription_agent(audio_bytes: bytes, filename: str = "audio.mp3") -> dict:
    """
    Transcribe audio to text using OpenAI Whisper.

    Args:
        audio_bytes: Raw audio file content.
        filename:    Original filename (Whisper uses extension to detect format).

    Returns:
        dict with keys: transcript (str), success (bool), error (str|None)
    """
    if not audio_bytes:
        return {
            "transcript": None,
            "success": False,
            "error": "No audio data provided."
        }

    ext = os.path.splitext(filename)[1] or ".mp3"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            response = _client.audio.transcriptions.create(
                model=get_transcription_model(),
                file=f,
                response_format="text"
            )

        transcript = response if isinstance(response, str) else response.text
        return {
            "transcript": transcript.strip(),
            "success": True,
            "error": None
        }

    except Exception as e:
        return {
            "transcript": None,
            "success": False,
            "error": f"Transcription failed: {str(e)}"
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
