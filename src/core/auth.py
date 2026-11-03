"""Simple, dependency-light authentication and authorization helpers.

This intentionally avoids external JWT dependencies so the project remains
reproducible without adding new runtime packages.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import HTTPException, Request

DEFAULT_SECRET = "makerere-student-support-agent-dev-secret"
DEFAULT_USERS: dict[str, dict[str, str]] = {
    "student": {"password": "student123", "role": "student"},
    "staff": {"password": "staff123", "role": "staff"},
    "admin": {"password": "admin123", "role": "admin"},
}


def _get_secret() -> str:
    return os.getenv("APP_SECRET_KEY", DEFAULT_SECRET)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padded = value + ("=" * ((4 - len(value) % 4) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def get_known_users() -> dict[str, dict[str, str]]:
    """Load configured users from the environment when present."""
    configured = os.getenv("AUTH_USERS_JSON")
    if not configured:
        return DEFAULT_USERS.copy()

    try:
        parsed = json.loads(configured)
    except json.JSONDecodeError:
        return DEFAULT_USERS.copy()

    if not isinstance(parsed, dict):
        return DEFAULT_USERS.copy()

    normalized: dict[str, dict[str, str]] = {}
    for username, payload in parsed.items():
        if isinstance(payload, dict):
            password = str(payload.get("password", ""))
            role = str(payload.get("role", "student"))
            normalized[str(username)] = {"password": password, "role": role}
    return normalized or DEFAULT_USERS.copy()


def issue_token(username: str, role: str, ttl_seconds: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(_get_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"


def verify_token(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed token")

    header_segment, payload_segment, signature_segment = parts
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = _b64url_encode(
        hmac.new(_get_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    )
    if not hmac.compare_digest(expected_signature, signature_segment):
        raise ValueError("Invalid signature")

    payload = json.loads(_b64url_decode(payload_segment).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("Token expired")
    return payload


def get_token_from_request(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def resolve_request_identity(request: Request, *, allow_anonymous: bool = True) -> dict[str, Any] | None:
    token = get_token_from_request(request)
    if not token:
        if allow_anonymous:
            return None
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        claims = verify_token(token)
    except ValueError as exc:
        if allow_anonymous:
            return None
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}") from exc

    request.state.user = claims
    return claims


def require_role(*allowed_roles: str):
    async def dependency(request: Request) -> dict[str, Any]:
        claims = resolve_request_identity(request, allow_anonymous=False)
        if claims is None:
            raise HTTPException(status_code=401, detail="Authentication required")

        role = str(claims.get("role", "")).lower()
        if allowed_roles and role not in {r.lower() for r in allowed_roles}:
            raise HTTPException(status_code=403, detail="Insufficient privileges for this action")
        return claims

    return dependency
