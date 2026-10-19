# W8-02: Production-grade container image for Makerere Student Support & Onboarding Triage Agent
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies required by native wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY src ./src
COPY knowledge ./knowledge
COPY prompts ./prompts
COPY docs ./docs
COPY README.md ./

# Create non-root runtime user and writable directories for traces and vectorstore
RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/evidence/traces /app/src/rag/vectorstore \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
