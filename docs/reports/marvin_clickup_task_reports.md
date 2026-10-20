# ClickUp Task Completion Reports — Mpanga Marvin Joseph
**Role:** AI Engineering Lead & DevOps  
**Project:** Makerere Student Support & Onboarding Triage Agent (BSE4104 Capstone)  
**Repository:** `https://github.com/marvinmpanga/Makerere-Student-Support-Agent`

---

## Week 1 Deliverables

### Task `W1-02`: Repository Scaffolding & Virtual Environment
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`.gitignore`](../../.gitignore), [`pyproject.toml`](../../pyproject.toml), [`requirements.txt`](../../requirements.txt), [`.env.example`](../../.env.example)
- **Summary of Work:**
  - Scaffolded the modular Python package layout (`src/core`, `src/rag`, `src/tools`, `src/agent`, `src/safety`, `src/eval`, `tests/`, `docs/`, `knowledge/`, `prompts/`, `evidence/`).
  - Configured [`pyproject.toml`](../../pyproject.toml) with project metadata, Python `>=3.11` compatibility, Ruff linter configuration, Pytest test discovery (`testpaths = ["tests"]`), and Bandit security exclusions.
  - Defined pinned dependency ranges in [`requirements.txt`](../../requirements.txt) (`fastapi`, `pydantic-settings`, `chromadb`, `pypdf`, `google-genai`, `google-generativeai`, `pytest`, `httpx`, `python-dotenv`).
  - Configured [`.gitignore`](../../.gitignore) to exclude virtual environments (`.venv/`), secrets (`.env`), raw PDF binaries (`knowledge/raw/*.pdf`), and local ChromaDB binary index files (`src/rag/vectorstore/*`).
- **Verification Evidence:**
  - Commit `3600dad` & PR `#8` / `#9` merged to `main`.

---

### Task `W1-03`: CI/CD Pipeline Configuration
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), [`README.md`](../../README.md), [`docs/ci-cd.md`](../../docs/ci-cd.md)
- **Summary of Work:**
  - Configured GitHub Actions matrix pipeline ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)) running on Python `3.11` and `3.12` across all pushes and pull requests.
  - Automated 5 quality gates: Python bytecode syntax validation (`compileall`), Ruff static linting (`ruff check src tests`), Bandit AST security scanning (`bandit -r src -ll`), dependency vulnerability auditing (`pip-audit`), controlled knowledge register schema verification, and Pytest unit testing with XML coverage upload.
  - Added CI/CD, Ruff, Bandit, and Pytest status badges to [`README.md`](../../README.md).
- **Verification Evidence:**
  - Commits `2fbc62f`, `fcbbaba`, `69dfd68` merged to `main`.

---

## Week 2 Deliverables

### Task `W2-01`: Model Selection Note (Gemini 1.5 Flash)
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`docs/decisions/adr_001_model_selection.md`](../decisions/adr_001_model_selection.md), [`docs/requirements/model_selection_note.md`](../requirements/model_selection_note.md)
- **Summary of Work:**
  - Authored Architecture Decision Record **ADR-001** justifying the selection of **Google Gemini 1.5 Flash (`gemini-1.5-flash`)** over OpenAI `gpt-4o-mini` and self-hosted `Llama-3.1-8B`.
  - Evaluated latency (sub-second TTFT), 1M+ token context window capacity for Makerere policy ingestion, native `response_mime_type="application/json"` structured output enforcement, cost efficiency, and Makerere data-privacy constraints.
  - Specified production hyperparameters (`temperature=0.2`, `top_p=0.95`, `max_output_tokens=1024`).
- **Verification Evidence:**
  - Commit `321c6f5` & PR `#4` / `#8` merged to `main`.

---

