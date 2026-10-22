from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_get_student_status_known():
    response = client.post("/api/v1/tools/student-status", json={"student_id": "123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "123456"
    assert data["status"] == "Enrolled"
    assert data["financial_hold"] is False

def test_get_student_status_financial_hold():
    response = client.post("/api/v1/tools/student-status", json={"student_id": "987654"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Suspended"
    assert data["financial_hold"] is True

def test_get_student_status_unknown():
    response = client.post("/api/v1/tools/student-status", json={"student_id": "999999"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Unknown"

def test_draft_support_ticket():
    response = client.post("/api/v1/tools/draft-ticket", json={
        "student_id": "123456",
        "issue_category": "Financial",
        "issue_description": "Test ticket",
        "priority": "Normal"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Drafted"
    assert data["student_confirmation_required"] is True
    assert data["ticket_id"].startswith("TKT-")

def test_draft_support_ticket_missing_fields():
    response = client.post("/api/v1/tools/draft-ticket", json={"student_id": "123456"})
    assert response.status_code == 422

