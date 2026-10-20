"""Unit tests for W2-04 BaselineExecutionHarness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.eval.baseline_harness import BaselineExecutionHarness


class _FakeLLMClient:
    def generate_response(
        self,
        system_instruction: str,
        user_query: str,
        context_documents: str | None = None,
        force_json: bool = False,
    ) -> dict[str, Any]:
        payload = {"intent": "policy_question", "query_echo": user_query}
        return {
            "status": "success",
            "model": "gemini-1.5-flash",
            "latency_seconds": 0.123,
            "response_text": json.dumps(payload),
            "structured_output": payload if force_json else None,
            "raw_usage": {"prompt_token_count": 40, "candidates_token_count": 15},
            "error_message": None,
        }


def test_harness_logs_trace_and_computes_total_tokens(tmp_path: Path) -> None:
    log_file = tmp_path / "traces.jsonl"
    harness = BaselineExecutionHarness(
        client=_FakeLLMClient(),
        prompt_version="v1.1",
        log_path=log_file,
    )
    trace = harness.run_case("How do I register late?", case_id="US-01")
    assert trace.status == "success"
    assert trace.total_tokens == 55
    assert trace.structured_output == {
        "intent": "policy_question",
        "query_echo": "How do I register late?",
    }
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    saved = json.loads(lines[0])
    assert saved["case_id"] == "US-01"
    assert saved["prompt_version"] == "v1.1"


def test_harness_run_suite_processes_all_cases(tmp_path: Path) -> None:
    log_file = tmp_path / "suite.jsonl"
    harness = BaselineExecutionHarness(client=_FakeLLMClient(), log_path=log_file)
    traces = harness.run_suite(
        [
            {"case_id": "US-01", "query": "When is tuition due?"},
            {"case_id": "US-02", "query": "How do I appeal a missing mark?"},
        ]
    )
    assert len(traces) == 2
    assert [t.case_id for t in traces] == ["US-01", "US-02"]
