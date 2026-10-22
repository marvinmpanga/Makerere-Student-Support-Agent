"""W6-03: Injection & Jailbreak Defense Layer.

Provides pre-inference input sanitization, adversarial prompt-injection and
jailbreak detection, non-negotiable Makerere institutional boundary enforcement
(blocking grade/fee/record manipulation), post-inference output leak scanning,
and structured audit logging to ``evidence/traces/safety_audit.jsonl``.
"""

from __future__ import annotations

import base64
import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAFETY_LOG = PROJECT_ROOT / "evidence" / "traces" / "safety_audit.jsonl"

MAX_INPUT_LENGTH = 2000


class SafetyCategory(str, Enum):
    """Taxonomy of adversarial or policy-violating inputs."""

    SAFE = "SAFE"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    JAILBREAK_ROLEPLAY = "JAILBREAK_ROLEPLAY"
    SYSTEM_PROMPT_EXTRACTION = "SYSTEM_PROMPT_EXTRACTION"
    DELIMITER_ESCAPE = "DELIMITER_ESCAPE"
    OBFUSCATED_PAYLOAD = "OBFUSCATED_PAYLOAD"
    UNAUTHORIZED_MUTATION = "UNAUTHORIZED_MUTATION"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    OUTPUT_LEAKAGE = "OUTPUT_LEAKAGE"
    INPUT_TOO_LONG = "INPUT_TOO_LONG"


@dataclass(frozen=True)
class ThreatRule:
    """Compiled regex signature for deterministic threat detection."""

    rule_id: str
    category: SafetyCategory
    severity: str  # "critical" | "high" | "medium"
    pattern: re.Pattern[str]
    refusal_message: str


REFUSAL_PROMPT_INJECTION = (
    "I cannot fulfill this request. Attempts to override system instructions or "
    "bypass safety boundaries are not permitted. I can only assist with verified "
    "Makerere University student support and policy inquiries."
)

REFUSAL_SYSTEM_EXTRACTION = (
    "I cannot disclose internal system prompts, hidden configurations, or "
    "developer instructions. How can I help you with Makerere University "
    "academic or onboarding policies?"
)

REFUSAL_UNAUTHORIZED_MUTATION = (
    "I cannot modify grades, alter examination results, waive tuition fees, or "
    "change official student records. The Makerere Student Support Agent has "
    "strictly read-only access and can only guide you through official "
    "Academic Registrar or College procedures."
)

REFUSAL_PRIVILEGE_ESCALATION = (
    "I cannot assume administrative privileges, bypass Human-in-the-Loop (HITL) "
    "ticket confirmation, or access another student's private records."
)

