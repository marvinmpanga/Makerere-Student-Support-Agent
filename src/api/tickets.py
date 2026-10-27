"""Student status, ticket drafting, and human-in-the-loop confirmation endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, HTTPException

from src.core.tools import MOCK_STUDENT_DB, PENDING_TICKETS
from src.schemas.api import (
    StudentStatusResponse,
    TicketConfirmRequest,
    TicketConfirmResponse,
    TicketDraftRequest,
    TicketDraftResponse,
)

router = APIRouter(tags=["Student Records & Tickets"])


@router.get("/student/{student_id}/status", response_model=StudentStatusResponse)
def get_student_status(student_id: str) -> StudentStatusResponse:
    """Deterministic read-only lookup of student enrollment and financial status."""
    record = MOCK_STUDENT_DB.get(student_id)
    if record is not None:
        return StudentStatusResponse(
            student_id=student_id,
            name=record.get("name", "Makerere Student"),
            program=record.get("enrolled_program", "Bachelor of Science in Software Engineering (BSSE)"),
            college=record.get("college", "College of Computing and Information Sciences (CoCIS)"),
            year_of_study=record.get("year_of_study", 4),
            status=record["status"],
            financial_hold=record.get("financial_hold", False),
            academic_warning=record.get("academic_warning", False),
        )
    # Default response for unknown students
    return StudentStatusResponse(
        student_id=student_id,
        name="Makerere Student",
        program="Bachelor of Science in Software Engineering (BSSE)",
        college="College of Computing and Information Sciences (CoCIS)",
        year_of_study=4,
        status="Enrolled",
        financial_hold=False,
        academic_warning=False,
    )


@router.post("/tickets/draft", response_model=TicketDraftResponse)
def draft_support_ticket(payload: TicketDraftRequest) -> TicketDraftResponse:
    """Draft an administrative support ticket awaiting student review and confirmation."""
    ticket_id = f"TKT-{payload.student_id}-{uuid.uuid4().hex[:6].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    draft = TicketDraftResponse(
        ticket_id=ticket_id,
        student_id=payload.student_id,
        issue_category=payload.issue_category,
        issue_description=payload.issue_description,
        priority=payload.priority,
        status="Drafted",
        message=(
            f"Successfully drafted support ticket {ticket_id} for student {payload.student_id}. "
            "Please review details and explicitly confirm submission."
        ),
        student_confirmation_required=True,
        created_at=now_iso,
    )

    # Store in pending tickets for atomic consume on confirmation
    PENDING_TICKETS[ticket_id] = draft

    return draft


@router.post("/tickets/confirm", response_model=TicketConfirmResponse)
def confirm_support_ticket(payload: TicketConfirmRequest) -> TicketConfirmResponse:
    """Human-in-the-loop explicit confirmation to dispatch or cancel a drafted ticket.

    Performs an atomic pop from the pending tickets store. If the ticket has
    already been consumed (submitted or cancelled), returns HTTP 404 to enforce
    the idempotency guarantee documented in Appendix E of the engineering report.
    """
    # Atomic pop: ticket can only be consumed once
    draft = PENDING_TICKETS.pop(payload.ticket_id, None)
    if draft is None:
        raise HTTPException(
            status_code=404,
            detail=f"No pending ticket found for ID: {payload.ticket_id}. "
            "It may have already been submitted or cancelled.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()

    if not payload.confirmed:
        return TicketConfirmResponse(
            ticket_id=payload.ticket_id,
            student_id=payload.student_id,
            status="Cancelled",
            message=f"Ticket {payload.ticket_id} was cancelled by the student.",
            dispatched_to=None,
            confirmed_at=now_iso,
        )

    # Route based on department
    destination = "College Academic Registrar Desk (CoCIS)"
    return TicketConfirmResponse(
        ticket_id=payload.ticket_id,
        student_id=payload.student_id,
        status="Submitted",
        message=f"Ticket {payload.ticket_id} successfully confirmed and dispatched to {destination}.",
        dispatched_to=destination,
        confirmed_at=now_iso,
    )
