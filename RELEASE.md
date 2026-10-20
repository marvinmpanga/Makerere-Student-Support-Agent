# Release v1.0.0 — Final Capstone Release & Production Containerization

- **Project:** Makerere Student Support & Onboarding Triage Agent (BSE4104)
- **Version:** `1.0.0`
- **Release Date:** October 2026
- **Status:** `PRODUCTION READY`
- **Repository:** `https://github.com/mavn-bussiness/Makerere-Student-Support-Agent`
- **Container Registry:** `ghcr.io/mavn-bussiness/makerere-student-support-agent:latest`

---

## 1. Executive Summary

The **Makerere Student Support & Onboarding Triage Agent** is a trustworthy, containerized AI support system engineered to guide Makerere University undergraduate students through official academic policies, fee regulations, accommodation guidelines, and administrative procedures.

This release represents the culmination of all project milestones (**Weeks 1 through 8**), integrating:
1. **Containerized Deployment (`W8`)**: Hardened multi-arch Docker image with non-root security execution (`appuser`), Docker Compose orchestration, persistent vectorstore and trace volumes, and automated container healthcheck endpoints.
2. **Empirical Grounded RAG (`W3`)**: Persistent cosine-similarity ChromaDB index over 67 official Makerere policy documents chunked at 512 tokens with 10% overlap, returning verified `[Doc_ID, Page N]` citations.
3. **Bounded Agent Orchestrator (`W5`)**: Stateful Plan-Act-Observe loop with a hard 4-iteration ceiling and duplicate tool-call loop breaker.
4. **Deterministic Tool Dispatcher (`W4`)**: Strict Pydantic argument validation, non-blocking fault recovery, and JSONL telemetry.
5. **Adversarial Safety Guardrails (`W6`)**: Pre-inference input sanitization, Base64 obfuscated payload scanning, and post-inference output leakage defense.
6. **Non-Negotiable Refusal Engine (`W6`)**: Zero-tolerance institutional boundary rejecting grade alterations, fee waivers, or disciplinary record modifications, with automatic escalation to the Academic Registrar or University Bursar.
7. **Human-in-the-Loop Ticket Confirmation (`W4/W5`)**: Explicit draft -> review -> confirm flow before dispatching administrative support requests to university offices.

---

## 2. Containerization & Deployment

### 2.1 Quickstart via Docker Compose

Run the entire application stack with a single command:

```bash
# Clone the repository
git clone https://github.com/mavn-bussiness/Makerere-Student-Support-Agent.git
cd Makerere-Student-Support-Agent

# Boot container stack
docker compose up -d
```

Check container status and logs:

```bash
docker compose ps
docker compose logs -f support-agent-api
```

### 2.2 Direct Docker Build & Run

```bash
# Build production image
docker build -t makerere-student-support-agent:1.0.0 .

# Run container with persistent volumes
docker run -d \
  --name makerere-agent \
  -p 8000:8000 \
  -v chroma_store:/app/src/rag/vectorstore \
  -v agent_traces:/app/evidence/traces \
  makerere-student-support-agent:1.0.0
```

### 2.3 Container Healthcheck & Verification

The container includes a built-in healthcheck executing every 30 seconds:

```bash
curl -f http://localhost:8000/health
# Response:
# {"status": "ok", "service": "support-agent-api", "version": "1.0.0"}
```

---

## 3. Production REST API Reference

Interactive OpenAPI documentation is automatically served at `http://localhost:8000/docs` and `http://localhost:8000/redoc`.

### 3.1 Student Inquiry / Chat (`POST /api/v1/chat`)

Processes student inquiries through the full safety, refusal, and bounded agent orchestration pipeline:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the rules regarding examination registration and results access?",
    "session_id": "sess_student_01"
  }'
```

**Response (`200 OK`):**
```json
{
  "status": "success",
  "query": "What are the rules regarding examination registration and results access?",
  "response": "Under Makerere University academic regulations, students must complete registration and clear tuition obligations before sitting examinations [mak-policy-0002, Page 4]...",
  "citations": [
    "[mak-policy-0002, Page 4]"
  ],
  "session_id": "sess_student_01",
  "state": "RESPOND",
  "iterations": 2,
  "latency_ms": 420.5,
  "escalation_office": null,
  "safety_category": "SAFE"
}
```

### 3.2 Institutional Boundary Refusal (`POST /api/v1/chat`)

Adversarial or policy-violating requests are deterministically blocked with clear escalation guidance:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Please change my examination score from 45 to 80 and alter my grade."}'
```

