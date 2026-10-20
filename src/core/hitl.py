from src.core.tools import confirm_ticket
from src.schemas.tools import TicketConfirmationRequest, TicketConfirmationResponse

def confirm_ticket_action(ticket_id: str, confirmed: bool) -> dict:
    """
    Deprecated CLI handler kept for backward compatibility tests.
    """
    print("--- HUMAN IN THE LOOP REQUIRED ---")
    print(f"Ticket {ticket_id} is pending your approval.")
    
    # In a real deployed web app, this would block the API response.
    # The new HTTP API uses process_ticket_confirmation instead.
    if confirmed:
        print(">> Proceeding: User approved.")
        return {"status": "success", "action": "ticket_confirmed"}
    else:
        print(">> Aborting: User rejected.")
        return {"status": "aborted", "action": "ticket_rejected"}

def process_ticket_confirmation(request: TicketConfirmationRequest) -> TicketConfirmationResponse:
    """
    API-compatible HITL handler. Called by the HTTP endpoint.
    No input() calls - state is driven by the HTTP request body.
    """
    return confirm_ticket(request.ticket_id, request.confirmed)

