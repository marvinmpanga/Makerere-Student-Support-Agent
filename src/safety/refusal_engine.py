"""W6-04: Non-Negotiable Refusal Engine.

Deterministic zero-tolerance policy boundary engine enforcing instant, polite
refusals whenever a user requests unauthorized administrative actions (grade/mark
alteration, fee waiver, transcript tampering, disciplinary override, or third-party
PII disclosure) or out-of-scope commercial/medical/legal advice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.safety.guardrails import (
    InjectionDefenseGuardrail,
    SafetyCategory,
    SafetyCheckResult,
)


@dataclass(frozen=True)
class RefusalDecision:
    """Structured refusal decision returned by ``NonNegotiableRefusalEngine``."""

    refused: bool
    policy_code: str
    category: str
    refusal_response: str | None
    escalation_office: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ESCALATION_MAP: dict[str, str] = {
    SafetyCategory.UNAUTHORIZED_MUTATION.value: "Office of the Academic Registrar / University Bursar",
    SafetyCategory.PRIVILEGE_ESCALATION.value: "DICTS Security & Academic Registrar Helpdesk",
    SafetyCategory.PROMPT_INJECTION.value: "System Security Monitor",
    SafetyCategory.JAILBREAK_ROLEPLAY.value: "System Security Monitor",
    SafetyCategory.SYSTEM_PROMPT_EXTRACTION.value: "System Security Monitor",
    SafetyCategory.DELIMITER_ESCAPE.value: "System Security Monitor",
    SafetyCategory.OBFUSCATED_PAYLOAD.value: "System Security Monitor",
}


class NonNegotiableRefusalEngine:
    """Enforces zero-tolerance institutional refusal boundaries with audit logging."""

    def __init__(self, guardrail: InjectionDefenseGuardrail | None = None) -> None:
        self.guardrail = guardrail or InjectionDefenseGuardrail()

    def evaluate(self, user_query: str) -> RefusalDecision:
        check: SafetyCheckResult = self.guardrail.inspect_input(user_query)
        if not check.allowed:
            office = ESCALATION_MAP.get(check.category, "College Registrar Helpdesk")
            return RefusalDecision(
                refused=True,
                policy_code=check.rule_id or "REF-001",
                category=check.category,
                refusal_response=check.refusal_message,
                escalation_office=office,
            )

        return RefusalDecision(
            refused=False,
            policy_code="ALLOW",
            category=SafetyCategory.SAFE.value,
            refusal_response=None,
            escalation_office=None,
        )
