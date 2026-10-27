"""Chat and agent orchestration API endpoint."""

from __future__ import annotations

import time
import uuid
from fastapi import APIRouter

from src.agent.orchestrator import AgentOrchestrator
from src.safety.guardrails import InjectionDefenseGuardrail
from src.safety.refusal_engine import NonNegotiableRefusalEngine
from src.schemas.api import ChatRequest, ChatResponse

router = APIRouter(tags=["Chat & Agent"])

_guardrail = InjectionDefenseGuardrail()
_refusal_engine = NonNegotiableRefusalEngine(guardrail=_guardrail)
_orchestrator = AgentOrchestrator()


@router.post("/chat", response_model=ChatResponse)
def handle_chat_query(payload: ChatRequest) -> ChatResponse:
    """Submit a query to the Makerere Student Support Triage Agent."""
    start_time = time.perf_counter()
    session_id = payload.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    # Step 1: Pre-inference Institutional Refusal Boundary check
    refusal = _refusal_engine.evaluate(payload.query)
    if refusal.refused:
        latency = (time.perf_counter() - start_time) * 1000.0
        return ChatResponse(
            status="refused",
            query=payload.query,
            response=refusal.refusal_response or "Request refused under Makerere University policy.",
            citations=[],
            session_id=session_id,
            state="INSTITUTIONAL_REFUSAL",
            iterations=0,
            latency_ms=round(latency, 2),
            escalation_office=refusal.escalation_office,
            safety_category=refusal.category,
        )

    # Step 2: Adversarial & Injection Safety Check
    safety_check = _guardrail.inspect_input(payload.query)
    if not safety_check.allowed:
        latency = (time.perf_counter() - start_time) * 1000.0
        return ChatResponse(
            status="refused",
            query=payload.query,
            response=safety_check.refusal_message or "Request blocked by safety guardrails.",
            citations=[],
            session_id=session_id,
            state="SAFETY_BLOCKED",
            iterations=0,
            latency_ms=round(latency, 2),
            escalation_office="DICTS Security & Academic Registrar Helpdesk",
            safety_category=safety_check.category,
        )

    # Step 3: Bounded Plan-Act-Observe Execution Loop
    run_result = _orchestrator.run(
        user_query=payload.query,
        session_id=session_id,
    )

    # Step 4: Post-inference Output Leak Scanning
    output_check = _guardrail.inspect_output(run_result.final_answer)
    answer = run_result.final_answer
    if not output_check.allowed:
        answer = output_check.sanitized_output or output_check.refusal_message or answer

    latency = (time.perf_counter() - start_time) * 1000.0
    return ChatResponse(
        status="success" if not run_result.terminated_by_guardrail else "fallback",
        query=payload.query,
        response=answer,
        citations=run_result.citations,
        session_id=session_id,
        state=run_result.final_state,
        iterations=run_result.iterations_used,
        latency_ms=round(latency, 2),
        escalation_office=None,
        safety_category="SAFE",
    )
