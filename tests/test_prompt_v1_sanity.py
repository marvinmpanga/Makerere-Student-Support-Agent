"""
Sanity verification for Prompt Specification v1.0 (W2-03).

Tests the system_prompt.md against one representative student query using a mocked
GeminiBaselineClient, then validates the structured output against the required schema.

Run:  python -m pytest tests/test_prompt_v1_sanity.py -v
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.core.llm import GeminiBaselineClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "v1.0"
VALID_CATEGORIES = {
    "Onboarding/Registration",
    "Examinations/Appeals",
    "Fees/Billing",
    "ICT/Portal",
    "General Academic",
    "Unsupported",
}
POLICY_ID_PATTERN = re.compile(r"^mak-policy-\d{4}$")

# Canonical mock response matching the v1.0 schema for a missing-mark query
MOCK_STRUCTURED_RESPONSE = {
    "inquiry_category": "Examinations/Appeals",
    "confidence_score": 0.88,
    "procedural_guidance": [
        (
            "Step 1: Log in to the AIMS student portal at aims.mak.ac.ug and navigate to "
            "'My Results' to confirm the mark is listed as missing or blank."
        ),
        (
            "Step 2: Obtain the official 'Missing Mark Report Form' from your Faculty "
            "Examinations Office (CoCIS, Senate Building, Room G14)."
        ),
        (
            "Step 3: Complete the form with your course unit code (BSE4104), lecturer name, "
            "and the date you sat the examination."
        ),
        "Step 4: Attach supporting evidence such as your examination attendance slip.",
        (
            "Step 5: Submit the form to the Faculty Examinations Officer within 14 working days "
            "of the official results release. Late submissions require Dean of Faculty approval."
        ),
        "Step 6: Retain a copy of your submitted form and request a reference number.",
        "Note: This process initiates an investigation and does not guarantee a mark change.",
    ],
    "policy_citations": ["mak-policy-0043", "mak-policy-0060", "mak-policy-0039"],
    "requires_ticket_escalation": True,
    "ticket_draft": {
        "target_office": "CoCIS Faculty Examinations Office",
        "subject": "Missing Examination Mark — BSE4104 — Year 4 Semester I",
        "case_details": (
            "A student registered in BSc Software Engineering, Year 4 Semester I 2025/2026, "
            "reports that the mark for course unit BSE4104 is absent from the official results "
            "published on the AIMS portal. The Faculty Examinations Officer is requested to "
            "investigate in accordance with mak-policy-0043."
        ),
        "student_confirmation_required": True,
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_system_prompt() -> str:
    """Load the raw executable system prompt (strip markdown header and comments)."""
    raw = (PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    # Strip everything up to and including the first horizontal rule (---)
    parts = raw.split("---", maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else raw.strip()


def validate_schema(output: dict) -> list[str]:
    """Return a list of schema violation messages (empty = pass)."""
    errors: list[str] = []

    # inquiry_category
    cat = output.get("inquiry_category")
    if cat not in VALID_CATEGORIES:
        errors.append(f"inquiry_category '{cat}' not in allowed enum {VALID_CATEGORIES}")

    # confidence_score
    score = output.get("confidence_score")
    if not isinstance(score, (int, float)) or not (0.0 <= float(score) <= 1.0):
        errors.append(f"confidence_score '{score}' must be a float in [0.0, 1.0]")

    # procedural_guidance
    guidance = output.get("procedural_guidance")
    if not isinstance(guidance, list) or len(guidance) < 1:
        errors.append("procedural_guidance must be a non-empty array")
    elif not all(isinstance(s, str) for s in guidance):
        errors.append("All procedural_guidance items must be strings")

    # policy_citations
    citations = output.get("policy_citations")
    if not isinstance(citations, list):
        errors.append("policy_citations must be an array")
    else:
        for cid in citations:
            if not POLICY_ID_PATTERN.match(cid):
                errors.append(f"policy_citations item '{cid}' does not match mak-policy-NNNN")

    # requires_ticket_escalation
    escalation = output.get("requires_ticket_escalation")
    if not isinstance(escalation, bool):
        errors.append("requires_ticket_escalation must be a boolean")

    # ticket_draft
    ticket = output.get("ticket_draft")
    if escalation is True:
        if ticket is None:
            errors.append("ticket_draft must not be null when requires_ticket_escalation is true")
        elif isinstance(ticket, dict):
            for field in ("target_office", "subject", "case_details", "student_confirmation_required"):
                if field not in ticket:
                    errors.append(f"ticket_draft missing required field '{field}'")
            if ticket.get("student_confirmation_required") is not True:
                errors.append("ticket_draft.student_confirmation_required must always be true")
    elif escalation is False and ticket is not None:
        errors.append("ticket_draft must be null when requires_ticket_escalation is false")

    return errors


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def system_prompt() -> str:
    return load_system_prompt()


def test_system_prompt_file_exists():
    """The system_prompt.md file must exist at prompts/v1.0/."""
    assert (PROMPTS_DIR / "system_prompt.md").exists(), (
        "prompts/v1.0/system_prompt.md not found"
    )


def test_prompt_spec_file_exists():
    """The prompt_spec.md file must exist at prompts/v1.0/."""
    assert (PROMPTS_DIR / "prompt_spec.md").exists(), (
        "prompts/v1.0/prompt_spec.md not found"
    )


def test_system_prompt_contains_no_markdown_fences(system_prompt):
    """Executable portion of system prompt must not contain ``` code fences."""
    assert "```" not in system_prompt, (
        "system_prompt.md contains markdown code fences which must not be injected into LLM"
    )


