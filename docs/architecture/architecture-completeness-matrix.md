# Architecture Completeness Matrix

| Requirement / control | Architectural element | Diagram(s) | Enforcement / verification | Status |
|---|---|---|---|---|
| Student asks for support | Student Client, REST API | 01, 02, 05, 08 | Request flow | Represented |
| Grounded policy guidance | RAG Retriever, approved corpus, grounding validator | 02, 03, 05, 08 | Evidence sufficiency check and citations | Represented |
| Verified student status | Student Record Tool, application data | 02, 03, 06, 08 | Authentication, RBAC, read-only tool | Represented |
| Ticket drafting | Agent Orchestrator, Ticket Management Tool | 02, 03, 07, 08 | Structured draft validation | Represented |
| Human review and edit | Human Approval Controller | 02, 03, 04, 07, 08 | Explicit Confirm & Submit gate | Represented |
| No persistence before confirmation | Backend workflow and Ticket Management Tool | 02, 04, 07, 08 | Confirmation checked before persistence | Represented |
| Authentication and authorization | Authentication Service, RBAC | 03, 05, 06, 07, 08 | Reject unauthenticated or unauthorized requests | Represented |
| Input and schema validation | Validation components | 03, 05, 06, 07, 08 | Reject malformed requests | Represented |
| Rate limiting and auditability | Rate Limiter, Audit Logger | 03, 07, 08 | Record actions and check submission limits | Represented |
| Prohibited actions | Safety guard and prohibited zone | 04, 08 | Reject and explain boundary | Represented |
| No direct AI database access | Container/component boundary | 02, 03, 06, 07 | Forbidden relationship shown | Represented |
| Unsupported question handling | Safety/policy guard | 05, 08 | Unsupported path and escalation | Represented |
| Failure and rejection paths | Alternate flows | 05, 06, 07, 08 | Authentication, validation, grounding, and human rejection branches | Represented |
| Physical deployment architecture | Excluded by scope | None | Not applicable to systems-design deliverable | Excluded |

The repository currently contains three explicit user stories. Add the authoritative US-01 through US-10 wording when supplied by the team before claiming exact story-level traceability.
