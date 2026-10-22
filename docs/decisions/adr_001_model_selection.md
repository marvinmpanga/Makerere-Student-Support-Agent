# ADR-001: Foundation Model Selection (Gemini 1.5 Flash)

- **Status:** Accepted
- **Date:** 2026-09-14
- **Owner:** Mpanga Marvin Joseph (AI Engineering Lead & DevOps)
- **Task ID:** W2-01

## Context
The Makerere Student Support & Onboarding Triage Agent requires a foundation Large Language Model (LLM) capable of low-latency administrative triage, strict adherence to structured JSON output contracts, and future context grounding across 66 official Makerere University policy documents.

## Decision
We select **Google Gemini 1.5 Flash (`gemini-1.5-flash`)** as the primary baseline foundation model for the Makerere Student Support & Onboarding Triage Agent, retaining **OpenAI GPT-4o-mini** as the secondary benchmark comparator.

## Technical Justification

| Criterion | Gemini 1.5 Flash | GPT-4o-mini (Comparator) | Llama 3.1 8B (Self-Hosted) | Decision Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Context Window** | **1,000,000+ tokens** | 128,000 tokens | 128,000 tokens | Large window accommodates multi-page Makerere policy excerpts and multi-turn history without truncation. |
| **Latency (TTFT)** | Sub-second typical TTFT | Sub-second typical TTFT | Hardware-dependent | Flash tier satisfies interactive student support P95 latency targets (<3.0s). |
| **Cost & Accessibility** | Generous free tier + lowest Flash token pricing | Paid API tier required | GPU hosting cost overhead | Enables team-wide evaluation and CI dry runs within student capstone budget constraints. |
| **Structured Output & Tool Calling** | Native `response_mime_type="application/json"` & function declarations | Native JSON mode & tool calling | Requires external grammar enforcement | Enforces deterministic Pydantic/JSON triage contracts for Week 2–4 deliverables. |
| **Data Privacy & Governance** | Minimized context; API keys in `.env` secret store | Same controls | Full local control | No raw student PII is transmitted outside approved read-only tool boundaries. |

## Hyperparameter Configuration
- `temperature = 0.2`: Minimizes generative variance so policy citations and procedural steps remain deterministic.
- `top_p = 0.95`: Retains natural phrasing while constraining low-probability token sampling.
- `max_output_tokens = 1024`: Bounds response length and cost per student interaction.
- `response_mime_type = "application/json"`: Enforced whenever structured triage output is requested.

## Consequences
- **Positive:** Fast iteration on prompt engineering (`v1.0` -> `v1.1`), native JSON mode support in `src/core/llm.py`, and seamless integration with the Week 3 RAG pipeline.
- **Negative / Risks:** Free-tier rate limits (`429 RESOURCE_EXHAUSTED`) during bulk embedding jobs require exponential backoff or a local ONNX embedding fallback (`all-MiniLM-L6-v2`) in `src/rag/ingest.py`.
