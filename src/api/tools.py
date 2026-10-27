from fastapi import APIRouter

from src.core.tools import draft_support_ticket, get_student_status
from src.schemas.tools import (
    DraftSupportTicketRequest,
    DraftSupportTicketResponse,
    GetStudentStatusRequest,
    GetStudentStatusResponse,
)

router = APIRouter(tags=["tools"])


@router.post("/student-status", response_model=GetStudentStatusResponse)
def student_status(request: GetStudentStatusRequest):
    """
    Read-only deterministic lookup of a student's status.
    """
    return get_student_status(request)


@router.post("/draft-ticket", response_model=DraftSupportTicketResponse)
def create_draft_ticket(request: DraftSupportTicketRequest):
    """
    Draft a support ticket.
    This does NOT persist the ticket. It requires explicit HITL confirmation.
    """
    return draft_support_ticket(request)

