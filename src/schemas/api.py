"""Pydantic schemas for REST API endpoints."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Student chat request payload."""

    query: str = Field(..., min_length=1, max_length=2000, description="Student inquiry text")
    session_id: str | None = Field(default=None, description="Optional conversation session ID")
    student_id: str | None = Field(default=None, description="Optional verified student ID")


class ChatResponse(BaseModel):
    """Structured response from the student support agent."""

    status: str = Field(..., description="'success' | 'refused' | 'fallback'")
    query: str
    response: str
    citations: list[str] = Field(default_factory=list)
    session_id: str
    state: str
    iterations: int
    latency_ms: float
    escalation_office: str | None = None
    safety_category: str | None = None


class PolicySearchRequest(BaseModel):
    """Request payload for searching Makerere University policies."""

    query: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)
    category: str | None = Field(default=None)


class PolicyHitItem(BaseModel):
    """Individual policy search excerpt hit."""

    doc_id: str
    citation: str
    title: str | None = None
    category: str | None = None
    score: float = 0.0
    text_snippet: str = ""


class PolicySearchResponse(BaseModel):
    """Structured result of policy search."""

    status: str
    total_hits: int
    citations: list[str] = Field(default_factory=list)
    hits: list[PolicyHitItem] = Field(default_factory=list)
    formatted_context: str = ""


class StudentStatusResponse(BaseModel):
    """Read-only student status record."""

    student_id: str
    name: str = "Demo Student"
    program: str = "Bachelor of Science in Software Engineering (BSSE)"
    college: str = "College of Computing and Information Sciences (CoCIS)"
    year_of_study: int = 4
    status: str = "Enrolled"
    financial_hold: bool = False
    academic_warning: bool = False


class TicketDraftRequest(BaseModel):
    """Request to draft an administrative support ticket."""

    student_id: str = Field(..., min_length=1)
    issue_category: str = Field(..., min_length=2)
    issue_description: str = Field(..., min_length=5)
    priority: str = Field(default="Normal")


class TicketDraftResponse(BaseModel):
    """Drafted ticket awaiting student confirmation."""

    ticket_id: str
    student_id: str
    issue_category: str
    issue_description: str
    priority: str
    status: str = "Drafted"
    message: str
    student_confirmation_required: bool = True
    created_at: str


class TicketConfirmRequest(BaseModel):
    """Human-in-the-loop explicit ticket confirmation request."""

    ticket_id: str = Field(..., min_length=1)
    student_id: str = Field(..., min_length=1)
    confirmed: bool = True


class TicketConfirmResponse(BaseModel):
    """Response after human-in-the-loop ticket confirmation."""

    ticket_id: str
    student_id: str
    status: str  # "Submitted" | "Cancelled"
    message: str
    dispatched_to: str | None = None
    confirmed_at: str


class EvaluationMetricsResponse(BaseModel):
    """Empirical evaluation benchmarks."""

    mean_reciprocal_rank: float
    precision_at_3: float
    hit_rate: float
    citation_compliance_rate: float
    safety_refusal_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    scenarios_evaluated: int
    raw_details: dict[str, Any] = Field(default_factory=dict)
