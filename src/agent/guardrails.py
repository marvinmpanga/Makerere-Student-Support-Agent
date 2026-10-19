"""W5-04: Max-Iteration Guardrails & Loop Breaker.

Enforces explicit execution boundaries on multi-step agent loops to prevent
runaway iterations, duplicate tool-call cycles, high latency, or excessive
token consumption. Emits deterministic fallback notices whenever a hard bound
is reached.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

MAX_AGENT_ITERATIONS = 4

FALLBACK_MAX_ITERATIONS_NOTICE = (
    "Notice: Automated processing reached the maximum execution boundary of "
    f"{MAX_AGENT_ITERATIONS} iterations without finalizing a verified answer. "
    "To prevent inaccurate guidance, this session has been halted. Please "
    "visit the Makerere College Registrar or Student Affairs Helpdesk."
)

FALLBACK_REPEATED_CALL_NOTICE = (
    "Notice: The assistant detected a repeated tool invocation cycle and halted "
    "execution to prevent a runaway loop. Please refine your question or contact "
    "the relevant Makerere University support office directly."
)

FALLBACK_TIMEOUT_NOTICE = (
    "Notice: Processing exceeded the maximum allowed response latency budget. "
    "Please retry your inquiry or escalate to the Student Support Helpdesk."
)

FALLBACK_TOKEN_BUDGET_NOTICE = (
    "Notice: Session token budget reached. Please start a new inquiry or "
    "escalate complex case documentation directly to your Faculty Registrar."
)


@dataclass(frozen=True)
class GuardrailConfig:
    """Configuration thresholds for bounded agent execution."""

    max_iterations: int = MAX_AGENT_ITERATIONS
    max_identical_tool_calls: int = 2
    max_elapsed_seconds: float = 30.0
    max_total_tokens: int = 8192


@dataclass
class GuardrailDecision:
    """Result of evaluating execution guardrails at a loop boundary."""

    allowed: bool
    reason: str = "ok"
    fallback_notice: str | None = None
    iteration: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_call_signature(tool_name: str, arguments: dict[str, Any] | str | None) -> str:
    if isinstance(arguments, dict):
        serialized = json.dumps(arguments, sort_keys=True, default=str)
    else:
        serialized = str(arguments or "")
    digest = hashlib.sha256(f"{tool_name}:{serialized}".encode("utf-8")).hexdigest()[:16]
    return f"{tool_name}:{digest}"


class LoopBreakerGuardrail:
    """Tracks per-run iteration count, tool call signatures, latency, and tokens."""

    def __init__(self, config: GuardrailConfig | None = None) -> None:
        self.config = config or GuardrailConfig()
        self._call_counts: dict[str, int] = {}
        self._total_tokens: int = 0

    def reset(self) -> None:
        self._call_counts.clear()
        self._total_tokens = 0

    def record_tokens(self, tokens: int | None) -> None:
        if isinstance(tokens, int) and tokens > 0:
            self._total_tokens += tokens

    def check_iteration(
        self,
        iteration: int,
        elapsed_seconds: float = 0.0,
    ) -> GuardrailDecision:
        """Check whether the orchestrator may enter ``iteration`` (1-indexed)."""
        if iteration > self.config.max_iterations:
            return GuardrailDecision(
                allowed=False,
                reason="max_iterations_reached",
                fallback_notice=FALLBACK_MAX_ITERATIONS_NOTICE,
                iteration=iteration,
                metadata={"max_iterations": self.config.max_iterations},
            )

        if elapsed_seconds > self.config.max_elapsed_seconds:
            return GuardrailDecision(
                allowed=False,
                reason="latency_budget_exceeded",
                fallback_notice=FALLBACK_TIMEOUT_NOTICE,
                iteration=iteration,
                metadata={
                    "elapsed_seconds": round(elapsed_seconds, 3),
                    "max_elapsed_seconds": self.config.max_elapsed_seconds,
                },
            )

        if self._total_tokens > self.config.max_total_tokens:
            return GuardrailDecision(
                allowed=False,
                reason="token_budget_exceeded",
                fallback_notice=FALLBACK_TOKEN_BUDGET_NOTICE,
                iteration=iteration,
                metadata={
                    "total_tokens": self._total_tokens,
                    "max_total_tokens": self.config.max_total_tokens,
                },
            )

        return GuardrailDecision(allowed=True, iteration=iteration)

    def check_tool_call(
        self,
        iteration: int,
        tool_name: str,
        arguments: dict[str, Any] | str | None,
    ) -> GuardrailDecision:
        """Detect repeated identical tool invocations within the same turn."""
        signature = _canonical_call_signature(tool_name, arguments)
        count = self._call_counts.get(signature, 0) + 1
        self._call_counts[signature] = count

        if count >= self.config.max_identical_tool_calls:
            return GuardrailDecision(
                allowed=False,
                reason="repeated_tool_call_cycle",
                fallback_notice=FALLBACK_REPEATED_CALL_NOTICE,
                iteration=iteration,
                metadata={
                    "tool_name": tool_name,
                    "signature": signature,
                    "call_count": count,
                },
            )

        return GuardrailDecision(
            allowed=True,
            iteration=iteration,
            metadata={"tool_name": tool_name, "signature": signature, "call_count": count},
        )
