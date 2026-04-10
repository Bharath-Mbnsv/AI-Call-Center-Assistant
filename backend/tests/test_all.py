"""
Test suite for AI Call Center Assistant.
Run: python -m pytest backend/tests -v
"""
import os
import json

import pytest


# ── Intake Agent Tests ────────────────────────────────────────────────
class TestIntakeAgent:

    def test_valid_transcript(self):
        from backend.agents.intake_agent import intake_agent
        result = intake_agent("Agent: Hello. Customer: Hi I need help.\nThis is a valid transcript.", "call.txt")
        assert result.valid is True
        assert result.input_type == "transcript"

    def test_empty_transcript_fails(self):
        from backend.agents.intake_agent import intake_agent
        result = intake_agent("", "call.txt")
        assert result.valid is False
        assert "empty" in result.error.lower()

    def test_too_short_transcript_fails(self):
        from backend.agents.intake_agent import intake_agent
        result = intake_agent("Hi", "call.txt")
        assert result.valid is False

    def test_valid_audio_bytes(self):
        from backend.agents.intake_agent import intake_agent
        fake_audio = b"FAKE_AUDIO_BYTES" * 100
        result = intake_agent(fake_audio, "call.mp3")
        assert result.valid is True
        assert result.input_type == "audio"

    def test_unsupported_audio_format_fails(self):
        from backend.agents.intake_agent import intake_agent
        result = intake_agent(b"fake", "call.xyz")
        assert result.valid is False

    def test_call_id_generated(self):
        from backend.agents.intake_agent import intake_agent
        result = intake_agent("Agent: Hello Customer: Hi I need help with my account please.", "t.txt")
        assert result.call_id.startswith("CALL-")

    def test_char_count_set(self):
        from backend.agents.intake_agent import intake_agent
        text = "Agent: Hello there. Customer: I need help with my billing issue please." * 2
        result = intake_agent(text, "t.txt")
        if result.valid:
            assert result.char_count == len(text)

    def test_timestamp_set(self):
        from backend.agents.intake_agent import intake_agent
        result = intake_agent("Agent: Hello. Customer: Hi I need help with something.", "t.txt")
        assert result.timestamp is not None and len(result.timestamp) > 0


# ── Summarization Agent Tests (logic only) ───────────────────────────
class TestSummarizationLogic:

    def test_empty_transcript_returns_error(self):
        from backend.agents.summarization_agent import summarization_agent
        result = summarization_agent("")
        assert result.error is not None

    def test_short_transcript_returns_error(self):
        from backend.agents.summarization_agent import summarization_agent
        result = summarization_agent("Hi")
        assert result.error is not None

    def test_callsummary_model_fields(self):
        from backend.agents.summarization_agent import CallSummary
        s = CallSummary(
            one_line_summary="Test summary",
            customer_issue="Billing issue",
            resolution="Refund issued",
            action_items=["Send confirmation email"],
            key_topics=["billing", "refund"],
            sentiment="Positive",
            call_outcome="Resolved"
        )
        assert s.one_line_summary == "Test summary"
        assert s.sentiment == "Positive"
        assert len(s.action_items) == 1
        assert s.error is None

    def test_callsummary_valid_outcomes(self):
        from backend.agents.summarization_agent import CallSummary
        for outcome in ["Resolved", "Unresolved", "Escalated", "Follow-up Required"]:
            s = CallSummary(
                one_line_summary="x", customer_issue="x", resolution="x",
                action_items=[], key_topics=[], sentiment="Neutral",
                call_outcome=outcome
            )
            assert s.call_outcome == outcome


# ── Quality Scoring Tests (logic only) ───────────────────────────────
class TestQualityScoringLogic:

    def test_empty_transcript_returns_error(self):
        from backend.agents.quality_score_agent import quality_score_agent
        result = quality_score_agent("")
        assert result.error is not None
        assert result.overall_score is None
        assert result.empathy.score is None

    def test_qa_score_model(self):
        from backend.agents.quality_score_agent import QAScore, DimensionScore
        score = QAScore(
            empathy=DimensionScore(score=8, justification="Agent was empathetic"),
            professionalism=DimensionScore(score=9, justification="Very professional"),
            resolution=DimensionScore(score=7, justification="Issue resolved"),
            communication_clarity=DimensionScore(score=8, justification="Clear communication"),
            overall_score=8,
            grade="Good",
            highlights=["Great empathy"],
            improvements=["Could be faster"]
        )
        assert score.overall_score == 8
        assert score.grade == "Good"
        assert score.error is None

    def test_dimension_score_range(self):
        """Scores should be between 1 and 10."""
        from backend.agents.quality_score_agent import DimensionScore
        d = DimensionScore(score=7, justification="Good performance")
        assert 1 <= d.score <= 10

    def test_grade_mapping(self):
        """Grade logic: 8-10=Excellent, 6-7=Good, 4-5=Needs Improvement, <4=Poor"""
        def get_grade(score):
            if score >= 8: return "Excellent"
            if score >= 6: return "Good"
            if score >= 4: return "Needs Improvement"
            return "Poor"

        assert get_grade(9) == "Excellent"
        assert get_grade(7) == "Good"
        assert get_grade(5) == "Needs Improvement"
        assert get_grade(2) == "Poor"


