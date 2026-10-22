# Makerere Student Support & Onboarding Triage Agent

[![CI](https://github.com/marvinmpanga/Makerere-Student-Support-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/marvinmpanga/Makerere-Student-Support-Agent/actions/workflows/ci.yml)
![Lint: Ruff](https://img.shields.io/badge/lint-ruff-261230)
![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow)
![Tests: Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC)
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

## Project Overview
This project implements a prototype Retrieval-Augmented Generation (RAG) pipeline for the Makerere Student Support Agent. The system is designed to answer student questions using approved policy and institutional guidance rather than relying on model memory alone.

The current milestone focuses on:
- offline knowledge ingestion and chunking
- retrieval from approved knowledge sources
- grounded prompt construction
- answer validation and refusal on unsupported questions
- API wiring for the RAG layer
- architecture and pipeline documentation
- automated tests for the prototype behavior

This is intentionally a prototype and not yet a production-ready system.

---

## Current Architecture
The repository includes a RAG architecture and pipeline specification under the `docs/rag/` folder:
- `docs/rag/README.md` - pipeline specification and responsibility boundaries
- `docs/rag/rag-architecture-diagram.md` - Mermaid diagram of the RAG flow

The implemented prototype covers the core loop:
1. source documents are read from the knowledge store
2. text is normalized and chunked
3. documents are indexed in memory for retrieval
4. student questions are matched against the relevant content
5. grounded context is assembled into the prompt
6. answers are only returned when evidence is available
7. unsupported questions trigger a refusal instead of a hallucinated answer

---

## Project Structure
- `docs/` - architecture, requirements, reports, and evaluation docs
- `docs/rag/` - RAG pipeline specification and architecture diagrams
- `knowledge/` - controlled policy register, document metadata, and raw source material
- `prompts/` - versioned prompt templates and specifications
- `src/` - application logic, RAG pipeline, deterministic checks, and API exposure
- `tests/` - unit and integration tests for the prototype
- `evidence/` - execution traces and project evidence

---

## RAG Prototype Components
- `src/core/rag_pipeline.py` - document ingestion, chunking, retrieval, grounding prompt builder, and answer validation
- `src/api/rag.py` - API endpoint for question answering
- `src/core/download_mak_policies.py` - Makerere policy source downloader
- `src/core/llm_harness.py` - LLM execution harness with traces and observability
- `src/main.py` - FastAPI application setup and route registration

---

## Environment Setup
This project requires a real Python environment. The repository was verified successfully using a local virtual environment:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest -q
```

On Windows, use the venv Python directly instead of the broken `py` app alias path.

---

## Verified Status
The current repository state has been verified in a real Python environment.

Command run:

```bash
.\.venv\Scripts\python.exe -m pytest -q
```

Result:

```text
14 passed, 3 warnings in 1.15s
```

The warnings are dependency-level deprecations from FastAPI/Starlette and do not block the implementation.

---

## Download Makerere Policies
Install the project dependencies and run the strict source downloader:

```bash
python -m pip install -r requirements.txt
python -m src.core.download_mak_policies
```

Policy files are stored under `knowledge/raw/mak-policies/`. The downloader also writes `knowledge/mak-policies-manifest.csv` and records each downloaded document in `knowledge/source_register.json` with its official source URL.

---

## Current Development Stage
This project is now at the first implementation milestone for the RAG layer:
- pipeline design is documented
- chunking and retrieval are implemented
- grounded prompt construction is working
- API wiring is active
- tests are passing in the real environment

The next stage will add:
- real Makerere policy corpus ingestion
- embeddings and vector storage
- prompt/version logging
- answer-grounding validation
- auth and observability scaffolding
- a more robust retrieval stack for production use

---

## Notes
The RAG layer is intentionally conservative. It refuses unsupported questions instead of guessing, which aligns with the project’s requirements for policy-grounded, auditable student support responses.