### Task `W2-04`: Baseline Execution Harness & Logging
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`src/eval/baseline_harness.py`](../../src/eval/baseline_harness.py), [`tests/test_baseline_harness.py`](../../tests/test_baseline_harness.py)
- **Summary of Work:**
  - Implemented `BaselineExecutionHarness` wrapping `GeminiBaselineClient` (`src/core/llm.py`) with deterministic offline client injection support for CI testing.
  - Recorded per-case `ExecutionTrace` telemetry (`request_id`, `timestamp_utc`, `case_id`, `prompt_version`, `model`, `status`, `latency_seconds`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `structured_output`) to `evidence/traces/baseline_runs.jsonl`.
- **Verification Evidence:**
  - Unit tests in `tests/test_baseline_harness.py` (`2 passed`); commit `8659101` merged in PR `#8`.

---

## Week 3 Deliverables

### Task `W3-03`: Ingestion, Chunking & Vector Indexing
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`src/rag/ingest.py`](../../src/rag/ingest.py), `src/rag/vectorstore/`, [`tests/test_rag_ingest.py`](../../tests/test_rag_ingest.py)
- **Summary of Work:**
  - Built end-to-end PDF policy ingestion pipeline reading [`knowledge/source_register.json`](../../knowledge/source_register.json) and extracting page-level text via `pypdf`.
  - Implemented token-window semantic chunking at **512 tokens with 10% (51-token) overlap**, tracking `page_start` and `page_end` across page boundaries.
  - Embedded chunks into a persistent cosine-similarity **ChromaDB** collection (`makerere_policies` in `src/rag/vectorstore/`) with pre-formatted `[Doc_ID, Page N]` / `[Doc_ID, Pages N-M]` citation metadata on every chunk.
  - Added pluggable embedding backends: `GeminiEmbedder` (`gemini-embedding-001` with 429 exponential backoff), `LocalEmbedder` (`all-MiniLM-L6-v2` ONNX offline), and `HashEmbedder` (deterministic CI unit tests).
  - Indexed **45 readable Makerere policy PDFs into 1,045 vector chunks** (gracefully flagging 21 scanned image-only PDFs for OCR).
- **Verification Evidence:**
  - 7 unit and end-to-end tests in `tests/test_rag_ingest.py` (`7 passed`); commits `1280d12` & `99b72d3` merged to `main` via PR `#8` & `#9`.

---

## Week 4 Deliverables

### Task `W4-02`: Implement `search_policy_docs` Tool
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`src/tools/policy_search.py`](../../src/tools/policy_search.py), [`tests/test_week4_tools.py`](../../tests/test_week4_tools.py)
- **Summary of Work:**
  - Implemented deterministic `search_policy_docs` tool querying the `makerere_policies` ChromaDB collection.
  - Enforced strict Pydantic input validation (`PolicySearchArgs` with `extra="forbid"`, `query` length `3..500`, `top_k` bounded `1..10`, and validated Makerere policy category filter).
  - Returned structured `PolicySearchResult` containing `PolicySearchHit` records, similarity scores, deduplicated `[Doc_ID, Page N]` citations, and formatted LLM context blocks.
- **Verification Evidence:**
  - Commit `8fdfa12` on branch `feature/W4-tools-dispatcher`; verified with `tests/test_week4_tools.py`.

---

### Task `W4-05`: LLM Tool Dispatcher & Telemetry Loop
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`src/core/dispatcher.py`](../../src/core/dispatcher.py), [`tests/test_week4_tools.py`](../../tests/test_week4_tools.py)
- **Summary of Work:**
  - Implemented `ToolDispatcher` to intercept LLM tool calls, validate arguments against registered Pydantic schemas, invoke targeted Python functions, and export JSON function schemas (`.tool_schemas()`).
  - Built non-blocking error recovery for unknown tools, malformed JSON arguments, and Pydantic validation failures (`status` in `success`, `validation_error`, `unknown_tool`, `execution_error`).
  - Implemented bounded `.run_loop()` feeding tool observations back into the model context window and logging per-call telemetry (`ToolTelemetryRecord`) to `evidence/traces/tool_dispatch.jsonl`.
- **Verification Evidence:**
  - Commit `8fdfa12` on branch `feature/W4-tools-dispatcher` (`7 passed` in `tests/test_week4_tools.py`).