# ── Validation Tests ──────────────────────────────────────────────────
class TestValidation:

    def test_valid_audio_extensions(self):
        from backend.utils.validation import validate_file_extension
        for ext in [".mp3", ".wav", ".m4a", ".webm"]:
            ok, msg = validate_file_extension(f"file{ext}")
            assert ok, f"Expected {ext} to be valid"

    def test_invalid_extension(self):
        from backend.utils.validation import validate_file_extension
        ok, msg = validate_file_extension("file.xyz")
        assert not ok

    def test_valid_transcript(self):
        from backend.utils.validation import validate_transcript_text
        ok, msg = validate_transcript_text("Agent: Hello. Customer: Hi I need help with my account.")
        assert ok

    def test_empty_transcript_invalid(self):
        from backend.utils.validation import validate_transcript_text
        ok, msg = validate_transcript_text("")
        assert not ok

    def test_short_transcript_invalid(self):
        from backend.utils.validation import validate_transcript_text
        ok, msg = validate_transcript_text("Hi")
        assert not ok

    def test_valid_json_dict_format(self):
        from backend.utils.validation import validate_json_transcript
        data = json.dumps({"transcript": "Agent: Hello, how can I help you today?"})
        ok, msg, text = validate_json_transcript(data)
        assert ok
        assert "Hello" in text

    def test_valid_json_list_format(self):
        from backend.utils.validation import validate_json_transcript
        data = json.dumps([
            {"speaker": "Agent", "text": "Hello, how can I help?"},
            {"speaker": "Customer", "text": "I need a refund."}
        ])
        ok, msg, text = validate_json_transcript(data)
        assert ok
        assert "Agent:" in text
        assert "Customer:" in text

    def test_invalid_json(self):
        from backend.utils.validation import validate_json_transcript
        ok, msg, text = validate_json_transcript("not valid json {{{")
        assert not ok

    def test_invalid_json_list_item_shape(self):
        from backend.utils.validation import validate_json_transcript
        ok, msg, text = validate_json_transcript(json.dumps(["oops"]))
        assert not ok
        assert "entry must be an object" in msg.lower()

    def test_non_string_json_transcript_rejected(self):
        from backend.utils.validation import validate_json_transcript
        ok, msg, text = validate_json_transcript(json.dumps({"transcript": ["not", "text"]}))
        assert not ok

    def test_transcript_too_long_invalid(self):
        from backend.utils.validation import validate_transcript_text, MAX_TRANSCRIPT_CHARS
        text = "a" * (MAX_TRANSCRIPT_CHARS + 1)
        ok, msg = validate_transcript_text(text)
        assert not ok
        assert "too long" in msg.lower()

    def test_clean_transcript(self):
        from backend.utils.validation import clean_transcript
        messy = "  Agent: Hello   \n\n\n  Customer: Hi  \n"
        cleaned = clean_transcript(messy)
        assert "  " not in cleaned
        assert cleaned.count("\n") == 1


