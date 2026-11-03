"""FastAPI application entrypoint for the Makerere Student Support & Onboarding Triage Agent."""

from __future__ import annotations

from pathlib import Path

import swagger_ui
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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
WEB_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "Production REST API for Makerere University Student Support & Onboarding Triage Agent. "
        "Provides bounded Plan-Act-Observe orchestration, grounded ChromaDB RAG with mandatory citations, "
        "adversarial prompt-injection defense, and non-negotiable institutional refusal guardrails."
    ),
    docs_url=None,
    redoc_url="/redoc",
)

app.mount("/static", StaticFiles(directory=WEB_DIR), name="student-ui")

app.mount(
    "/docs-assets",
    StaticFiles(directory=Path(swagger_ui.__file__).parent / "static"),
    name="swagger-ui",
)


@app.get("/docs", include_in_schema=False)
def swagger_ui() -> HTMLResponse:
    """Serve Swagger UI with assets hosted by this application."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url or "",
        title=f"{app.title} - Swagger UI",
        swagger_js_url="/docs-assets/swagger-ui-bundle.js",
        swagger_css_url="/docs-assets/swagger-ui.css",
        swagger_favicon_url="/docs-assets/favicon-32x32.png",
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


@app.get("/", tags=["System"], response_model=None)
def read_root(request: Request) -> FileResponse | JSONResponse:
    """Serve the student UI to browsers and retain JSON metadata for API clients."""
    if "text/html" in request.headers.get("accept", ""):
        return FileResponse(WEB_DIR / "index.html")
    return JSONResponse({
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "status": "online",
        "docs_url": "/docs",
    })


@app.get("/app", response_class=HTMLResponse, include_in_schema=False, response_model=None)
def student_app() -> FileResponse:
    """Serve the student-facing support interface directly."""
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Container health check endpoint for Docker & Kubernetes."""
    return {"status": "ok", "service": "support-agent-api", "version": settings.version}
