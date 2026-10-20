"""FastAPI application entrypoint for the Makerere Student Support & Onboarding Triage Agent."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.api import api_router


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


@app.get("/", tags=["System"])
def read_root() -> dict[str, str]:
    """Root metadata endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Container health check endpoint for Docker & Kubernetes."""
    return {"status": "ok", "service": "support-agent-api", "version": settings.version}
