"""FastAPI application entrypoint for the Makerere Student Support & Onboarding Triage Agent."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.api import api_router
from src.ui.portal import get_portal_html


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Makerere Student Support Agent"
    version: str = "1.0.0"
    environment: str = "production"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "Production REST API for Makerere University Student Support & Onboarding Triage Agent. "
        "Provides bounded Plan-Act-Observe orchestration, grounded ChromaDB RAG with mandatory citations, "
        "adversarial prompt-injection defense, and non-negotiable institutional refusal guardrails."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for web and client frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all v1 API routes
app.include_router(api_router)

# Mount system architecture modular routers
try:
    from src.api.hitl import router as hitl_router
    from src.api.llm import router as llm_router
    from src.api.memory import router as memory_router
    from src.api.rag import router as rag_router
    from src.api.tools import router as tools_router

    app.include_router(llm_router, prefix="/api/v1/llm", tags=["LLM Harness"])
    app.include_router(rag_router, prefix="/api/v1/rag", tags=["RAG Pipeline"])
    app.include_router(tools_router, prefix="/api/v1/tools", tags=["Tools Deterministic"])
    app.include_router(memory_router, prefix="/api/v1/memory", tags=["Session Memory"])
    app.include_router(hitl_router, prefix="/api/v1/hitl", tags=["HITL"])
except ImportError:
    pass


@app.get("/", tags=["System"])
def read_root(request: Request):
    """Root metadata endpoint or interactive Web UI if opened in browser."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return HTMLResponse(get_portal_html())
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "status": "online",
        "docs_url": "/docs",
        "portal_url": "/ui",
    }


@app.get("/ui", response_class=HTMLResponse, tags=["Web Portal"])
def get_ui() -> HTMLResponse:
    """Interactive Web Portal for students and administrators."""
    return HTMLResponse(get_portal_html())


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Container health check endpoint for Docker & Kubernetes."""
    return {"status": "ok", "service": "support-agent-api", "version": settings.version}