DEFAULT_THREAT_RULES: tuple[ThreatRule, ...] = (
    ThreatRule(
        rule_id="INJ-001",
        category=SafetyCategory.PROMPT_INJECTION,
        severity="critical",
        pattern=re.compile(
            r"\b(ignore|disregard|forget|override|bypass)\b.{0,40}"
            r"\b(previous|prior|above|all|system|developer|safety)\b.{0,25}"
            r"\b(instructions?|prompts?|rules?|constraints?|guardrails?)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        refusal_message=REFUSAL_PROMPT_INJECTION,
    ),
    ThreatRule(
        rule_id="INJ-002",
        category=SafetyCategory.JAILBREAK_ROLEPLAY,
        severity="critical",
        pattern=re.compile(
            r"\b(you\s+are\s+now\s+DAN|do\s+anything\s+now|developer\s+mode|"
            r"jailbreak|unrestricted\s+mode|act\s+as\s+an?\s+unfiltered|"
            r"pretend\s+you\s+have\s+no\s+restrictions|"
            r"hypothetically\s+bypass)\b",
            re.IGNORECASE,
        ),
        refusal_message=REFUSAL_PROMPT_INJECTION,
    ),
    ThreatRule(
        rule_id="INJ-003",
        category=SafetyCategory.SYSTEM_PROMPT_EXTRACTION,
        severity="high",
        pattern=re.compile(
            r"\b(reveal|print|show|output|repeat|dump|display|verbatim)\b.{0,40}"
            r"\b(system\s+prompt|hidden\s+instructions?|developer\s+message|"
            r"initial\s+prompt|api\s+keys?|\.env)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        refusal_message=REFUSAL_SYSTEM_EXTRACTION,
    ),
    ThreatRule(
        rule_id="INJ-004",
        category=SafetyCategory.DELIMITER_ESCAPE,
        severity="high",
        pattern=re.compile(
            r"(<\s*/?\s*system\s*>|\[/?INST\]|<<\s*SYS\s*>>|"
            r"###\s*(System|Instruction)\s*:|```\s*system)",
            re.IGNORECASE,
        ),
        refusal_message=REFUSAL_PROMPT_INJECTION,
    ),
    ThreatRule(
        rule_id="MUT-001",
        category=SafetyCategory.UNAUTHORIZED_MUTATION,
        severity="critical",
        pattern=re.compile(
            r"\b(change|modify|alter|update|increase|boost|edit|delete|waive|"
            r"clear|forgive|cancel|override)\b.{0,45}"
            r"\b(my\s+|the\s+|student\s+)?"
            r"(grades?|marks?|cgpa|gpa|exam\s+results?|tuition|fees?\s+balance|"
            r"financial\s+hold|academic\s+record|transcript)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        refusal_message=REFUSAL_UNAUTHORIZED_MUTATION,
    ),
    ThreatRule(
        rule_id="ESC-001",
        category=SafetyCategory.PRIVILEGE_ESCALATION,
        severity="critical",
        pattern=re.compile(
            r"\b(i\s+am\s+the\s+(vice\s+chancellor|academic\s+registrar|"
            r"system\s+administrator|dean)|sudo\s+|grant\s+admin\s+access|"
            r"auto[-\s]?approve\s+ticket|skip\s+human\s+confirmation|"
            r"show\s+me\s+all\s+students'?|another\s+student'?s\s+results?)\b",
            re.IGNORECASE,
        ),
        refusal_message=REFUSAL_PRIVILEGE_ESCALATION,
    ),
)

_BASE64_CANDIDATE_RE = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{20,}={0,2}(?![A-Za-z0-9+/=])")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

OUTPUT_FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("LEAK-API-KEY", re.compile(r"AIza[0-9A-Za-z\-_]{20,}")),
    (
        "LEAK-SYSTEM-HEADER",
        re.compile(r"NON-NEGOTIABLE SYSTEM CONSTRAINTS|INTERNAL SYSTEM PROMPT", re.IGNORECASE),
    ),
    (
        "LEAK-MUTATION-CLAIM",
        re.compile(
            r"\bI\s+have\s+(updated|changed|modified|waived|cleared)\s+your\s+"
            r"(grade|mark|cgpa|tuition|fee\s+balance)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass
class SafetyCheckResult:
    """Outcome of inspecting a user input or model output."""

    allowed: bool
    category: str = SafetyCategory.SAFE.value
    rule_id: str | None = None
    severity: str = "none"
    sanitized_text: str = ""
    refusal_message: str | None = None
    matched_indicator: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyAuditRecord:
    """Persistent audit log entry written to ``evidence/traces/safety_audit.jsonl``."""

    audit_id: str
    timestamp_utc: str
    direction: str  # "input" | "output"
    allowed: bool
    category: str
    rule_id: str | None
    severity: str
    input_preview: str
    refusal_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InjectionDefenseGuardrail:
    """Multi-layered input/output safety guardrail and audit logger."""

    def __init__(
        self,
        rules: tuple[ThreatRule, ...] = DEFAULT_THREAT_RULES,
        max_input_length: int = MAX_INPUT_LENGTH,
        audit_log_path: Path | None = DEFAULT_SAFETY_LOG,
    ) -> None:
        self.rules = rules
        self.max_input_length = max_input_length
        self.audit_log_path = Path(audit_log_path) if audit_log_path else None
        self.audit_trail: list[SafetyAuditRecord] = []

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Strip null/control characters and normalize whitespace."""
        cleaned = _CONTROL_CHARS_RE.sub("", text or "")
        return re.sub(r"\s+", " ", cleaned).strip()

    def _decode_obfuscated_segments(self, text: str) -> list[str]:
        """Decode suspicious Base64 tokens so encoded injections are caught."""
        decoded_segments: list[str] = []
        for match in _BASE64_CANDIDATE_RE.finditer(text):
            token = match.group(0)
            if len(token) % 4 != 0:
                continue
            try:
                raw = base64.b64decode(token, validate=True)
                decoded = raw.decode("utf-8", errors="ignore")
                if decoded and sum(c.isprintable() for c in decoded) / len(decoded) > 0.85:
                    decoded_segments.append(decoded)
            except Exception:  # noqa: BLE001
                continue
        return decoded_segments

    def inspect_input(self, user_input: str) -> SafetyCheckResult:
        """Validate and scan incoming student input before LLM or tool execution."""
        sanitized = self.sanitize_text(user_input)

        if len(sanitized) > self.max_input_length:
            res = SafetyCheckResult(
                allowed=False,
                category=SafetyCategory.INPUT_TOO_LONG.value,
                rule_id="LEN-001",
                severity="medium",
                sanitized_text=sanitized[: self.max_input_length],
                refusal_message=(
                    f"Input exceeds the maximum allowed length of {self.max_input_length} "
                    "characters. Please submit a concise student support question."
                ),
            )
            self._log_audit("input", sanitized, res)
            return res

        # Scan both the raw sanitized text and any Base64-decoded payload segments.
        decoded_payloads = self._decode_obfuscated_segments(sanitized)
        surfaces = [sanitized, *decoded_payloads]

        for idx, surface in enumerate(surfaces):
            for rule in self.rules:
                match = rule.pattern.search(surface)
                if match:
                    cat = (
                        SafetyCategory.OBFUSCATED_PAYLOAD.value
                        if idx > 0
                        else rule.category.value
                    )
                    res = SafetyCheckResult(
                        allowed=False,
                        category=cat,
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        sanitized_text=sanitized,
                        refusal_message=rule.refusal_message,
                        metadata={
                            "matched_span": match.group(0)[:80],
                            "obfuscated": idx > 0,
                        },
                    )
                    self._log_audit("input", sanitized, res)
                    return res

        res = SafetyCheckResult(
            allowed=True,
            category=SafetyCategory.SAFE.value,
            sanitized_text=sanitized,
        )
        self._log_audit("input", sanitized, res)
        return res

    def inspect_output(self, model_output: str) -> SafetyCheckResult:
        """Scan LLM output to prevent secret leakage or unauthorized mutation claims."""
        text = model_output or ""
        for rule_id, pattern in OUTPUT_FORBIDDEN_PATTERNS:
            match = pattern.search(text)
            if match:
                res = SafetyCheckResult(
                    allowed=False,
                    category=SafetyCategory.OUTPUT_LEAKAGE.value,
                    rule_id=rule_id,
                    severity="critical",
                    sanitized_text=REFUSAL_UNAUTHORIZED_MUTATION,
                    refusal_message=REFUSAL_UNAUTHORIZED_MUTATION,
                    metadata={"matched_span": match.group(0)[:80]},
                )
                self._log_audit("output", text, res)
                return res

        return SafetyCheckResult(
            allowed=True,
            category=SafetyCategory.SAFE.value,
            sanitized_text=text,
        )

    def _log_audit(self, direction: str, raw_text: str, result: SafetyCheckResult) -> None:
        record = SafetyAuditRecord(
            audit_id=str(uuid.uuid4()),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            direction=direction,
            allowed=result.allowed,
            category=result.category,
            rule_id=result.rule_id,
            severity=result.severity,
            input_preview=raw_text[:160],
            refusal_message=result.refusal_message,
        )
        self.audit_trail.append(record)
        if self.audit_log_path is not None:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
