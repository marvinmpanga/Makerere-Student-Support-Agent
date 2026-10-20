"""REST API package exposing all Makerere Student Support Agent endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.chat import router as chat_router
from src.api.evaluation import router as eval_router
from src.api.policy import router as policy_router
from src.api.tickets import router as tickets_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(chat_router)
api_router.include_router(policy_router)
api_router.include_router(tickets_router)
api_router.include_router(eval_router)

__all__ = ["api_router"]
