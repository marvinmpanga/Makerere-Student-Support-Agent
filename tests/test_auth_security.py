from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_login_and_profile_round_trip():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "student", "password": "student123"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "student"
    assert payload["token"]

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {payload['token']}"},
    )
    assert me.status_code == 200
    body = me.json()
    assert body["authenticated"] is True
    assert body["username"] == "student"
    assert body["role"] == "student"

    anonymous = client.get("/api/v1/auth/me")
    assert anonymous.status_code == 200
    assert anonymous.json()["authenticated"] is False


def test_protected_ticket_endpoints_require_auth():
    protected = client.post(
        "/api/v1/tools/draft-ticket",
        json={
            "student_id": "123456",
            "issue_category": "Finance",
            "issue_description": "Need help with tuition balance.",
        },
    )
    assert protected.status_code == 401

    status_route = client.get("/api/v1/student/123456/status")
    assert status_route.status_code == 401