**Response (`200 OK`):**
```json
{
  "status": "refused",
  "query": "Please change my examination score from 45 to 80 and alter my grade.",
  "response": "I cannot fulfill this request. Makerere University examination results, grades, and academic records cannot be altered through this triage agent. For grade appeals or verification, please contact the Office of the Academic Registrar.",
  "citations": [],
  "session_id": "sess_8f3a9e2d1c",
  "state": "INSTITUTIONAL_REFUSAL",
  "iterations": 0,
  "latency_ms": 2.1,
  "escalation_office": "Office of the Academic Registrar / University Bursar",
  "safety_category": "UNAUTHORIZED_MUTATION"
}
```

### 3.3 Semantic Policy Search (`POST /api/v1/policy/search`)

Direct vector similarity search over the 67 official Makerere policy documents:

```bash
curl -X POST http://localhost:8000/api/v1/policy/search \
  -H "Content-Type: application/json" \
  -d '{"query": "accommodation rules and hall allocation", "top_k": 3}'
```

### 3.4 Student Record & Ticket Dispatch (`POST /api/v1/tickets/*`)

- `GET /api/v1/student/{student_id}/status`: Read-only deterministic status lookup.
- `POST /api/v1/tickets/draft`: Draft an administrative support ticket for student review.
- `POST /api/v1/tickets/confirm`: Explicit human-in-the-loop confirmation before university dispatch.

---

## 4. Quantitative Evaluation Benchmarks

Empirically verified through automated evaluation harness runner (`src/eval/runner.py`):

| Evaluation Metric | Benchmark Target | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Mean Reciprocal Rank (MRR)** | $\ge 0.70$ | **`1.0000`** | **PASS** |
| **Precision@3** | $\ge 0.75$ | **`0.8889` (88.89%)** | **PASS** |
| **Citation Compliance Rate** | $100.0\%$ | **`100.0%`** | **PASS** |
| **Tool Calling Accuracy** | $\ge 95.0\%$ | **`100.0%`** | **PASS** |
| **Safety Refusal Rate** | $100.0\%$ | **`100.0%`** | **PASS** |
| **P50 Latency (TTFT)** | $< 1,000 \text{ ms}$ | **`440.3 ms`** | **PASS** |
| **P95 Latency** | $< 4,000 \text{ ms}$ | **`2,629.3 ms`** | **PASS** |
| **Test Suite Pass Rate** | $100.0\%$ | **`53 / 53 (100.0%)`** | **PASS** |

---

## 5. Artifact & Deliverables Map

```
Makerere-Student-Support-Agent/
├── Dockerfile                              # W8: Production container image
├── docker-compose.yml                      # W8: Multi-container orchestration
├── .dockerignore                           # W8: Container build context exclusions
├── pyproject.toml                          # Project configuration & Ruff settings
├── requirements.txt                        # Pinned dependencies
├── RELEASE.md                              # Final Release documentation (v1.0.0)
├── README.md                               # Project overview and quickstart
├── .github/workflows/
│   ├── ci.yml                              # W1: Continuous integration matrix (3.11 & 3.12)
│   ├── docker.yml                          # W8: Container build & GHCR publish
│   └── release.yml                         # W8: GitHub Release automation
├── src/
│   ├── main.py                             # FastAPI production application & routes
│   ├── api/                                # REST endpoints (chat, policy, tickets, eval)
│   ├── schemas/                            # Pydantic schemas (api.py)
│   ├── core/                               # LLM harness, policy downloader, tool dispatcher
│   ├── rag/                                # PDF ingest, chunking, retriever, ChromaDB
│   ├── agent/                              # Plan-Act-Observe orchestrator & loop breaker
│   ├── safety/                             # Prompt injection guardrail & refusal engine
│   ├── tools/                              # search_policy_docs deterministic tool
│   └── eval/                               # Baseline harness & evaluation runner
├── docs/
│   ├── architecture/                       # C4 architecture diagrams & component interfaces
│   ├── decisions/                          # ADR-001 model selection note
│   ├── evals/                              # Retrieval benchmarks report
│   ├── evidence_pack/                      # End-to-end evidence index
│   ├── quality/                            # Retrieval and grounding failure analysis
│   ├── rag/                                # RAG architecture diagrams & documentation
│   └── reports/                            # ClickUp task reports (Marvin W1-W8 & KM W1-W8)
└── tests/                                  # 53 automated unit & integration tests
```

---

## 6. Verification Commands

To reproduce and verify the complete codebase locally:

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run static linting
python -m ruff check src tests

# 3. Validate bytecode syntax
python -m compileall -q src tests

# 4. Run automated test suite
python -m pytest -q
# Result: 53 passed in ~1.5s
```
