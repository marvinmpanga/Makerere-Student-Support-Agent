from typing import Optional
from pydantic import BaseModel, Field


class GetStudentStatusRequest(BaseModel):
    """Schema for requesting a student's status."""
    student_id: str = Field(..., description="The unique identifier for the student (e.g., student number).")


class GetStudentStatusResponse(BaseModel):
    """Schema for the student's status response."""
    student_id: str = Field(..., description="The student's identifier.")
    status: str = Field(..., description="The current academic status (e.g., 'Enrolled', 'Graduated', 'Suspended').")
    enrolled_program: Optional[str] = Field(default=None, description="The program the student is currently enrolled in.")
    financial_hold: bool = Field(default=False, description="Whether the student has a financial hold preventing registration or graduation.")
    message: Optional[str] = Field(default=None, description="Additional context or system messages regarding the student's status.")


class DraftSupportTicketRequest(BaseModel):
    """Schema for drafting a new support ticket."""
    student_id: str = Field(..., description="The unique identifier for the student submitting the ticket.")
    issue_category: str = Field(..., description="The category of the issue (e.g., 'Academics', 'Finance', 'IT Support', 'General').")
    issue_description: str = Field(..., description="A detailed description of the student's issue.")


class DraftSupportTicketResponse(BaseModel):
    """Schema for the drafted support ticket response."""
    ticket_id: str = Field(..., description="The newly generated unique ticket identifier.")
    status: str = Field(..., description="The current status of the ticket (e.g., 'Draft', 'Pending Confirmation').")
    message: str = Field(..., description="Confirmation message regarding the draft ticket creation.")
    student_confirmation_required: bool = Field(
        default=True,
        description="Always True. The ticket must NOT be persisted without explicit student confirmation."
    )


class TicketConfirmationRequest(BaseModel):
    """Request to confirm or reject a previously drafted ticket."""
    ticket_id: str = Field(..., description="The ticket ID returned from the /draft-ticket endpoint.")
    student_id: str = Field(..., description="The student ID submitting the confirmation.")
    confirmed: bool = Field(..., description="True to submit the ticket, False to cancel it.")


class TicketConfirmationResponse(BaseModel):
    """Result of the Human-in-the-Loop ticket confirmation step."""
    ticket_id: str = Field(..., description="The ticket ID that was confirmed or cancelled.")
    final_status: str = Field(..., description="'Submitted' if confirmed, 'Cancelled' if rejected.")
    message: str = Field(..., description="Human-readable result message.")
    audit_event: str = Field(..., description="Audit log event name (e.g. TICKET_SUBMITTED, TICKET_CANCELLED).")
