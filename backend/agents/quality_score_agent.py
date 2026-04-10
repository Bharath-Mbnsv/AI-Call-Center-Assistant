"""
Quality Scoring Agent
----------------------
Evaluates call quality using OpenAI function calling.
Scores: Empathy, Professionalism, Resolution, Communication, Overall.
Each score is 1–10 with justification.

Model name comes from config/mcp.yaml (backend.config). On primary-model
failure the agent transparently retries with the fallback model.
"""
import os
import json
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from backend.config import get_primary_model, get_fallback_model

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ── Pydantic schema for QA scores ────────────────────────────────────
class DimensionScore(BaseModel):
    score: Optional[int] = None  # 1-10 when available
    justification: str  # One sentence reason


class QAScore(BaseModel):
    """Full quality assessment of a customer service call."""
    empathy: DimensionScore
    professionalism: DimensionScore
    resolution: DimensionScore
    communication_clarity: DimensionScore
    overall_score: Optional[int] = None  # 1-10 weighted average when available
    grade: Optional[str] = None          # Excellent / Good / Needs Improvement / Poor
    highlights: list[str]       # What was done well
    improvements: list[str]     # What could be better
    error: Optional[str] = None


# ── Function schema for function calling ─────────────────────────────
QA_FUNCTION = {
    "name": "evaluate_call_quality",
    "description": "Score a customer service call on multiple quality dimensions",
    "parameters": {
        "type": "object",
        "properties": {
            "empathy": {
                "type": "object",
                "properties": {
                    "score": {"type": "integer", "minimum": 1, "maximum": 10},
                    "justification": {"type": "string"}
                },
                "required": ["score", "justification"]
            },
            "professionalism": {
                "type": "object",
                "properties": {
                    "score": {"type": "integer", "minimum": 1, "maximum": 10},
                    "justification": {"type": "string"}
                },
                "required": ["score", "justification"]
            },
            "resolution": {
                "type": "object",
                "properties": {
                    "score": {"type": "integer", "minimum": 1, "maximum": 10},
                    "justification": {"type": "string"}
                },
                "required": ["score", "justification"]
            },
            "communication_clarity": {
                "type": "object",
                "properties": {
                    "score": {"type": "integer", "minimum": 1, "maximum": 10},
                    "justification": {"type": "string"}
                },
                "required": ["score", "justification"]
            },
            "overall_score": {"type": "integer", "minimum": 1, "maximum": 10},
            "grade": {
                "type": "string",
                "enum": ["Excellent", "Good", "Needs Improvement", "Poor"]
            },
            "highlights": {
                "type": "array", "items": {"type": "string"}
            },
            "improvements": {
                "type": "array", "items": {"type": "string"}
            }
        },
        "required": [
            "empathy", "professionalism", "resolution",
            "communication_clarity", "overall_score", "grade",
            "highlights", "improvements"
        ]
    }
}

SYSTEM_PROMPT = """You are a call center quality assurance specialist.
Evaluate the call transcript using this rubric:

EMPATHY (1-10): Did the agent acknowledge customer feelings? Show understanding?
PROFESSIONALISM (1-10): Was the agent polite, patient, and professional throughout?
RESOLUTION (1-10): Was the customer's issue actually resolved? Efficiently?
COMMUNICATION CLARITY (1-10): Were explanations clear, simple, and easy to follow?

Scoring guide:
9-10: Exceptional  |  7-8: Good  |  5-6: Average  |  3-4: Below average  |  1-2: Poor

Be strict but fair. Base scoring strictly on the transcript evidence."""


def quality_score_agent(transcript: str) -> QAScore:
    """
    Score a call transcript using GPT function calling.

    Args:
        transcript: Full call text.

    Returns:
        QAScore Pydantic model with dimension scores and feedback.
    """
    if not transcript or len(transcript.strip()) < 20:
        return QAScore(
            empathy=DimensionScore(justification="No transcript"),
            professionalism=DimensionScore(justification="No transcript"),
            resolution=DimensionScore(justification="No transcript"),
            communication_clarity=DimensionScore(justification="No transcript"),
            highlights=[], improvements=[],
            error="Transcript missing or too short."
        )

    models_to_try = [get_primary_model(), get_fallback_model()]
    last_error: Optional[Exception] = None

    for model_name in models_to_try:
        try:
            response = _client.chat.completions.create(
                model=model_name,
                temperature=0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Call transcript:\n\n{transcript}"}
                ],
                tools=[{"type": "function", "function": QA_FUNCTION}],
                tool_choice={"type": "function", "function": {"name": "evaluate_call_quality"}}
            )

            tool_call = response.choices[0].message.tool_calls[0]
            data = json.loads(tool_call.function.arguments)

            return QAScore(
                empathy=DimensionScore(**data["empathy"]),
                professionalism=DimensionScore(**data["professionalism"]),
                resolution=DimensionScore(**data["resolution"]),
                communication_clarity=DimensionScore(**data["communication_clarity"]),
                overall_score=data["overall_score"],
                grade=data["grade"],
                highlights=data.get("highlights", []),
                improvements=data.get("improvements", [])
            )
        except Exception as e:
            last_error = e
            continue  # try the fallback model

    return QAScore(
        empathy=DimensionScore(justification="Error"),
        professionalism=DimensionScore(justification="Error"),
        resolution=DimensionScore(justification="Error"),
        communication_clarity=DimensionScore(justification="Error"),
        highlights=[], improvements=[],
        error=str(last_error) if last_error else "Unknown QA scoring error"
    )
