#!/usr/bin/env python3
"""
AI Call Center Assistant — FastMCP Server
=========================================
Exposes call-center analysis tools, resources, and prompts via MCP.

Run locally after installing dependencies:
    python call_center_mcp/server.py

Or with FastMCP CLI:
    fastmcp run call_center_mcp/server.py
"""
from pathlib import Path
import sys
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - exercised indirectly in tests
    class FastMCP:  # minimal fallback so local tests can import this module
        def __init__(self, name: str, instructions: str = ""):
            self.name = name
            self.instructions = instructions
            self.tools = {}
            self.resources = {}
            self.prompts = {}

        def tool(self):
            def decorator(func):
                self.tools[func.__name__] = func
                return func
            return decorator

        def resource(self, uri: str):
            def decorator(func):
                self.resources[uri] = func
                return func
            return decorator

        def prompt(self):
            def decorator(func):
                self.prompts[func.__name__] = func
                return func
            return decorator

        def run(self):
            raise RuntimeError(
                "fastmcp is not installed. Run `pip install -r requirements.txt` first."
            )

from backend.agents.intake_agent import intake_agent
from backend.agents.quality_score_agent import quality_score_agent
from backend.agents.routing_agent import run_pipeline
from backend.agents.summarization_agent import summarization_agent
from backend.utils.validation import clean_transcript, validate_transcript_text

