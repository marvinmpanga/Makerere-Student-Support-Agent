"""W5-02: Bounded Agent Orchestrator Loop (Plan-Act-Observe State Machine).

Executes a stateful multi-step Plan-Act-Observe workflow over ``ToolDispatcher``
and ``LoopBreakerGuardrail``, enforcing a strict 4-iteration ceiling and writing
audit traces to ``evidence/traces/agent_loop.jsonl``.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from src.agent.guardrails import (
    GuardrailConfig,
    GuardrailDecision,
    LoopBreakerGuardrail,
)
from src.core.dispatcher import ToolDispatcher, ToolTelemetryRecord

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AGENT_LOG = PROJECT_ROOT / "evidence" / "traces" / "agent_loop.jsonl"


class AgentState(str, Enum):
    """Explicit states in the Plan-Act-Observe orchestration graph."""

    INTAKE = "INTAKE"
    PLAN = "PLAN"
    ACT = "ACT"
    OBSERVE = "OBSERVE"
    RESPOND = "RESPOND"
    FALLBACK_TERMINATED = "FALLBACK_TERMINATED"


@dataclass
class AgentStepTrace:
    """Single state-machine transition and Plan-Act-Observe step trace."""

    iteration: int
    state: str
    plan_thought: str
    action_tool: str | None = None
    action_args: dict[str, Any] | None = None
    observation_summary: str | None = None
    latency_ms: float = 0.0
    guardrail_decision: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OrchestratorRunResult:
    """Complete execution trace returned by ``AgentOrchestrator.run``."""

    run_id: str
    session_id: str
    user_query: str
    final_state: str
    terminated_by_guardrail: bool
    termination_reason: str
    iterations_used: int
    final_answer: str
    citations: list[str] = field(default_factory=list)
    state_transitions: list[str] = field(default_factory=list)
    steps: list[AgentStepTrace] = field(default_factory=list)
    tool_traces: list[ToolTelemetryRecord] = field(default_factory=list)
    total_latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["steps"] = [s.to_dict() for s in self.steps]
        payload["tool_traces"] = [t.to_dict() for t in self.tool_traces]
        return payload


PlannerFn = Callable[[list[dict[str, Any]], int], dict[str, Any]]


class AgentOrchestrator:
    """Stateful Plan-Act-Observe orchestrator with hard 4-iteration guardrails.

    Parameters
    ----------
    dispatcher:
        ``ToolDispatcher`` used in the ``ACT`` state.
    guardrail_config:
        ``GuardrailConfig`` (defaults to ``max_iterations=4``).
    planner:
        Callable ``planner(messages, iteration) -> dict`` returning either:
        - ``{"thought": str, "action": {"tool_name": str, "arguments": dict}, "tokens": int}``
        - ``{"thought": str, "final_answer": str, "citations": list[str], "tokens": int}``
        If omitted, a default policy-first planner is used that searches Makerere
        policy docs on iteration 1 and synthesizes a cited response on iteration 2.
    log_path:
        JSONL trace file path for bounded execution proof.
    """

    def __init__(
        self,
        dispatcher: ToolDispatcher | None = None,
        guardrail_config: GuardrailConfig | None = None,
        planner: PlannerFn | None = None,
        log_path: Path | None = DEFAULT_AGENT_LOG,
    ) -> None:
        self.dispatcher = dispatcher or ToolDispatcher()
        self.guardrail_config = guardrail_config or GuardrailConfig()
        self.planner = planner or self._default_policy_planner
        self.log_path = Path(log_path) if log_path else None

    def _default_policy_planner(
        self,
        messages: list[dict[str, Any]],
        iteration: int,
    ) -> dict[str, Any]:
        """Deterministic fallback planner when no external LLM planner is injected."""
        user_query = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        if not tool_msgs:
            return {
                "thought": "Retrieve relevant Makerere University policy chunks first.",
                "action": {
                    "tool_name": "search_policy_docs",
                    "arguments": {"query": user_query, "top_k": 3},
                },
            }

        last_obs = tool_msgs[-1].get("observation") or {}
        citations = list(last_obs.get("citations") or [])
        context = str(last_obs.get("formatted_context") or "").strip()
        if not context or not citations:
            return {
                "thought": "No grounded policy chunks matched the student query.",
                "final_answer": (
                    "I could not find a verified Makerere University policy section "
                    "matching your request. Please consult your College Registrar."
                ),
                "citations": [],
            }

        return {
            "thought": f"Synthesize grounded answer using retrieved citations {citations}.",
            "final_answer": (
                f"According to official Makerere University policy:\n{context}\n\n"
                f"Sources: {', '.join(citations)}"
            ),
            "citations": citations,
        }

    def run(
        self,
        user_query: str,
        session_id: str | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> OrchestratorRunResult:
        """Execute the Plan-Act-Observe state machine for a single user turn."""
        started = time.perf_counter()
        run_id = str(uuid.uuid4())
        active_session = session_id or f"sess-{run_id[:8]}"
        guardrail = LoopBreakerGuardrail(self.guardrail_config)

        transitions: list[str] = [AgentState.INTAKE.value]
        steps: list[AgentStepTrace] = []
        tool_traces: list[ToolTelemetryRecord] = []
        collected_citations: list[str] = []

        messages: list[dict[str, Any]] = list(history or [])
        messages.append({"role": "user", "content": user_query})

        iteration = 0
        while True:
            iteration += 1
            elapsed = time.perf_counter() - started
            iter_check = guardrail.check_iteration(iteration, elapsed_seconds=elapsed)
            if not iter_check.allowed:
                return self._terminate_with_fallback(
                    run_id=run_id,
                    session_id=active_session,
                    user_query=user_query,
                    decision=iter_check,
                    iterations_used=iteration - 1,
                    transitions=transitions,
                    steps=steps,
                    tool_traces=tool_traces,
                    citations=collected_citations,
                    started_at=started,
                )

            # --- PLAN STATE ---
            step_started = time.perf_counter()
            transitions.append(AgentState.PLAN.value)
            plan_out = self.planner(messages, iteration)
            guardrail.record_tokens(plan_out.get("tokens"))
            thought = str(plan_out.get("thought", ""))

            if "final_answer" in plan_out and not plan_out.get("action"):
                transitions.append(AgentState.RESPOND.value)
                for cit in plan_out.get("citations") or []:
                    if cit not in collected_citations:
                        collected_citations.append(cit)
                steps.append(
                    AgentStepTrace(
                        iteration=iteration,
                        state=AgentState.RESPOND.value,
                        plan_thought=thought,
                        latency_ms=round((time.perf_counter() - step_started) * 1000.0, 3),
                        guardrail_decision=iter_check.to_dict(),
                    )
                )
                result = OrchestratorRunResult(
                    run_id=run_id,
                    session_id=active_session,
                    user_query=user_query,
                    final_state=AgentState.RESPOND.value,
                    terminated_by_guardrail=False,
                    termination_reason="completed",
                    iterations_used=iteration,
                    final_answer=str(plan_out["final_answer"]),
                    citations=collected_citations,
                    state_transitions=transitions,
                    steps=steps,
                    tool_traces=tool_traces,
                    total_latency_ms=round((time.perf_counter() - started) * 1000.0, 3),
                )
                self._append_log(result)
                return result

            # --- ACT STATE ---
            action = plan_out.get("action") or {}
            tool_name = str(action.get("tool_name") or action.get("name") or "")
            tool_args = action.get("arguments")

            call_check = guardrail.check_tool_call(iteration, tool_name, tool_args)
            if not call_check.allowed:
                steps.append(
                    AgentStepTrace(
                        iteration=iteration,
                        state=AgentState.FALLBACK_TERMINATED.value,
                        plan_thought=thought,
                        action_tool=tool_name,
                        action_args=tool_args if isinstance(tool_args, dict) else None,
                        latency_ms=round((time.perf_counter() - step_started) * 1000.0, 3),
                        guardrail_decision=call_check.to_dict(),
                    )
                )
                return self._terminate_with_fallback(
                    run_id=run_id,
                    session_id=active_session,
                    user_query=user_query,
                    decision=call_check,
                    iterations_used=iteration,
                    transitions=transitions,
                    steps=steps,
                    tool_traces=tool_traces,
                    citations=collected_citations,
                    started_at=started,
                )

            transitions.append(AgentState.ACT.value)
            record = self.dispatcher.dispatch(tool_name, tool_args)
            tool_traces.append(record)

            # --- OBSERVE STATE ---
            transitions.append(AgentState.OBSERVE.value)
            if record.status == "success" and isinstance(record.output, dict):
                observation = record.output
                for cit in observation.get("citations") or []:
                    if cit not in collected_citations:
                        collected_citations.append(cit)
                obs_summary = f"status=success hits={observation.get('total_hits', 'n/a')}"
            else:
                observation = {
                    "status": record.status,
                    "error_message": record.error_message,
                }
                obs_summary = f"status={record.status} error={record.error_message}"

            messages.append(
                {
                    "role": "tool",
                    "tool_name": tool_name,
                    "status": record.status,
                    "observation": observation,
                }
            )
            steps.append(
                AgentStepTrace(
                    iteration=iteration,
                    state=AgentState.OBSERVE.value,
                    plan_thought=thought,
                    action_tool=tool_name,
                    action_args=tool_args if isinstance(tool_args, dict) else None,
                    observation_summary=obs_summary,
                    latency_ms=round((time.perf_counter() - step_started) * 1000.0, 3),
                    guardrail_decision=call_check.to_dict(),
                )
            )

    def _terminate_with_fallback(
        self,
        *,
        run_id: str,
        session_id: str,
        user_query: str,
        decision: GuardrailDecision,
        iterations_used: int,
        transitions: list[str],
        steps: list[AgentStepTrace],
        tool_traces: list[ToolTelemetryRecord],
        citations: list[str],
        started_at: float,
    ) -> OrchestratorRunResult:
        transitions.append(AgentState.FALLBACK_TERMINATED.value)
        result = OrchestratorRunResult(
            run_id=run_id,
            session_id=session_id,
            user_query=user_query,
            final_state=AgentState.FALLBACK_TERMINATED.value,
            terminated_by_guardrail=True,
            termination_reason=decision.reason,
            iterations_used=iterations_used,
            final_answer=decision.fallback_notice or "",
            citations=citations,
            state_transitions=transitions,
            steps=steps,
            tool_traces=tool_traces,
            total_latency_ms=round((time.perf_counter() - started_at) * 1000.0, 3),
        )
        self._append_log(result)
        return result

    def _append_log(self, result: OrchestratorRunResult) -> None:
        if self.log_path is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            **result.to_dict(),
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
