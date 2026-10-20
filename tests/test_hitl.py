from fastapi.testclient import TestClient
from src.main import app
from src.core.tools import PENDING_TICKETS

client = TestClient(app)

def setup_function():
    PENDING_TICKETS.clear()

def test_full_hitl_flow_confirmation():
    # 1. Draft a ticket
    draft_resp = client.post("/api/v1/tools/draft-ticket", json={
        "student_id": "123456",
        "issue_category": "Financial",
        "issue_description": "Need help",
        "priority": "Normal"
    })
    ticket_id = draft_resp.json()["ticket_id"]
    
    # 2. Confirm the ticket
    confirm_resp = client.post("/api/v1/hitl/confirm-ticket", json={
        "ticket_id": ticket_id,
        "student_id": "123456",
        "confirmed": True
    })
    
    assert confirm_resp.status_code == 200
    data = confirm_resp.json()
    assert data["ticket_id"] == ticket_id
    assert data["final_status"] == "Submitted"
    assert data["audit_event"] == "TICKET_SUBMITTED"
    
    # 3. Verify it is removed from pending store
    assert ticket_id not in PENDING_TICKETS

def test_full_hitl_flow_cancellation():
    draft_resp = client.post("/api/v1/tools/draft-ticket", json={
        "student_id": "123456",
        "issue_category": "Financial",
        "issue_description": "Need help",
        "priority": "Normal"
    })
    ticket_id = draft_resp.json()["ticket_id"]
    
    confirm_resp = client.post("/api/v1/hitl/confirm-ticket", json={
        "ticket_id": ticket_id,
        "student_id": "123456",
        "confirmed": False
    })
    
    assert confirm_resp.status_code == 200
    data = confirm_resp.json()
    assert data["final_status"] == "Cancelled"
    assert data["audit_event"] == "TICKET_CANCELLED"

def test_confirm_unknown_ticket_returns_404():
    confirm_resp = client.post("/api/v1/hitl/confirm-ticket", json={
        "ticket_id": "TKT-UNKNOWN99",
        "student_id": "123456",
        "confirmed": True
    })
    assert confirm_resp.status_code == 404

