"""W2-04: Baseline LLM execution harness and structured telemetry logging.

Executes user stories or ad-hoc queries against ``GeminiBaselineClient`` (or an
injected/offline client for deterministic tests), validates structured JSON
responses, and appends structured execution traces to ``evidence/traces/``.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "prompts" / "v1.0" / "system_prompt.md"
DEFAULT_LOG_PATH = PROJECT_ROOT / "evidence" / "traces" / "baseline_runs.jsonl"


class LLMClientProtocol(Protocol):
    def generate_response(
        self,
        system_instruction: str,
        user_query: str,
        context_documents: str | None = None,
        force_json: bool = False,
    ) -> dict[str, Any]: ...


@dataclass
class ExecutionTrace:
    request_id: str
    timestamp_utc: str
    case_id: str
    prompt_version: str
    model: str
    status: str
    latency_seconds: float
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    user_query: str
    response_text: str
    structured_output: dict[str, Any] | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaselineExecutionHarness:
    """Runs baseline prompts through the LLM client and logs JSONL telemetry."""

    def __init__(
        self,
        client: LLMClientProtocol | None = None,
        system_prompt_path: Path = DEFAULT_PROMPT_PATH,
        prompt_version: str = "v1.0",
        log_path: Path = DEFAULT_LOG_PATH,
    ) -> None:
        self._client = client
        self.system_prompt_path = Path(system_prompt_path)
        self.prompt_version = prompt_version
        self.log_path = Path(log_path)

    def _get_client(self) -> LLMClientProtocol:
        if self._client is None:
            from src.core.llm import GeminiBaselineClient

            self._client = GeminiBaselineClient()
        return self._client

    def load_system_prompt(self) -> str:
        if self.system_prompt_path.is_file():
            return self.system_prompt_path.read_text(encoding="utf-8")
        return "You are the Makerere University Student Support & Onboarding Triage Agent."

    def run_case(
        self,
        user_query: str,
        case_id: str = "ad-hoc",
        context_documents: str | None = None,
        force_json: bool = True,
    ) -> ExecutionTrace:
        started = time.perf_counter()
        system_instruction = self.load_system_prompt()
        raw = self._get_client().generate_response(
            system_instruction=system_instruction,
            user_query=user_query,
            context_documents=context_documents,
            force_json=force_json,
        )
        elapsed = raw.get("latency_seconds") or (time.perf_counter() - started)
        usage = raw.get("raw_usage") or {}
        p_tok = usage.get("prompt_token_count")
        c_tok = usage.get("candidates_token_count")
        total = (p_tok + c_tok) if (isinstance(p_tok, int) and isinstance(c_tok, int)) else None

        trace = ExecutionTrace(
            request_id=str(uuid.uuid4()),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            case_id=case_id,
            prompt_version=self.prompt_version,
            model=str(raw.get("model", "gemini-1.5-flash")),
            status=str(raw.get("status", "error")),
            latency_seconds=round(float(elapsed), 4),
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=total,
            user_query=user_query,
            response_text=str(raw.get("response_text", "")),
            structured_output=raw.get("structured_output"),
            error_message=raw.get("error_message"),
        )
        self._append_log(trace)
        return trace

    def run_suite(
        self,
        cases: list[dict[str, Any]],
        force_json: bool = True,
    ) -> list[ExecutionTrace]:
        return [
            self.run_case(
                user_query=case["query"],
                case_id=case.get("case_id", f"US-{idx:02d}"),
                context_documents=case.get("context"),
                force_json=force_json,
            )
            for idx, case in enumerate(cases, start=1)
        ]

    def _append_log(self, trace: ExecutionTrace) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