---

## Week 5 Deliverables

### Task `W5-02`: Bounded Agent Orchestrator Loop
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`src/agent/orchestrator.py`](../../src/agent/orchestrator.py), [`evidence/traces/agent_loop.jsonl`](../../evidence/traces/agent_loop.jsonl), [`tests/test_week5_agent.py`](../../tests/test_week5_agent.py)
- **Summary of Work:**
  - Implemented stateful **Plan-Act-Observe** state machine (`INTAKE -> PLAN -> ACT -> OBSERVE -> RESPOND / FALLBACK_TERMINATED`) in `AgentOrchestrator`.
  - Integrated `ToolDispatcher` and `LoopBreakerGuardrail` to execute multi-step policy lookups, aggregate `[Doc_ID, Page N]` citations across turns, and log complete state-transition traces to `evidence/traces/agent_loop.jsonl`.
- **Verification Evidence:**
  - Commit `75821cb` on branch `feature/W5-agent-orchestrator`; trace proof committed in `evidence/traces/agent_loop.jsonl`.

---

### Task `W5-04`: Max-Iteration Guardrails & Loop Breaker
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`src/agent/guardrails.py`](../../src/agent/guardrails.py), [`tests/test_week5_agent.py`](../../tests/test_week5_agent.py)
- **Summary of Work:**
  - Implemented `LoopBreakerGuardrail` enforcing a strict ceiling of **4 iterations** (`MAX_AGENT_ITERATIONS = 4`), SHA-256 duplicate tool-call cycle detection (`max_identical_tool_calls = 2`), latency budget (`30.0s`), and token budget (`8192`).
  - Emits deterministic student fallback notices (`FALLBACK_MAX_ITERATIONS_NOTICE`, `FALLBACK_REPEATED_CALL_NOTICE`) whenever hard boundaries are triggered.
- **Verification Evidence:**
  - Commit `75821cb` on branch `feature/W5-agent-orchestrator` (`4 passed` in `tests/test_week5_agent.py`).

---

## Week 6 Deliverables

### Task `W6-03`: Injection & Jailbreak Defense Layer
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`src/safety/guardrails.py`](../../src/safety/guardrails.py), [`evidence/traces/safety_audit.jsonl`](../../evidence/traces/safety_audit.jsonl), [`tests/test_week6_safety.py`](../../tests/test_week6_safety.py)
- **Summary of Work:**
  - Implemented `InjectionDefenseGuardrail` providing pre-inference input sanitization, length enforcement (`2,000` chars), and deterministic regex + Base64-decoded payload scanning across 6 threat categories:
    - `INJ-001`: Direct prompt instruction override
    - `INJ-002`: Jailbreak & DAN roleplay personas
    - `INJ-003`: System prompt & secret extraction
    - `INJ-004`: Delimiter/tag escape attacks (`</system>`, `[INST]`, `<<SYS>>`)
    - `MUT-001`: Non-negotiable institutional mutation boundary (blocking grade, mark, CGPA, and tuition fee alterations)
    - `ESC-001`: Privilege escalation & HITL confirmation bypass
  - Implemented `.inspect_output()` to block API key leaks (`LEAK-API-KEY`), system prompt leaks (`LEAK-SYSTEM-HEADER`), and false grade/fee mutation claims (`LEAK-MUTATION-CLAIM`).
  - Logged structured refusal audit records to `evidence/traces/safety_audit.jsonl`.
- **Verification Evidence:**
  - Commits `bac022d` & `25a33bb` on branch `feature/W6-safety-guardrails` (`6 passed` in `tests/test_week6_safety.py`).

---

## Week 7 Deliverables

