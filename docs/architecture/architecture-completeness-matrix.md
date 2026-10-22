# Architecture Completeness Matrix

| Requirement / control | Architectural element | Diagram(s) | Enforcement / verification | Status | Code Location |
|---|---|---|---|---|---|
| Student asks for support | Student Client, REST API | 01, 02, 05, 08 | Request flow | Implemented | `src/main.py` |
| Grounded policy guidance | RAG Retriever, approved corpus, grounding validator | 02, 03, 05, 08 | Evidence sufficiency check and citations | Implemented | `src/core/rag_pipeline.py`, `src/api/rag.py` |
| Verified student status | Student Record Tool, application data | 02, 03, 06, 08 | Authentication, RBAC, read-only tool | Implemented | `src/core/tools.py`, `src/api/tools.py` |
| Ticket drafting | Agent Orchestrator, Ticket Management Tool | 02, 03, 07, 08 | Structured draft validation | Implemented | `src/core/tools.py`, `src/api/tools.py` |
| Human review and edit | Human Approval Controller | 02, 03, 04, 07, 08 | Explicit Confirm & Submit gate | Implemented | `src/core/hitl.py`, `src/api/hitl.py` |
| No persistence before confirmation | Backend workflow and Ticket Management Tool | 02, 04, 07, 08 | Confirmation checked before persistence | Implemented | `src/core/tools.py`, `src/core/hitl.py` |
| Authentication and authorization | Authentication Service, RBAC | 03, 05, 06, 07, 08 | Reject unauthenticated or unauthorized requests | Designed | TBD |
| Input and schema validation | Validation components | 03, 05, 06, 07, 08 | Reject malformed requests | Implemented | `src/schemas/*.py` |
| Rate limiting and auditability | Rate Limiter, Audit Logger | 03, 07, 08 | Record actions and check submission limits | Designed | TBD |
| Prohibited actions | Safety guard and prohibited zone | 04, 08 | Reject and explain boundary | Implemented | `prompts/system_prompt_v1.txt` |
| No direct AI database access | Container/component boundary | 02, 03, 06, 07 | Forbidden relationship shown | Implemented | `src/core/tools.py` |
| Unsupported question handling | Safety/policy guard | 05, 08 | Unsupported path and escalation | Implemented | `src/core/llm_harness.py` |
| Failure and rejection paths | Alternate flows | 05, 06, 07, 08 | Authentication, validation, grounding, and human rejection branches | Implemented | End-to-end APIs |
| Physical deployment architecture | Excluded by scope | None | Not applicable to systems-design deliverable | Excluded | N/A |

The repository currently contains three explicit user stories. Add the authoritative US-01 through US-10 wording when supplied by the team before claiming exact story-level traceability.

