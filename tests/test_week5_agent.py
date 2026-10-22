"""Tests for W5-02 (AgentOrchestrator) and W5-04 (LoopBreakerGuardrail)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.agent.guardrails import (
    FALLBACK_MAX_ITERATIONS_NOTICE,
    FALLBACK_REPEATED_CALL_NOTICE,
    GuardrailConfig,
    LoopBreakerGuardrail,
)
from src.agent.orchestrator import AgentOrchestrator, AgentState
from src.core.dispatcher import ToolDispatcher, ToolSpecification


class _StepArgs(BaseModel):
    step: int = Field(..., ge=1)


def _make_dispatcher(tmp_path: Path) -> ToolDispatcher:
    dispatcher = ToolDispatcher(
        telemetry_log_path=tmp_path / "tool_telemetry.jsonl",
        register_defaults=False,
    )
    dispatcher.register(
        ToolSpecification(
            name="mock_step_tool",
            description="Deterministic step tool for orchestrator tests",
            args_schema=_StepArgs,
            handler=lambda step: {
                "total_hits": 1,
                "citations": [f"[mak-policy-000{step}, Page {step}]"],
                "formatted_context": f"Policy excerpt for step {step}.",
            },
        )
    )
    return dispatcher


def test_plan_act_observe_completes_and_collects_citations(tmp_path: Path) -> None:
    dispatcher = _make_dispatcher(tmp_path)
    log_path = tmp_path / "agent_loop.jsonl"

    def planner(messages: list[dict[str, Any]], iteration: int) -> dict[str, Any]:
        if iteration == 1:
            return {
                "thought": "Call mock_step_tool for step 1",
                "action": {"tool_name": "mock_step_tool", "arguments": {"step": 1}},
                "tokens": 120,
            }
        return {
            "thought": "Answer student using retrieved policy",
            "final_answer": "Late registration requires Registrar approval [mak-policy-0001, Page 1].",
            "citations": ["[mak-policy-0001, Page 1]"],
            "tokens": 80,
        }

    orchestrator = AgentOrchestrator(
        dispatcher=dispatcher,
        planner=planner,
        log_path=log_path,
    )
    result = orchestrator.run("How do I apply for late registration?", session_id="sess-01")

    assert result.final_state == AgentState.RESPOND.value
    assert result.terminated_by_guardrail is False
    assert result.iterations_used == 2
    assert result.citations == ["[mak-policy-0001, Page 1]"]
    assert result.state_transitions == [
        "INTAKE",
        "PLAN",
        "ACT",
        "OBSERVE",
        "PLAN",
        "RESPOND",
    ]
    assert log_path.is_file()


def test_hard_termination_at_max_4_iterations_emits_fallback_notice(tmp_path: Path) -> None:
    dispatcher = _make_dispatcher(tmp_path)
    log_path = tmp_path / "bounded_proof.jsonl"

    # Planner always requests a distinct valid tool call and never finalizes.
    def runaway_planner(_messages: list[dict[str, Any]], iteration: int) -> dict[str, Any]:
        return {
            "thought": f"Still searching at iteration {iteration}",
            "action": {"tool_name": "mock_step_tool", "arguments": {"step": iteration}},
        }

    orchestrator = AgentOrchestrator(
        dispatcher=dispatcher,
        guardrail_config=GuardrailConfig(max_iterations=4),
        planner=runaway_planner,
        log_path=log_path,
    )
    result = orchestrator.run("Runaway multi-step query")

    assert result.terminated_by_guardrail is True
    assert result.termination_reason == "max_iterations_reached"
    assert result.final_state == AgentState.FALLBACK_TERMINATED.value
    assert result.iterations_used == 4
    assert result.final_answer == FALLBACK_MAX_ITERATIONS_NOTICE
    assert len(result.tool_traces) == 4

    logged = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert logged["terminated_by_guardrail"] is True
    assert logged["termination_reason"] == "max_iterations_reached"
    assert logged["iterations_used"] == 4


def test_loop_breaker_halts_on_repeated_identical_tool_call(tmp_path: Path) -> None:
    dispatcher = _make_dispatcher(tmp_path)

    def cycling_planner(_messages: list[dict[str, Any]], _iteration: int) -> dict[str, Any]:
        return {
            "thought": "Repeat the exact same tool call",
            "action": {"tool_name": "mock_step_tool", "arguments": {"step": 1}},
        }

    orchestrator = AgentOrchestrator(
        dispatcher=dispatcher,
        planner=cycling_planner,
        log_path=tmp_path / "cycle.jsonl",
    )
    result = orchestrator.run("Trigger duplicate call loop")

    assert result.terminated_by_guardrail is True
    assert result.termination_reason == "repeated_tool_call_cycle"
    assert result.final_state == AgentState.FALLBACK_TERMINATED.value
    assert result.final_answer == FALLBACK_REPEATED_CALL_NOTICE
    assert len(result.tool_traces) == 1


def test_guardrail_latency_and_token_budgets() -> None:
    guard = LoopBreakerGuardrail(
        GuardrailConfig(max_iterations=4, max_elapsed_seconds=5.0, max_total_tokens=500)
    )
    timeout_dec = guard.check_iteration(iteration=2, elapsed_seconds=6.2)
    assert timeout_dec.allowed is False
    assert timeout_dec.reason == "latency_budget_exceeded"

    guard.record_tokens(600)
    token_dec = guard.check_iteration(iteration=2, elapsed_seconds=1.0)
    assert token_dec.allowed is False
    assert token_dec.reason == "token_budget_exceeded"
