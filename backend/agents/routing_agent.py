"""
Routing Agent — LangGraph Orchestration
-----------------------------------------
Builds the full multi-agent pipeline using LangGraph StateGraph.
Handles:
  - Sequential flow: Intake → Transcription → Summarization → QA Scoring
  - Fallback: if any stage fails, pipeline continues with error logged
  - Conditional routing: skips transcription if input is already text
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from backend.agents.intake_agent import intake_agent, CallMetadata
from backend.agents.transcription_agent import transcription_agent
from backend.agents.summarization_agent import summarization_agent, CallSummary
from backend.agents.quality_score_agent import quality_score_agent, QAScore


# ── State definition ─────────────────────────────────────────────────
class CallState(TypedDict):
    # Inputs
    raw_input: object           # str (transcript) or bytes (audio)
    filename: str

    # Agent outputs
    metadata: Optional[dict]
    transcript: Optional[str]
    summary: Optional[dict]
    qa_score: Optional[dict]

    # Routing / error tracking
    current_stage: str
    errors: list[str]
    fallback_used: bool


# ── Node functions ───────────────────────────────────────────────────

def intake_node(state: CallState) -> CallState:
    """Validate input and extract metadata."""
    try:
        meta: CallMetadata = intake_agent(state["raw_input"], state.get("filename", ""))
        state["metadata"] = meta.model_dump()
        state["current_stage"] = "intake"

        if not meta.valid:
            state["errors"].append(f"Intake: {meta.error}")
            state["fallback_used"] = True
    except Exception as e:
        state["errors"].append(f"Intake error: {str(e)}")
        state["fallback_used"] = True
        state["metadata"] = {"valid": False, "input_type": "transcript", "error": str(e)}

    return state


def transcription_node(state: CallState) -> CallState:
    """Transcribe audio bytes to text. Skipped if input is already text."""
    try:
        result = transcription_agent(state["raw_input"], state.get("filename", "audio.mp3"))
        if result["success"]:
            state["transcript"] = result["transcript"]
        else:
            state["errors"].append(f"Transcription: {result['error']}")
            state["fallback_used"] = True
            state["transcript"] = None
    except Exception as e:
        state["errors"].append(f"Transcription error: {str(e)}")
        state["fallback_used"] = True
        state["transcript"] = None

    state["current_stage"] = "transcription"
    return state


def summarization_node(state: CallState) -> CallState:
    """Generate structured summary from transcript."""
    transcript = state.get("transcript") or ""

    try:
        summary: CallSummary = summarization_agent(transcript)
        state["summary"] = summary.model_dump()
        if summary.error:
            state["errors"].append(f"Summarization: {summary.error}")
            state["fallback_used"] = True
    except Exception as e:
        state["errors"].append(f"Summarization error: {str(e)}")
        state["fallback_used"] = True
        state["summary"] = {"error": str(e)}

    state["current_stage"] = "summarization"
    return state


def qa_scoring_node(state: CallState) -> CallState:
    """Score call quality on multiple dimensions."""
    transcript = state.get("transcript") or ""

    try:
        score: QAScore = quality_score_agent(transcript)
        state["qa_score"] = score.model_dump()
        if score.error:
            state["errors"].append(f"QA Scoring: {score.error}")
            state["fallback_used"] = True
    except Exception as e:
        state["errors"].append(f"QA scoring error: {str(e)}")
        state["fallback_used"] = True
        state["qa_score"] = {"error": str(e)}

    state["current_stage"] = "complete"
    return state


# ── Text passthrough node ─────────────────────────────────────────────

def text_passthrough_node(state: CallState) -> CallState:
    """
    For text input: copy raw_input directly into transcript.
    Must be a proper node — routing functions cannot mutate LangGraph state.
    """
    if isinstance(state["raw_input"], str) and state["raw_input"].strip():
        state["transcript"] = state["raw_input"]
    else:
        state["errors"].append("Passthrough: No valid text input found.")
        state["fallback_used"] = True
    state["current_stage"] = "passthrough"
    return state


# ── Conditional routing ───────────────────────────────────────────────

def route_after_intake(state: CallState) -> str:
    """
    After intake:
    - Audio input → transcription node (Whisper)
    - Text input  → text_passthrough node (sets transcript, then summarization)
    """
    meta = state.get("metadata", {})
    input_type = meta.get("input_type", "transcript")

    if input_type == "audio" and meta.get("valid", False):
        return "transcription"
    return "text_passthrough"


def route_after_transcript(state: CallState) -> str:
    """
    After transcription / passthrough: only run the LLM stages when we
    actually have text to analyse. When the transcript is empty we skip
    straight to the end — this saves two LLM calls per failed run and
    keeps the error list focused on the real cause (bad input or
    transcription failure) instead of cascading ``transcript too short``
    messages from every downstream stage.
    """
    transcript = state.get("transcript")
    if transcript and len(transcript.strip()) >= 20:
        return "summarization"
    return "skip"


def skip_llm_stages_node(state: CallState) -> CallState:
    """Terminal marker when the pipeline short-circuits before LLM stages."""
    state["current_stage"] = "complete"
    state["fallback_used"] = True
    # Only add a generic note if no prior stage already logged a reason.
    if not state.get("errors"):
        state["errors"].append("Skipped summarization and QA: no usable transcript.")
    return state


# ── Build graph ───────────────────────────────────────────────────────

def build_pipeline() -> object:
    """Build and return the compiled LangGraph pipeline."""
    graph = StateGraph(CallState)

    # Add all nodes
    graph.add_node("intake", intake_node)
    graph.add_node("transcription", transcription_node)
    graph.add_node("text_passthrough", text_passthrough_node)
    graph.add_node("summarization", summarization_node)
    graph.add_node("qa_scoring", qa_scoring_node)
    graph.add_node("skip_llm_stages", skip_llm_stages_node)

    # Entry point
    graph.set_entry_point("intake")

    # Conditional routing: audio → transcription, text → text_passthrough
    graph.add_conditional_edges(
        "intake",
        route_after_intake,
        {
            "transcription": "transcription",
            "text_passthrough": "text_passthrough",
        }
    )

    # After transcription/passthrough, only proceed to summarization if
    # we have a usable transcript. Otherwise short-circuit to the end
    # marker so we don't waste two LLM calls on an empty transcript.
    for source in ("transcription", "text_passthrough"):
        graph.add_conditional_edges(
            source,
            route_after_transcript,
            {
                "summarization": "summarization",
                "skip": "skip_llm_stages",
            },
        )

    graph.add_edge("summarization", "qa_scoring")
    graph.add_edge("qa_scoring", END)
    graph.add_edge("skip_llm_stages", END)

    return graph.compile()


_compiled_pipeline = build_pipeline()


def run_pipeline(input_data: str | bytes, filename: str = "") -> CallState:
    """
    Run the full call processing pipeline.

    Args:
        input_data: Text transcript (str) or audio bytes.
        filename:   Original filename for format detection.

    Returns:
        Final CallState with all agent outputs.
    """

    initial_state: CallState = {
        "raw_input": input_data,
        "filename": filename,
        "metadata": None,
        "transcript": None,
        "summary": None,
        "qa_score": None,
        "current_stage": "start",
        "errors": [],
        "fallback_used": False,
    }

    return _compiled_pipeline.invoke(initial_state)