def test_system_prompt_contains_absolute_prohibitions(system_prompt):
    """System prompt must explicitly prohibit grade alteration and fee waivers."""
    assert "grade" in system_prompt.lower(), "Prompt must mention grade prohibition"
    assert "waiver" in system_prompt.lower(), "Prompt must mention waiver prohibition"
    assert "student_confirmation_required" in system_prompt, (
        "Prompt must reference student_confirmation_required"
    )


def test_system_prompt_enforces_json_only_output(system_prompt):
    """System prompt must instruct the model to return raw JSON only."""
    assert "raw" in system_prompt.lower() or "only" in system_prompt.lower(), (
        "System prompt must instruct JSON-only output"
    )
    assert "markdown" in system_prompt.lower() or "fences" in system_prompt.lower(), (
        "System prompt must explicitly forbid markdown code fences"
    )


def test_missing_mark_sanity_query(monkeypatch):
    """
    Sanity test: mock the Gemini API and confirm the structured output passes
    the v1.0 schema for the canonical missing-mark query.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-sanity")

    mock_response = SimpleNamespace(
        text=json.dumps(MOCK_STRUCTURED_RESPONSE),
        usage_metadata=SimpleNamespace(
            prompt_token_count=312,
            candidates_token_count=487,
        ),
    )

    system_instruction = load_system_prompt()
    user_payload = json.dumps({
        "student_id": "23/U/1234/PS",
        "programme": "BSc Software Engineering",
        "academic_year": "Year 4 Semester I 2025/2026",
        "query": "How do I report a missing exam mark for BSE4104?",
        "context_documents": (
            "[mak-policy-0043] Chapter 7: Missing marks must be reported to the Faculty "
            "Examinations Officer within 14 working days of results release.\n"
            "[mak-policy-0060] Section 4.2: Semester credit system retake and mark dispute "
            "procedures for undergraduate students."
        ),
    })

    with patch("src.core.llm.genai.configure"), patch(
        "src.core.llm.genai.GenerativeModel"
    ) as model_class:
        model_class.return_value.generate_content.return_value = mock_response
        client = GeminiBaselineClient()
        result = client.generate_response(
            system_instruction=system_instruction,
            user_query=user_payload,
            force_json=True,
        )

    # Top-level call checks
    assert result["status"] == "success", f"LLM call failed: {result.get('error_message')}"
    assert result["structured_output"] is not None, "structured_output must not be None"
    assert result["latency_seconds"] >= 0

    structured = result["structured_output"]

    # Schema validation
    violations = validate_schema(structured)
    assert not violations, f"Schema violations: {violations}"

    # Specific field assertions for the missing-mark case
    assert structured["inquiry_category"] == "Examinations/Appeals"
    assert structured["confidence_score"] >= 0.80
    assert len(structured["procedural_guidance"]) >= 5
    assert "mak-policy-0043" in structured["policy_citations"]
    assert structured["requires_ticket_escalation"] is True
    assert structured["ticket_draft"] is not None
    assert structured["ticket_draft"]["student_confirmation_required"] is True
    assert "23/U/1234/PS" not in structured["ticket_draft"]["case_details"], (
        "student_id must not appear in ticket_draft.case_details"
    )

    # Print formatted output for visual inspection
    print("\n" + "=" * 70)
    print("SANITY VERIFICATION — Prompt v1.0 — Missing Mark Query (BSE4104)")
    print("=" * 70)
    print(json.dumps(structured, indent=2, ensure_ascii=False))
    print("=" * 70)
    print(f"Token usage — prompt: {result['raw_usage']['prompt_token_count']}, "
          f"response: {result['raw_usage']['candidates_token_count']}")
    print(f"Latency: {result['latency_seconds']:.4f}s")
    print(f"Schema violations: {len(violations)} (expected: 0)")
