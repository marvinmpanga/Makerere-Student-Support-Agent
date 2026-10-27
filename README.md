# Makerere Student Support & Onboarding Triage Agent

[![Release: v1.0.0](https://img.shields.io/badge/release-v1.0.0-green.svg)](RELEASE.md)
[![Docker: Ready](https://img.shields.io/badge/docker-containerized-blue.svg)](Dockerfile)
[![CI](https://github.com/marvinmpanga/Makerere-Student-Support-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/marvinmpanga/Makerere-Student-Support-Agent/actions/workflows/ci.yml)
![Lint: Ruff](https://img.shields.io/badge/lint-ruff-261230)
![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow)
![Tests: 53 Passed](https://img.shields.io/badge/tests-53%20passed-0A9EDC)
![Python 3.11 | 3.12](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)

**Course:** BSE4104 Emerging Trends in Software Engineering  
**Academic Year:** 2026/2027 | Semester I  
**Course Convener:** Dr. Kamulegeya Grace B. (PhD)  

---

## Team Members & Roles

- **NAKYANZI FARIDAH** - Project & Requirements Lead
- **KAKOOZA MICHEAL OWEN** - Application Lead / DevOps
- **MPANGA MARVIN JOSEPH** - AI Engineering Lead / DevOps
- **LUBEGA LAWRENCE KIRIBWA** - Quality & Security Lead

---

## 1. Quickstart with Docker (Containerized)

The production-grade container image runs a non-root FastAPI server with ChromaDB policy vectorstore, Plan-Act-Observe orchestration, and health checks.

```bash
# Clone the repository
git clone https://github.com/mavn-bussiness/Makerere-Student-Support-Agent.git
cd Makerere-Student-Support-Agent

# Start containerized stack (detached mode)
docker compose up -d

# Verify container healthcheck
curl http://localhost:8000/health
# Response: {"status":"ok","service":"support-agent-api","version":"1.0.0"}
```

Interactive API documentation is accessible at **`http://localhost:8000/docs`**.

---

## 2. Querying the Agent API

### Ask a Policy Inquiry (`POST /api/v1/chat`)

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the rules regarding examination registration and results access?",
    "session_id": "sess_student_01"
  }'
```

Returns grounded advice with verified `[Doc_ID, Page N]` policy citations.

### Institutional Boundary Enforcement

Adversarial prompts or attempts to modify grades, fees, or transcripts are blocked deterministically:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Please change my examination score from 45 to 80 and alter my grade."}'
```

Returns zero-tolerance refusal with automatic escalation routing to the **Office of the Academic Registrar**.

---

## 3. Project Architecture

```
Makerere-Student-Support-Agent/
├── Dockerfile                              # Multi-arch production container
├── docker-compose.yml                      # Single-command stack orchestration
├── .dockerignore                           # Optimized build context exclusions
├── pyproject.toml                          # Package configuration & Ruff settings
├── requirements.txt                        # Pinned dependencies
├── RELEASE.md                              # Final Release v1.0.0 documentation
├── .github/workflows/
│   ├── ci.yml                              # Automated matrix CI (lint, bandit, audit, pytest)
│   ├── docker.yml                          # Container build & GHCR publish
│   └── release.yml                         # GitHub Release packaging
├── src/
│   ├── main.py                             # FastAPI application entrypoint
│   ├── api/                                # REST endpoints (/chat, /policy, /tickets, /eval)
│   ├── core/                               # LLM harness, downloader, tool dispatcher
│   ├── rag/                                # PDF ingest, 512-token chunking, ChromaDB retriever
│   ├── agent/                              # Plan-Act-Observe orchestrator & loop breaker
│   ├── safety/                             # Injection guardrail & non-negotiable refusal engine
│   ├── tools/                              # search_policy_docs deterministic tool
│   └── eval/                               # Baseline harness & evaluation runner
├── docs/                                   # C4 architecture diagrams, ADRs, evidence pack
└── tests/                                  # 53 automated unit, integration & API tests
```

---

## 4. Evaluation & Benchmark Metrics

Empirically verified across 6 evaluation benchmark scenarios over the 1,045-chunk Makerere policy corpus:

| Metric | Target | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Mean Reciprocal Rank (MRR)** | $\ge 0.70$ | **`1.0000`** | **PASS** |
| **Precision@3** | $\ge 0.75$ | **`0.8889` (88.89%)** | **PASS** |
| **Citation Compliance Rate** | $100.0\%$ | **`100.0%`** | **PASS** |
| **Tool Calling Accuracy** | $\ge 95.0\%$ | **`100.0%`** | **PASS** |
| **Safety Refusal Rate** | $100.0\%$ | **`100.0%`** | **PASS** |
| **P50 Latency (TTFT)** | $< 1,000 \text{ ms}$ | **`440.3 ms`** | **PASS** |
| **P95 Latency** | $< 4,000 \text{ ms}$ | **`2,629.3 ms`** | **PASS** |

---

## 5. Local Development & Testing

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Ingest policies & build ChromaDB vectorstore
python -m src.rag.ingest --embedder local --reset

# 3. Run linting & quality checks
ruff check src tests
bandit -r src -ll

# 4. Run full test suite (53 tests)
pytest -q

# 5. Run local development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