### Task `W7-02`: Automated Evaluation Harness Runner
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`src/eval/runner.py`](../../src/eval/runner.py), [`tests/test_week7_runner.py`](../../tests/test_week7_runner.py)
- **Summary of Work:**
  - Implemented `EvaluationHarnessRunner` executing end-to-end benchmark scenarios across `InjectionDefenseGuardrail`, `AgentOrchestrator`, `ToolDispatcher`, and `search_policy_docs`.
  - Computed empirical Week 7 metrics on the 1,045-chunk Makerere policy vector index:
    - **Mean Reciprocal Rank (MRR):** `1.0000`
    - **Precision@3:** `0.8889 (88.89%)`
    - **Citation Compliance Rate:** `100.0%`
    - **Tool Call Accuracy:** `100.0%`
    - **Safety Refusal Rate:** `100.0%`
    - **Latency (P50 / P95):** `440.3 ms` / `2,629.3 ms`
    - **Estimated Cost (6 Scenarios):** `$0.001505 USD` (`5,626` tokens)
- **Verification Evidence:**
  - Commit `6630e1f` on branch `feature/W7-eval-runner` (`3 passed` in `tests/test_week7_runner.py`).

---

## Week 8 Deliverables

### Task `W8-01`: Multi-Container Orchestration (`docker-compose.yml`)
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`docker-compose.yml`](../../docker-compose.yml), [`.dockerignore`](../../.dockerignore)
- **Summary of Work:**
  - Designed and configured single-command `docker compose up -d` orchestration booting the Makerere Student Support API service.
  - Configured persistent named volumes for ChromaDB vectorstore (`chroma_vectorstore:/app/src/rag/vectorstore`) and execution audit telemetry (`agent_traces:/app/evidence/traces`).
  - Implemented container healthcheck probe testing `http://localhost:8000/health` at 30-second intervals with 5-second timeouts.
  - Created [`.dockerignore`](../../.dockerignore) to prevent virtual environments, local caches, raw binaries, and test coverage artifacts from bloating the build context.
- **Verification Evidence:**
  - `docker-compose.yml` verified; container boots and passes health checks.

---

### Task `W8-02`: Production Container Image & Hardening (`Dockerfile`)
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`Dockerfile`](../../Dockerfile), [`src/main.py`](../../src/main.py), [`src/api/`](../../src/api/)
- **Summary of Work:**
  - Authored multi-arch production `Dockerfile` based on `python:3.12-slim`.
  - Enforced non-root user execution (`useradd appuser`) and restricted filesystem permissions for security compliance.
  - Implemented container entrypoint running `uvicorn src.main:app --host 0.0.0.0 --port 8000` with automated container healthcheck (`curl -f http://localhost:8000/health`).
  - Integrated REST API router endpoints (`/api/v1/chat`, `/api/v1/policy/search`, `/api/v1/student/{id}/status`, `/api/v1/tickets/draft`, `/api/v1/tickets/confirm`, `/api/v1/eval/metrics`).
- **Verification Evidence:**
  - Commit `d89f8dc` and unit tests in `tests/test_api.py` (`53 passed`).

---

### Task `W8-03`: Final GitHub Release (v1.0.0) & Automated CI/CD
- **Status:** `COMPLETE`
- **Assignee:** Mpanga Marvin Joseph
- **Target Artifacts:** [`RELEASE.md`](../../RELEASE.md), [`.github/workflows/docker.yml`](../../.github/workflows/docker.yml), [`.github/workflows/release.yml`](../../.github/workflows/release.yml), [`pyproject.toml`](../../pyproject.toml)
- **Summary of Work:**
  - Bumped project version to `v1.0.0` in [`pyproject.toml`](../../pyproject.toml) and [`src/main.py`](../../src/main.py).
  - Authored comprehensive [`RELEASE.md`](../../RELEASE.md) detailing quickstart commands, REST API schemas, architectural completeness matrix, and verified evaluation benchmarks.
  - Built GitHub Actions automated release pipeline ([`.github/workflows/release.yml`](../../.github/workflows/release.yml)) for building distribution wheels/tarballs and publishing GitHub Releases.
  - Built Docker validation and GHCR publishing pipeline ([`.github/workflows/docker.yml`](../../.github/workflows/docker.yml)).
- **Verification Evidence:**
  - Release artifacts generated, 53 test cases passing, all quality gates verified.
