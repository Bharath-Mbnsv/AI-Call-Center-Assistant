"""
Summarization Agent
--------------------
Generates a structured summary from a call transcript.
Model name + temperature come from config/mcp.yaml (backend.config).
On primary-model failure, transparently retries with the fallback model.
"""
import os
import json
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from backend.config import get_primary_model, get_fallback_model, get_model_temperature

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ── Pydantic output schema ───────────────────────────────────────────
class CallSummary(BaseModel):
    """Structured summary of a customer service call."""
    one_line_summary: str              # Single sentence overview
    customer_issue: str                # What the customer called about
    resolution: str                    # How it was resolved (or not)
    action_items: list[str]            # Follow-up tasks required
    key_topics: list[str]              # Main topics discussed
    sentiment: str                     # Customer sentiment: Positive / Neutral / Negative
    call_outcome: str                  # Resolved / Unresolved / Escalated / Follow-up Required
    error: Optional[str] = None


SYSTEM_PROMPT = """You are an expert call center analyst. 
Analyze the provided call transcript and return a JSON object with exactly these fields:

{
  "one_line_summary": "One sentence overview of the call",
  "customer_issue": "Clear description of why the customer called",
  "resolution": "How the issue was resolved, or why it wasn't",
  "action_items": ["list", "of", "follow-up", "tasks"],
  "key_topics": ["topic1", "topic2"],
  "sentiment": "Positive | Neutral | Negative",
  "call_outcome": "Resolved | Unresolved | Escalated | Follow-up Required"
}

Be factual and concise. Base everything strictly on the transcript — do not invent details.
Return ONLY valid JSON, no explanation, no markdown fences."""


def summarization_agent(transcript: str) -> CallSummary:
    """
    Generate a structured summary from a call transcript.

    Args:
        transcript: Full text of the call.

    Returns:
        CallSummary Pydantic model with structured fields.
    """
    if not transcript or len(transcript.strip()) < 20:
        return CallSummary(
            one_line_summary="No transcript available",
            customer_issue="N/A", resolution="N/A",
            action_items=[], key_topics=[],
            sentiment="Neutral", call_outcome="Unresolved",
            error="Transcript too short or missing."
        )

    temperature = get_model_temperature()
    models_to_try = [get_primary_model(), get_fallback_model()]
    last_error: Optional[Exception] = None

    for model_name in models_to_try:
        try:
            response = _client.chat.completions.create(
                model=model_name,
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Transcript:\n\n{transcript}"}
                ]
            )
            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)
            return CallSummary(**data)
        except json.JSONDecodeError as e:
            # Schema/parsing failures won't be fixed by retrying another model.
            return CallSummary(
                one_line_summary="Summary parsing failed",
                customer_issue="Parse error", resolution="N/A",
                action_items=[], key_topics=[],
                sentiment="Neutral", call_outcome="Unresolved",
                error=f"JSON parse error: {str(e)}"
            )
        except Exception as e:
            last_error = e
            continue  # API/model failure — try the fallback model

    return CallSummary(
        one_line_summary="Summarization failed",
        customer_issue="Error", resolution="N/A",
        action_items=[], key_topics=[],
        sentiment="Neutral", call_outcome="Unresolved",
        error=str(last_error) if last_error else "Unknown summarization error"
    )
