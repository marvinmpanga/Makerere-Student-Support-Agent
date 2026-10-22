"""W4-05: LLM Tool Dispatcher & Telemetry Loop.

Intercepts LLM tool invocation requests, validates parameters against strict
Pydantic schemas, executes registered deterministic Python functions, logs
per-invocation telemetry, and feeds structured observations back into the model
context window without crashing on malformed or hallucinated arguments.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from src.tools.policy_search import PolicySearchArgs, search_policy_docs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TELEMETRY_LOG = PROJECT_ROOT / "evidence" / "traces" / "tool_dispatch.jsonl"


@dataclass
class ToolSpecification:
    """Binds a tool name to its Pydantic input schema and callable handler."""

    name: str
    description: str
    args_schema: type[BaseModel]
    handler: Callable[..., Any]


@dataclass
class ToolTelemetryRecord:
    """Telemetry record emitted for every tool dispatch attempt."""

    dispatch_id: str
    timestamp_utc: str
    tool_name: str
    status: str  # "success" | "validation_error" | "unknown_tool" | "execution_error"
    latency_ms: float
    arguments: dict[str, Any]
    output: dict[str, Any] | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DispatchLoopResult:
    """Result of a bounded LLM -> Tool -> Observation execution loop."""

    status: str
    final_response: str
    iterations: int
    tool_traces: list[ToolTelemetryRecord] = field(default_factory=list)
    structured_output: dict[str, Any] | None = None


class ToolDispatcher:
    """Registry, validator, executor, and telemetry logger for bounded LLM tools."""

    def __init__(
        self,
        telemetry_log_path: Path | None = DEFAULT_TELEMETRY_LOG,
        register_defaults: bool = True,
    ) -> None:
        self._registry: dict[str, ToolSpecification] = {}
        self.telemetry_log_path = Path(telemetry_log_path) if telemetry_log_path else None
        self.history: list[ToolTelemetryRecord] = []
        if register_defaults:
            self._register_default_tools()

    def _register_default_tools(self) -> None:
        self.register(
            ToolSpecification(
                name="search_policy_docs",
                description=(
                    "Search official Makerere University policy documents in ChromaDB "
                    "and return grounded excerpts with [Doc_ID, Page N] citations."
                ),
                args_schema=PolicySearchArgs,
                handler=lambda **kwargs: search_policy_docs(**kwargs).model_dump(),
            )
        )

    def register(self, spec: ToolSpecification) -> None:
        """Register or replace a tool specification."""
        self._registry[spec.name] = spec

    @property
    def registered_tools(self) -> list[str]:
        return sorted(self._registry.keys())

    def tool_schemas(self) -> list[dict[str, Any]]:
        """Export JSON schemas for all registered tools for LLM function-calling."""
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "parameters": spec.args_schema.model_json_schema(),
            }
            for spec in self._registry.values()
        ]

    def dispatch(
        self,
        tool_name: str,
        raw_arguments: dict[str, Any] | str | None,
    ) -> ToolTelemetryRecord:
        """Validate arguments, invoke the targeted tool, and log telemetry.

        Never raises on unknown tools, invalid JSON, or Pydantic validation errors;
        instead returns a structured ``ToolTelemetryRecord`` so the LLM loop can
        recover gracefully.
        """
        started = time.perf_counter()
        dispatch_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        parsed_args: dict[str, Any]
        if raw_arguments is None:
            parsed_args = {}
        elif isinstance(raw_arguments, str):
            try:
                loaded = json.loads(raw_arguments)
                if not isinstance(loaded, dict):
                    return self._finalize(
                        ToolTelemetryRecord(
                            dispatch_id=dispatch_id,
                            timestamp_utc=now_iso,
                            tool_name=tool_name,
                            status="validation_error",
                            latency_ms=(time.perf_counter() - started) * 1000.0,
                            arguments={"raw": raw_arguments},
                            error_message="Tool arguments JSON must decode to an object.",
                        )
                    )
                parsed_args = loaded
            except json.JSONDecodeError as exc:
                return self._finalize(
                    ToolTelemetryRecord(
                        dispatch_id=dispatch_id,
                        timestamp_utc=now_iso,
                        tool_name=tool_name,
                        status="validation_error",
                        latency_ms=(time.perf_counter() - started) * 1000.0,
                        arguments={"raw": raw_arguments},
                        error_message=f"Malformed JSON tool arguments: {exc}",
                    )
                )
        elif isinstance(raw_arguments, dict):
            parsed_args = dict(raw_arguments)
        else:
            return self._finalize(
                ToolTelemetryRecord(
                    dispatch_id=dispatch_id,
                    timestamp_utc=now_iso,
                    tool_name=tool_name,
                    status="validation_error",
                    latency_ms=(time.perf_counter() - started) * 1000.0,
                    arguments={"raw": str(raw_arguments)},
                    error_message=f"Unsupported argument container: {type(raw_arguments).__name__}",
                )
            )

        spec = self._registry.get(tool_name)
        if spec is None:
            return self._finalize(
                ToolTelemetryRecord(
                    dispatch_id=dispatch_id,
                    timestamp_utc=now_iso,
                    tool_name=tool_name,
                    status="unknown_tool",
                    latency_ms=(time.perf_counter() - started) * 1000.0,
                    arguments=parsed_args,
                    error_message=(
                        f"Tool '{tool_name}' is not registered. "
                        f"Allowed tools: {self.registered_tools}"
                    ),
                )
            )

        try:
            validated = spec.args_schema(**parsed_args)
        except ValidationError as exc:
            return self._finalize(
                ToolTelemetryRecord(
                    dispatch_id=dispatch_id,
                    timestamp_utc=now_iso,
                    tool_name=tool_name,
                    status="validation_error",
                    latency_ms=(time.perf_counter() - started) * 1000.0,
                    arguments=parsed_args,
                    error_message=f"Schema validation failed for '{tool_name}': {exc}",
                )
            )

        try:
            clean_kwargs = validated.model_dump()
            raw_output = spec.handler(**clean_kwargs)
            output_dict = (
                raw_output.model_dump()
                if isinstance(raw_output, BaseModel)
                else (raw_output if isinstance(raw_output, dict) else {"result": raw_output})
            )
            return self._finalize(
                ToolTelemetryRecord(
                    dispatch_id=dispatch_id,
                    timestamp_utc=now_iso,
                    tool_name=tool_name,
                    status="success",
                    latency_ms=(time.perf_counter() - started) * 1000.0,
                    arguments=clean_kwargs,
                    output=output_dict,
                )
            )
        except Exception as exc:  # noqa: BLE001 - non-blocking tool failure handling
            return self._finalize(
                ToolTelemetryRecord(
                    dispatch_id=dispatch_id,
                    timestamp_utc=now_iso,
                    tool_name=tool_name,
                    status="execution_error",
                    latency_ms=(time.perf_counter() - started) * 1000.0,
                    arguments=parsed_args,
                    error_message=f"Tool '{tool_name}' raised {type(exc).__name__}: {exc}",
                )
            )

    def run_loop(
        self,
        llm_step: Callable[[list[dict[str, Any]]], dict[str, Any]],
        user_query: str,
        max_iterations: int = 4,
    ) -> DispatchLoopResult:
        """Execute a bounded LLM -> Tool -> Observation loop.

        ``llm_step(messages)`` receives the conversation transcript so far and returns
        either:
        - ``{"tool_call": {"name": str, "arguments": dict}}`` to invoke a tool, or
        - ``{"final_answer": str, "structured_output": dict | None}`` to finish.
        """
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_query}]
        traces: list[ToolTelemetryRecord] = []

        for iteration in range(1, max_iterations + 1):
            step = llm_step(messages)
            tool_call = step.get("tool_call")
            if not tool_call:
                return DispatchLoopResult(
                    status="completed",
                    final_response=str(step.get("final_answer", "")),
                    iterations=iteration,
                    tool_traces=traces,
                    structured_output=step.get("structured_output"),
                )

            name = str(tool_call.get("name", ""))
            args = tool_call.get("arguments")
            record = self.dispatch(name, args)
            traces.append(record)

            observation = (
                record.output
                if record.status == "success"
                else {"status": record.status, "error": record.error_message}
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_name": name,
                    "status": record.status,
                    "observation": observation,
                }
            )

        return DispatchLoopResult(
            status="max_iterations_exceeded",
            final_response=(
                "Unable to complete request within the maximum allowed tool iterations "
                f"({max_iterations}). Please escalate to a human support officer."
            ),
            iterations=max_iterations,
            tool_traces=traces,
        )

    def _finalize(self, record: ToolTelemetryRecord) -> ToolTelemetryRecord:
        record.latency_ms = round(record.latency_ms, 3)
        self.history.append(record)
        if self.telemetry_log_path is not None:
            self.telemetry_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.telemetry_log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        return record
