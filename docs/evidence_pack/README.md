# Comprehensive Capstone Evidence Pack

- **Project:** Makerere Student Support & Onboarding Triage Agent (BSE4104)
- **Compiled By:** Mpanga Marvin Joseph (AI Engineering Lead & DevOps)
- **Repository:** `https://github.com/marvinmpanga/Makerere-Student-Support-Agent`

---

## 1. End-to-End Artifact & Evidence Index

| Task Area | ClickUp Task Name | Primary Code / Doc Artifact | Verification & Trace Evidence |
| :--- | :--- | :--- | :--- |
| **Week 1** | Repository Scaffold & CI Automation Setup | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), [`pyproject.toml`](../../pyproject.toml), [`requirements.txt`](../../requirements.txt), [`.gitignore`](../../.gitignore) | GitHub Actions matrix (Python 3.11 & 3.12), Ruff, Bandit, `pip-audit`, Pytest coverage |
| **Week 2** | Implement Automated Evaluation Harness (Baseline) | [`src/eval/baseline_harness.py`](../../src/eval/baseline_harness.py), [`docs/decisions/adr_001_model_selection.md`](../decisions/adr_001_model_selection.md) | [`tests/test_baseline_harness.py`](../../tests/test_baseline_harness.py) (`2 passed`) |
| **Week 3** | Assemble Policy Corpus & Build Source Register | [`src/core/download_mak_policies.py`](../../src/core/download_mak_policies.py), [`knowledge/source_register.json`](../../knowledge/source_register.json), [`knowledge/mak-policies-manifest.csv`](../../knowledge/mak-policies-manifest.csv) | 66 official Makerere policies cataloged with URLs & metadata; [`tests/test_download_mak_policies.py`](../../tests/test_download_mak_policies.py) |
| **Week 3** | Build Ingestion, Chunking & Vector Indexing Pipeline | [`src/rag/ingest.py`](../../src/rag/ingest.py), `src/rag/vectorstore/` | 45 readable PDFs -> 1,045 chunks (512 tokens, 10% overlap) in ChromaDB; [`tests/test_rag_ingest.py`](../../tests/test_rag_ingest.py) (`7 passed`) |
| **Week 3** | Implement Retrieval & Grounded Context Injector | [`src/rag/retriever.py`](../../src/rag/retriever.py) | Injects mandatory `[Doc_ID, Page N]` source tags into LLM prompt context |
| **Week 4** | Connect LLM Tool-Calling Loop & Dispatcher | [`src/core/dispatcher.py`](../../src/core/dispatcher.py), [`src/tools/policy_search.py`](../../src/tools/policy_search.py) | Pydantic validation, non-blocking recovery, JSONL telemetry; [`tests/test_week4_tools.py`](../../tests/test_week4_tools.py) (`7 passed`) |
| **Week 5** | Build Agent Orchestrator & Loop Controller | [`src/agent/orchestrator.py`](../../src/agent/orchestrator.py) | Stateful `INTAKE -> PLAN -> ACT -> OBSERVE -> RESPOND` workflow; [`evidence/traces/agent_loop.jsonl`](../../evidence/traces/agent_loop.jsonl) |
| **Week 5** | Implement Max-Iteration Guard & Infinite-Loop Blocker | [`src/agent/guardrails.py`](../../src/agent/guardrails.py) | Hard 4-iteration ceiling & SHA-256 duplicate call breaker; [`tests/test_week5_agent.py`](../../tests/test_week5_agent.py) (`4 passed`) |
| **Week 6** | Build Prompt Injection & Adversarial Guardrail Layer | [`src/safety/guardrails.py`](../../src/safety/guardrails.py) | Regex + Base64 payload decoding + output leak scanner; [`evidence/traces/safety_audit.jsonl`](../../evidence/traces/safety_audit.jsonl); [`tests/test_week6_safety.py`](../../tests/test_week6_safety.py) (`6 passed`) |
| **Week 6** | Implement Non-Negotiable Refusal Engine | [`src/safety/refusal_engine.py`](../../src/safety/refusal_engine.py) | Zero-tolerance refusal for grade/fee/record mutation with Registrar escalation mapping |
| **Week 7** | Implement Automated Evaluation Harness | [`src/eval/runner.py`](../../src/eval/runner.py) | End-to-end benchmark runner; [`tests/test_week7_runner.py`](../../tests/test_week7_runner.py) (`3 passed`) |
| **Week 7** | Benchmark Retrieval (Precision@k, MRR, Hit Rate) | [`docs/evals/retrieval_benchmarks.md`](../evals/retrieval_benchmarks.md) | `MRR = 1.0000`, `Precision@3 = 88.89%`, `Hit Rate = 100%`, `Refusal Rate = 100%` |
| **Week 8** | Multi-Container Orchestration (`docker-compose.yml`) | [`docker-compose.yml`](../../docker-compose.yml), [`.dockerignore`](../../.dockerignore) | Single-command orchestration, persistent ChromaDB and trace volumes, healthcheck |
| **Week 8** | Production Container Image & REST API | [`Dockerfile`](../../Dockerfile), [`src/main.py`](../../src/main.py), [`src/api/`](../../src/api/) | Non-root `appuser`, `/health`, `/api/v1/chat`, `/api/v1/policy/search`; [`tests/test_api.py`](../../tests/test_api.py) (`9 passed`) |
| **Week 8** | Final GitHub Release & Automated Workflows | [`RELEASE.md`](../../RELEASE.md), [`.github/workflows/release.yml`](../../.github/workflows/release.yml), [`.github/workflows/docker.yml`](../../.github/workflows/docker.yml) | Automated GitHub release packaging, container build & GHCR publish |

---

## 2. Reproducibility Commands

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Download Makerere policy corpus (66 PDFs)
python -m src.core.download_mak_policies

# 3. Build ChromaDB vector index (512 tokens, 10% overlap)
python -m src.rag.ingest --embedder local --reset

# 4. Run quantitative benchmark evaluation suite
python -m src.eval.runner

# 5. Run lint and unit test suite (53 tests)
ruff check src tests
pytest -q

# 6. Run containerized stack
docker compose up -d
curl http://localhost:8000/health
```
