# Prompt Version Changelog
<!-- Versioning scaffold for W2-03 | Author: Nakyanzi Faridah | Date: 2026-09-16 -->

Track all prompt changes across versions to maintain reproducibility of each baseline
and audit the effect of optimisations on the 10-case evaluation suite.

---

## v1.0 — 2026-09-16 — Baseline Release

**Author:** Nakyanzi Faridah (Project & Requirements Lead / AI Engineer)
**ClickUp Task:** W2-03 (123rgxu65nw)
**Status:** Released

### Summary
Initial production-ready prompt authored as part of the BSE4104 capstone sprint.
Establishes the full specification and executable system prompt for the Makerere University
Student Support & Administrative Triage Agent (MAK-STA).

### Changes Introduced
- Defined MAK-STA persona with explicit authority boundaries and 5 functional scope areas.
- Authored input payload contract: 5 typed fields (`student_id`, `programme`,
  `academic_year`, `query`, `context_documents`) with constraints and RAG chunk format.
- Established 7 hard-refusal triggers with required response actions per trigger.
- Defined soft-guardrail rules for partial-grounding scenarios.
- Published full output JSON schema with 6 fields:
  - `inquiry_category` (enum: 6 values)
  - `confidence_score` (float 0.0–1.0)
  - `procedural_guidance` (array of strings, minItems: 1)
  - `policy_citations` (pattern: `mak-policy-NNNN`, verified IDs only)
  - `requires_ticket_escalation` (boolean)
  - `ticket_draft` (object with `student_confirmation_required: true` const, or null)
- Documented canonical example for "missing exam mark" inquiry (BSE4104).
- Authored inquiry routing table mapping 6 categories to policy docs and escalation offices.
- Specified 6 edge-case protocols (no-context, ambiguous category, multi-issue, missing
  fields, non-English, safety-critical).
- Wrote executable `system_prompt.md` with hard-prohibition list and strict JSON-only
  output instruction (no markdown fences).

### Files
- `prompts/v1.0/prompt_spec.md` — full specification document
- `prompts/v1.0/system_prompt.md` — raw executable system prompt

### Evaluation Baseline
To be evaluated against a 10-case test suite covering:
1. Missing exam mark inquiry
2. Course registration / provisional admission
3. Retake eligibility query
4. Tuition fee payment procedure
5. AIMS portal login issue
6. Hard refusal: grade alteration request
7. Hard refusal: CGPA manipulation
8. Hard refusal: fee waiver request
9. Ambiguous / multi-issue query
10. Query with no context documents

---

## v1.1 — TBD — Post-Evaluation Optimisations

**Author:** TBD
**Status:** Planned — awaiting 10-case evaluation run results

### Planned Focus Areas
- [ ] Record failure cases from the evaluation run with evidence and severity ratings.
- [ ] Review and tighten JSON adherence: investigate cases where the model added markdown
      fences or prose outside the JSON object.
- [ ] Tighten grounding refusal triggers: evaluate whether `confidence_score` thresholds
      (0.30 / 0.65) correctly gate escalation in edge cases.
- [ ] Review `policy_citations` precision: audit any IDs cited that are not in
      `knowledge/source_register.json`.
- [ ] Reassess `inquiry_category` routing accuracy on ambiguous multi-issue queries.
- [ ] Evaluate `ticket_draft` quality: assess whether `case_details` is actionable for
      the receiving office without the student_id.
- [ ] Document any expected regressions introduced by tightening rules.
- [ ] Update `system_prompt.md` with refined instructions targeting identified failures.

### Release Notes
_No v1.1 changes released yet. Update this section after evaluation._

---

## Version Naming Convention

| Version | Meaning                                           |
|---------|---------------------------------------------------|
| 1.0     | Baseline — first evaluated release                |
| 1.x     | Minor — prompt text edits, no schema changes      |
| 2.0     | Major — schema breaking changes or full rewrite   |

All versions retain their `system_prompt.md` file in their respective `prompts/vX.Y/`
directory for reproducibility. The evaluation harness in `tests/` must reference the
specific version under test.
