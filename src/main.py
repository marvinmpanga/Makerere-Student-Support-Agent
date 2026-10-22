from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Makerere Student Support Agent"
    environment: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


from src.api.llm import router as llm_router
from src.api.rag import router as rag_router

settings = Settings()
app = FastAPI(title=settings.app_name)

app.include_router(llm_router, prefix="/api/v1/llm")
app.include_router(rag_router, prefix="/api/v1/rag")

@app.get("/")
def read_root() -> dict[str, str]:
    return {"name": settings.app_name, "environment": settings.environment}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