SERVER_TAG = "[Served by call-center-assistant MCP]"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONFIG_PATH = PROJECT_ROOT / "config" / "mcp.yaml"
SAMPLE_DIR = BACKEND_ROOT / "data" / "sample_transcripts"
DEFAULT_CONFIG = {
    "model": {"primary": "gpt-4o", "fallback": "gpt-4o-mini", "temperature": 0.2},
    "transcription": {
        "model": "whisper-1",
        "supported_formats": [".mp3", ".wav", ".m4a", ".webm", ".ogg", ".mp4"],
        "max_file_size_mb": 25,
    },
    "pipeline": {"max_transcript_chars": 50_000, "fallback_on_error": True, "log_errors": True},
    "qa_rubric": {
        "dimensions": ["empathy", "professionalism", "resolution", "communication_clarity"],
        "scale": 10,
        "grade_thresholds": {"excellent": 8, "good": 6, "needs_improvement": 4, "poor": 0},
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge ``override`` into ``base``. Override wins on leaf values."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG

    try:
        with CONFIG_PATH.open(encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}
    except yaml.YAMLError as exc:
        print(f"[mcp] Warning: failed to parse {CONFIG_PATH}: {exc}. Using defaults.")
        return DEFAULT_CONFIG

    if not isinstance(data, dict):
        print(f"[mcp] Warning: {CONFIG_PATH} did not contain a mapping. Using defaults.")
        return DEFAULT_CONFIG

    return _deep_merge(DEFAULT_CONFIG, data)


CONFIG = _load_config()
# Defensive lookups so a partial mcp.yaml never crashes startup.
PRIMARY_MODEL = CONFIG.get("model", {}).get("primary", DEFAULT_CONFIG["model"]["primary"])
TRANSCRIPTION_MODEL = CONFIG.get("transcription", {}).get("model", DEFAULT_CONFIG["transcription"]["model"])
MAX_TRANSCRIPT_CHARS = CONFIG.get("pipeline", {}).get(
    "max_transcript_chars", DEFAULT_CONFIG["pipeline"]["max_transcript_chars"]
)
SUPPORTED_AUDIO_FORMATS = ", ".join(
    CONFIG.get("transcription", {}).get("supported_formats", DEFAULT_CONFIG["transcription"]["supported_formats"])
)
QA_DIMENSIONS = ", ".join(
    CONFIG.get("qa_rubric", {}).get("dimensions", DEFAULT_CONFIG["qa_rubric"]["dimensions"])
)

mcp = FastMCP(
    name="AI Call Center Assistant",
    instructions=(
        "You are a call center operations assistant. Use these tools to validate "
        "call transcripts, generate summaries, score service quality, and review "
        "sample calls. The primary LLM is configured as "
        f"{PRIMARY_MODEL}, transcription uses {TRANSCRIPTION_MODEL}, and transcript "
        f"inputs should stay under {MAX_TRANSCRIPT_CHARS} characters. Score calls on "
        f"these configured QA dimensions: {QA_DIMENSIONS}. Be factual and concise, "
        "and clearly separate actual model output from any validation or fallback errors."
    ),
)


def _sample_slug_map() -> dict[str, Path]:
    samples = {}
    if SAMPLE_DIR.exists():
        for path in sorted(SAMPLE_DIR.glob("*.txt")):
            samples[path.stem] = path
    return samples


def _format_list(items: list[str], empty_label: str = "None") -> str:
    if not items:
        return empty_label
    return "\n".join(f"- {item}" for item in items)


def _load_sample_text(sample_name: str) -> str:
    samples = _sample_slug_map()
    if sample_name not in samples:
        available = ", ".join(sorted(samples)) or "no samples available"
        raise ValueError(
            f"Unknown sample '{sample_name}'. Available samples: {available}"
        )
    return samples[sample_name].read_text(encoding="utf-8")


def _prepare_transcript(transcript: str) -> tuple[bool, str, str]:
    cleaned = clean_transcript(transcript or "")
    if len(cleaned) > MAX_TRANSCRIPT_CHARS:
        return (
            False,
            f"Transcript too long (> {MAX_TRANSCRIPT_CHARS} chars). Please trim.",
            cleaned,
        )
    ok, message = validate_transcript_text(cleaned)
    return ok, message, cleaned


def _configuration_notes() -> list[str]:
    return [
        f"Configured summary/QA model: {PRIMARY_MODEL}",
        f"Configured transcription model: {TRANSCRIPTION_MODEL}",
        f"Configured max transcript length: {MAX_TRANSCRIPT_CHARS}",
        f"Configured audio formats: {SUPPORTED_AUDIO_FORMATS}",
        f"Configured QA dimensions: {QA_DIMENSIONS}",
    ]


@mcp.tool()
def validate_transcript_input(
    transcript: str,
    filename: str = "transcript.txt",
) -> str:
    """Validate a call transcript before analysis.

    Returns intake metadata plus a clear pass/fail status. Use this to check
    transcript quality before running summarization or QA scoring.
    """
    cleaned = clean_transcript(transcript or "")
    metadata = intake_agent(cleaned, filename)
    status = "valid" if metadata.valid else "invalid"
    details = [
        f"{SERVER_TAG}",
        "",
        f"Validation status: {status}",
        f"Input type: {metadata.input_type}",
        f"Call ID: {metadata.call_id}",
        f"Estimated duration: {metadata.duration_estimate or 'N/A'}",
        f"Character count: {metadata.char_count or 0}",
    ]
    if metadata.error:
        details.append(f"Error: {metadata.error}")
    details.extend(["", "Configuration:"])
    details.extend(f"- {note}" for note in _configuration_notes())
    return "\n".join(details)


@mcp.tool()
def summarize_call(transcript: str) -> str:
    """Generate a structured summary for a customer-service transcript."""
    ok, message, cleaned = _prepare_transcript(transcript)
    if not ok:
        return f"{SERVER_TAG}\n\nUnable to summarize transcript: {message}"

    summary = summarization_agent(cleaned)
    if summary.error:
        return f"{SERVER_TAG}\n\nSummarization failed: {summary.error}"

    return "\n".join([
        f"{SERVER_TAG}",
        "",
        f"One-line summary: {summary.one_line_summary}",
        f"Customer issue: {summary.customer_issue}",
        f"Resolution: {summary.resolution}",
        f"Sentiment: {summary.sentiment}",
        f"Outcome: {summary.call_outcome}",
        "Action items:",
        _format_list(summary.action_items),
        "Key topics:",
        _format_list(summary.key_topics),
        "",
        f"Configured model: {PRIMARY_MODEL}",
    ])


@mcp.tool()
def score_call_quality(transcript: str) -> str:
    """Evaluate a transcript on empathy, professionalism, resolution, and clarity."""
    ok, message, cleaned = _prepare_transcript(transcript)
    if not ok:
        return f"{SERVER_TAG}\n\nUnable to score transcript: {message}"

    qa = quality_score_agent(cleaned)
    if qa.error:
        return f"{SERVER_TAG}\n\nQA scoring failed: {qa.error}"

    dimensions = [
        ("Empathy", qa.empathy),
        ("Professionalism", qa.professionalism),
        ("Resolution", qa.resolution),
        ("Communication Clarity", qa.communication_clarity),
    ]
    overall = f"{qa.overall_score}/10" if qa.overall_score is not None else "N/A"
    lines = [
        f"{SERVER_TAG}",
        "",
        f"Overall score: {overall}",
        f"Grade: {qa.grade or 'N/A'}",
        "",
        "Dimension scores:",
    ]
    for label, score in dimensions:
        score_value = f"{score.score}/10" if score.score is not None else "N/A"
        lines.append(f"- {label}: {score_value} — {score.justification}")
    lines.extend([
        "",
        "Highlights:",
        _format_list(qa.highlights),
        "Improvements:",
        _format_list(qa.improvements),
        "",
        f"Configured QA dimensions: {QA_DIMENSIONS}",
    ])
    return "\n".join(lines)


@mcp.tool()
def analyze_call(transcript: str, filename: str = "transcript.txt") -> str:
    """Run the full call-analysis pipeline on a transcript.

    Includes intake metadata, summary, QA score, and any fallback errors.
    """
    ok, message, cleaned = _prepare_transcript(transcript)
    if not ok:
        return f"{SERVER_TAG}\n\nUnable to analyze transcript: {message}"

    result = run_pipeline(cleaned, filename)
    metadata = result.get("metadata") or {}
    summary = result.get("summary") or {}
    qa = result.get("qa_score") or {}
    errors = result.get("errors") or []

    summary_error = summary.get("error")
    qa_error = qa.get("error")

    lines = [
        f"{SERVER_TAG}",
        "",
        f"Call ID: {metadata.get('call_id', 'N/A')}",
        f"Input type: {metadata.get('input_type', 'N/A')}",
        f"Estimated duration: {metadata.get('duration_estimate', 'N/A')}",
        f"Current stage: {result.get('current_stage', 'N/A')}",
        f"Fallback used: {'yes' if result.get('fallback_used') else 'no'}",
        f"Configured model: {PRIMARY_MODEL}",
        "",
        "Summary:",
    ]
    if summary_error:
        lines.append(f"- Error: {summary_error}")
    else:
        lines.extend([
            f"- One-line summary: {summary.get('one_line_summary', 'N/A')}",
            f"- Customer issue: {summary.get('customer_issue', 'N/A')}",
            f"- Resolution: {summary.get('resolution', 'N/A')}",
            f"- Sentiment: {summary.get('sentiment', 'N/A')}",
            f"- Outcome: {summary.get('call_outcome', 'N/A')}",
        ])

    lines.extend(["", "QA:"])
    if qa_error:
        lines.append(f"- Error: {qa_error}")
    else:
        lines.extend([
            f"- Overall score: {qa.get('overall_score', 'N/A')}",
            f"- Grade: {qa.get('grade', 'N/A')}",
        ])

    lines.extend(["", "Errors:", _format_list(errors)])
    return "\n".join(lines)


@mcp.tool()
def get_sample_transcript(sample_name: str) -> str:
    """Load one of the built-in sample transcripts by slug."""
    try:
        text = _load_sample_text(sample_name)
    except ValueError as exc:
        return f"{SERVER_TAG}\n\n{exc}"
    return f"{SERVER_TAG}\n\nSample: {sample_name}\n\n{text}"


# Patch docstring with the live list of sample slugs so MCP clients see real values.
_available_slugs = sorted(_sample_slug_map())
get_sample_transcript.__doc__ = (
    "Load one of the built-in sample transcripts by slug.\n\n"
    f"Available slugs: {', '.join(_available_slugs) if _available_slugs else 'none'}."
)


@mcp.resource("config://mcp-settings")
def get_mcp_settings() -> str:
    """Read the call-center MCP configuration file."""
    return CONFIG_PATH.read_text(encoding="utf-8")


@mcp.resource("config://runtime-summary")
def get_runtime_summary() -> str:
    """Summarize the MCP runtime configuration currently in use."""
    return "\n".join(_configuration_notes())


@mcp.resource("samples://catalog")
def get_sample_catalog() -> str:
    """List all bundled sample transcript slugs."""
    samples = sorted(_sample_slug_map())
    if not samples:
        return "No sample transcripts available."
    return "\n".join(samples)


@mcp.resource("samples://transcript/{sample_name}")
def get_sample_resource(sample_name: str) -> str:
    """Read a sample transcript by slug."""
    return _load_sample_text(sample_name)


@mcp.prompt()
def supervisor_review(sample_name: str = "poor_service_example") -> str:
    """Prompt template for a supervisor reviewing a call."""
    return (
        f"Please review the sample call '{sample_name}'.\n\n"
        f"1. Use get_sample_transcript to load the transcript\n"
        f"2. Use analyze_call to run the full analysis\n"
        f"3. Explain the main customer issue, whether it was resolved, and the "
        f"largest coaching opportunity for the agent\n"
        f"4. Keep the response concise and manager-friendly"
    )


@mcp.prompt()
def qa_coaching(sample_name: str = "billing_dispute") -> str:
    """Prompt template for quality-coaching feedback."""
    return (
        f"I want coaching feedback for the sample call '{sample_name}'.\n\n"
        f"1. Use get_sample_transcript to fetch the transcript\n"
        f"2. Use score_call_quality to evaluate it\n"
        f"3. Summarize what the agent did well\n"
        f"4. Give 3 practical coaching recommendations for improvement"
    )


if __name__ == "__main__":
    mcp.run()