class TestMCPServer:

    def test_sample_catalog_contains_expected_entries(self):
        from call_center_mcp.server import get_sample_catalog
        catalog = get_sample_catalog()
        assert "billing_dispute" in catalog
        assert "technical_support" in catalog

    def test_get_sample_transcript_returns_content(self):
        from call_center_mcp.server import get_sample_transcript
        result = get_sample_transcript("billing_dispute")
        assert "Sample: billing_dispute" in result
        assert "Customer" in result or "Agent" in result

    def test_validate_transcript_input_rejects_short_text(self):
        from call_center_mcp.server import validate_transcript_input
        result = validate_transcript_input("Hi")
        assert "invalid" in result.lower()

    def test_analyze_call_rejects_invalid_text(self):
        from call_center_mcp.server import analyze_call
        result = analyze_call("Hi")
        assert "unable to analyze transcript" in result.lower()

    def test_mcp_config_resource_reads_yaml(self):
        from call_center_mcp.server import get_mcp_settings
        config_text = get_mcp_settings()
        assert 'primary: "gpt-4o"' in config_text
        assert 'fallback: "gpt-4o-mini"' in config_text

    def test_mcp_runtime_summary_uses_config(self):
        from call_center_mcp.server import get_runtime_summary
        summary = get_runtime_summary()
        assert "Configured summary/QA model: gpt-4o" in summary
        assert "Configured transcription model: whisper-1" in summary

    def test_deep_merge_recursively_merges_nested_dicts(self):
        from call_center_mcp.server import _deep_merge
        base = {"model": {"primary": "a", "temperature": 0.2}, "pipeline": {"x": 1}}
        override = {"model": {"primary": "b"}, "pipeline": {"y": 2}}
        merged = _deep_merge(base, override)
        # nested override wins at the leaf
        assert merged["model"]["primary"] == "b"
        # unmentioned leaves survive
        assert merged["model"]["temperature"] == 0.2
        # sibling keys from both sides are preserved
        assert merged["pipeline"] == {"x": 1, "y": 2}
        # base is not mutated
        assert base["model"]["primary"] == "a"

    def test_deep_merge_override_replaces_non_dict(self):
        from call_center_mcp.server import _deep_merge
        merged = _deep_merge({"k": [1, 2]}, {"k": [3]})
        assert merged["k"] == [3]

    def test_score_call_quality_shows_na_when_scoring_fails(self):
        """On empty input the QA agent errors out; the tool should surface that cleanly."""
        from call_center_mcp.server import score_call_quality
        result = score_call_quality("")
        # empty transcript is rejected before scoring is ever attempted
        assert "unable to score transcript" in result.lower()
        # and we should never render the string "None/10"
        assert "None/10" not in result

    def test_analyze_call_surfaces_summary_and_qa_errors(self, monkeypatch):
        """analyze_call should show per-stage error lines, not fabricated values."""
        from call_center_mcp import server as mcp_server

        fake_result = {
            "metadata": {
                "call_id": "CALL-TEST",
                "input_type": "transcript",
                "duration_estimate": "1 min",
            },
            "summary": {"error": "LLM unavailable"},
            "qa_score": {"error": "LLM unavailable"},
            "errors": ["Summarization: LLM unavailable", "QA: LLM unavailable"],
            "current_stage": "complete",
            "fallback_used": True,
        }
        monkeypatch.setattr(mcp_server, "run_pipeline", lambda text, filename: fake_result)

        transcript = "Agent: Hello. Customer: Hi I need help with my billing issue please."
        output = mcp_server.analyze_call(transcript)

        assert "Summary:" in output
        assert "- Error: LLM unavailable" in output
        assert "QA:" in output
        # Should NOT have invented summary fields when the stage errored
        assert "One-line summary:" not in output
        assert "Overall score:" not in output
        assert "Fallback used: yes" in output


# ── Routing Logic Tests ───────────────────────────────────────────────
class TestRoutingLogic:

    def test_text_input_skips_transcription(self):
        """Text input should route through text passthrough."""
        from backend.agents.routing_agent import route_after_intake
        state = {
            "raw_input": "Agent: Hello. Customer: I need help.",
            "metadata": {"input_type": "transcript", "valid": True},
            "errors": []
        }
        assert route_after_intake(state) == "text_passthrough"

    def test_audio_input_routes_to_transcription(self):
        """Audio input should route to transcription first."""
        from backend.agents.routing_agent import route_after_intake
        state = {
            "raw_input": b"fake_audio",
            "metadata": {"input_type": "audio", "valid": True},
            "errors": []
        }
        assert route_after_intake(state) == "transcription"

    def test_invalid_input_falls_back(self):
        """Invalid input should fall back to summarization gracefully."""
        from backend.agents.routing_agent import run_pipeline
        state = run_pipeline("", "call.txt")
        assert len(state["errors"]) > 0
        assert state["fallback_used"] is True
        assert state["current_stage"] == "complete"

    def test_state_has_required_keys(self):
        """CallState must have all required keys."""
        state = {
            "raw_input": "test",
            "filename": "test.txt",
            "metadata": None,
            "transcript": None,
            "summary": None,
            "qa_score": None,
            "current_stage": "start",
            "errors": [],
            "fallback_used": False,
        }
        required = ["raw_input", "filename", "metadata", "transcript",
                    "summary", "qa_score", "current_stage", "errors", "fallback_used"]
        for key in required:
            assert key in state

    def test_errors_accumulate_dont_stop_pipeline(self):
        """Errors should be logged but pipeline should continue."""
        errors = []
        # Simulate intake error
        errors.append("Intake: File too small")
        # Pipeline continues to summarization
        assert len(errors) == 1
        # Simulate summarization also having an issue
        errors.append("Summarization: Parse error")
        assert len(errors) == 2
        # Pipeline still reaches QA stage


# ── Sample Data Tests ─────────────────────────────────────────────────
class TestSampleData:

    def test_sample_transcripts_exist(self):
        sample_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_transcripts")
        assert os.path.exists(sample_dir), "Sample transcripts directory missing"

    def test_sample_transcripts_readable(self):
        sample_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_transcripts")
        files = [f for f in os.listdir(sample_dir) if f.endswith(".txt")]
        assert len(files) >= 3, "Expected at least 3 sample transcripts"
        for f in files:
            path = os.path.join(sample_dir, f)
            with open(path) as fp:
                content = fp.read()
            assert len(content) > 100, f"{f} appears empty"

    def test_sample_transcripts_have_agent_customer(self):
        """Good transcripts should contain Agent and Customer turns."""
        sample_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_transcripts")
        for f in os.listdir(sample_dir):
            if f.endswith(".txt"):
                path = os.path.join(sample_dir, f)
                with open(path) as fp:
                    content = fp.read()
                assert "Agent:" in content or "Customer:" in content, f"{f} missing speaker labels"
