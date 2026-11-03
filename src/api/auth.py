"""Authentication endpoints and authorization helpers for the app."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.core.auth import get_known_users, issue_token, resolve_request_identity

router = APIRouter(tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    username: str
    role: str


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    users = get_known_users()
    user = users.get(payload.username)
    if not user or user.get("password") != payload.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = issue_token(payload.username, user["role"])
    return LoginResponse(token=token, username=payload.username, role=user["role"])


@router.get("/auth/me")
def current_user(request: Request) -> dict[str, object]:
    claims = resolve_request_identity(request, allow_anonymous=True)
    if claims is None:
        return {"authenticated": False, "username": None, "role": None}
    return {
        "authenticated": True,
        "username": claims.get("sub"),
        "role": claims.get("role"),
        "exp": claims.get("exp"),
    }
