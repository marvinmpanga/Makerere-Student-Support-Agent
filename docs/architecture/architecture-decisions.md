# Architecture Decisions

## AD-01: Separate AI from deterministic execution

**Requirement:** Support natural-language understanding while respecting strict safety boundaries.

**Decision:** AI handles interpretation, retrieval, synthesis, classification, and drafting. The backend validates AI proposals before tool execution.

**Reason:** Generated output is non-authoritative and must not bypass security or business controls.

**Implementation:** Technology remains TBD unless specified by the project.

## AD-02: Use controlled capabilities for student status and tickets

Student status is accessed through a read-only deterministic capability. Ticket drafting produces structured draft content; persistence occurs only through the controlled workflow after confirmation.

## AD-03: Require explicit human confirmation

The workflow is Draft -> Review/Edit -> Confirm & Submit -> deterministic validation -> persistence. The student remains the authority for the consequential submission.

## AD-04: Ground policy answers in approved sources

Policy questions pass through retrieval and grounding/citation validation before response generation, reducing unsupported claims and making answers reviewable.

## AD-05: Fail closed for prohibited requests

The safety/policy guard rejects prohibited actions and escalates cases requiring authorized human handling.

## AD-06: Keep implementation technology logical/TBD

No cloud provider, database vendor, hosting topology, Docker, Kubernetes, or external SIS integration is introduced in this systems-design package.
