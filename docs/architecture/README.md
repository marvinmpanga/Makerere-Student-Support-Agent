# Systems Design Architecture

This folder contains the logical architecture for the Makerere Student Support and Onboarding Triage Agent.

## Diagram set

| ID | View | Purpose |
|---|---|---|
| 01 | System context | People, system boundary, approved external policy sources |
| 02 | Logical containers | Major system responsibilities and data/control boundaries |
| 03 | Components | Internal responsibilities and controlled interfaces |
| 04 | Responsibility boundary | AI versus deterministic versus human authority |
| 05 | Policy sequence | Grounded policy-question processing |
| 06 | Student-status sequence | Authenticated, read-only status lookup |
| 07 | Ticket sequence | Draft, human review, explicit confirmation, persistence |
| 08 | End-to-end activity | Supported, unsupported, prohibited, failure, and approval paths |

## Design scope

Included: logical components, responsibilities, interfaces, data flow, control flow, trust boundaries, validation, authorization, grounding, auditability, and human approval.

Excluded: deployment topology, cloud providers, hosting, containers as infrastructure, Docker, Kubernetes, networks, load balancers, and production operations.

## Authority rules

- AI output is generated content and is not authoritative.
- Deterministic controls enforce authentication, authorization, validation, safety, tool access, rate limiting, auditing, and persistence.
- Student status is accessed through a read-only deterministic capability.
- Support tickets are persisted only after explicit student confirmation.
- Prohibited academic, financial, disciplinary, and admissions decisions are rejected or escalated.

## Rendering

The files use Mermaid source blocks and render in GitHub Markdown and compatible VS Code extensions. For a polished submission, import or reproduce each view in draw.io and export PDF/SVG while keeping these Markdown files as the version-controlled specification.
