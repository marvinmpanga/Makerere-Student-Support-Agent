from fastapi import APIRouter, HTTPException
from src.schemas.tools import TicketConfirmationRequest, TicketConfirmationResponse
from src.core.hitl import process_ticket_confirmation

router = APIRouter(tags=["hitl"])

@router.post("/confirm-ticket", response_model=TicketConfirmationResponse)
def confirm_ticket_endpoint(request: TicketConfirmationRequest):
    """
    Human-in-the-Loop confirmation gate.
    Student explicitly confirms or cancels a drafted ticket.
    Ticket is only persisted if confirmed=True.
    """
    try:
        return process_ticket_confirmation(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

