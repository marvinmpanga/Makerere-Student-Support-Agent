# Document Retrieval & Grounding Failure Analysis

**Project:** Makerere Student Support & Onboarding Triage Agent  
**Course:** BSE4104 – Emerging Trends in Software Engineering  
**Prepared by:** Lubega Lawrence Kiribwa  
**Role:** Quality & Security Lead  
**Academic Year:** 2026/2027  
**Branch:** `system_archtecture`

## 1. Introduction

The Makerere Student Support & Onboarding Triage Agent is intended to provide reliable guidance on registration, examination procedures, retake policies, programme transfers, and other student-support matters. For this system, generating a relevant answer is not enough: policy information should be supported by approved Makerere University documents.

This analysis examines retrieval and grounding weaknesses observed in the US-01 to US-10 prompt evaluation, identifies risks and possible causes, and recommends improvements.

## 2. Objectives

- Determine whether the baseline demonstrates retrieval from approved university documents.
- Identify institutional claims that could not be verified from retrieved sources.
- Distinguish plausible model-generated information from evidence-grounded guidance.
- Recommend retrieval, grounding, and testing improvements.

## 3. Current System Analysis

The LLM harness is implemented in `src/core/llm_harness.py`. It sends the user's query to the configured Gemini model and records execution information such as request identifiers, latency, token usage, and raw model output. The API endpoint is `POST /api/v1/llm/execute`.

During the evaluation, the model generated structured answers, but the execution path did not demonstrate retrieval from an approved Makerere document collection or grounding of answers in retrieved passages.

**Key finding:** LLM response generation was demonstrated; approved-source retrieval and grounding were not demonstrated by the evaluated execution path.

## 4. Evidence of Retrieval and Grounding Failures

### 4.1 US-01: Orientation and Registration

The agent generated a three-step registration checklist and named Makerere-related sources. However, the evaluation did not demonstrate that the documents were retrieved or that the requirements were checked against their contents.

**Failure:** Source retrieval and requirement accuracy could not be independently verified.  
**Risk:** Students might rely on outdated, incomplete, or incorrect registration requirements.

### 4.2 US-02: Missing Examination Mark

The agent provided a reporting procedure, suggested documents, escalation channels, and a deadline involving a 30-day reporting period. Retrieval of the relevant examination regulations was not demonstrated.

**Failure:** Policy-dependent claims lacked verified evidence from an approved source.  
**Risk:** A student could miss the correct deadline or follow an incorrect escalation procedure.

### 4.3 US-04: Retake Policy Guidance

The agent discussed retake fee calculations, credit-unit limits, and transcript handling. It correctly refused to modify transcript records, but the fee and credit-unit guidance was not verified against approved university documents.

**Failure:** Authoritative grounding of retake guidance was not demonstrated.  
**Risk:** Incorrect information could affect financial planning or course registration.

### 4.4 US-07: Unsupported Query Handling

The agent recognized that a request about a university-owned private jet for personal travel was unsupported. However, it then generated additional claims about official travel, transport procedures, approvals, and responsible offices.

**Failure:** Recognizing an unsupported question did not prevent further unverified institutional claims.  
**Risk:** Users may mistake plausible-sounding information for official policy.

### 4.5 US-08: Change of Programme

The agent provided transfer guidance on cut-off criteria, application windows, eligibility, and Academic Registrar routing. The policy details were not demonstrated as retrieved from approved sources.

**Failure:** The authority of the stated rules and deadlines could not be established.  
**Risk:** Students could misunderstand eligibility or submit applications incorrectly.

## 5. Root Cause Analysis

### 5.1 No Demonstrated Retrieval-Augmented Generation

The evaluated path sends queries to the language model but does not demonstrate retrieval from an approved university document collection. The model may therefore answer from learned patterns rather than current authoritative information.

### 5.2 No Enforced Source-Grounding Requirement

The baseline did not demonstrate a requirement that policy claims be supported by retrieved evidence before a response is returned.

### 5.3 Missing Evidence Validation

The evaluation did not demonstrate automated checks that cited documents exist, that passages support the claims, or that the sources are approved and current.

### 5.4 Weak Unsupported-Query Fallback

US-07 showed that the model could reject the premise and then continue generating related institutional information. A controlled fallback is needed to prevent speculation when evidence is unavailable.

### 5.5 Missing Document Version Controls

The evaluated workflow did not demonstrate checks for publication dates, effective dates, superseded policies, or approved versions.

## 6. Recommended Solution: Retrieval-Augmented Generation

Introduce Retrieval-Augmented Generation (RAG) so the agent retrieves relevant passages from approved documents and uses them as evidence when responding.

### Proposed Workflow

1. **Document collection:** Obtain approved Makerere policies, regulations, registration instructions, examination procedures, forms, and official guidance.
2. **Document processing:** Extract text and preserve titles, section headings, versions, and effective dates where available.
3. **Chunking:** Divide documents into meaningful passages while preserving context.
4. **Indexing:** Store passages in a searchable index. Semantic/vector search can be combined with keyword search.
5. **Retrieval:** Find passages relevant to the student's question.
6. **Evidence validation:** Check relevance and approved-source status.
7. **Grounded generation:** Instruct the model to answer from retrieved evidence, not unsupported assumptions.
8. **Citations:** Include document titles and relevant sections or page references where available.
9. **Fallback:** If evidence is insufficient, state that the policy could not be verified and direct the student to an appropriate official office.
10. **Logging:** Record retrieved source identifiers, responses, and evaluation outcomes for auditing.

## 7. Proposed Grounding Rules

- Policy claims must be supported by retrieved evidence from approved documents.
- The model must not invent document titles, section numbers, deadlines, fees, forms, or eligibility requirements.
- Citations must refer to documents actually retrieved, and passages must support the claims cited.
- Conflicting sources must be handled using an approved source-priority and version policy.
- If evidence is missing or insufficient, the agent must state that it cannot verify the answer.
- Unsupported questions must receive a controlled fallback rather than speculative policy guidance.
- High-impact cases, including transcript changes and fee waivers, must require appropriate authorization and human review.
- Logs must not unnecessarily expose student personal information or secrets.

These controls should be enforced through application logic and testing, not only through model instructions.

## 8. Proposed Test Plan

### Test 1: Supported Policy Question
**Input:** Ask about a registration requirement covered by an approved document.  
**Expected result:** Retrieve the relevant source, answer from it, and provide a verifiable citation.

### Test 2: Unsupported Policy Question
**Input:** Ask for an official policy not covered by the approved collection.  
**Expected result:** State that the policy could not be verified and do not invent requirements or approval procedures.

### Test 3: Missing Source
**Input:** Ask for a fee or deadline absent from the indexed documents.  
**Expected result:** Do not guess; explain that the information could not be verified and direct the student to an official channel.

### Test 4: Conflicting Documents
**Input:** Ask a question where two retrieved documents conflict.  
**Expected result:** Apply configured authority/version rules or disclose the conflict and escalate.

### Test 5: Outdated Document
**Input:** Ask about a procedure with both an outdated document and a verified current version in the collection.  
**Expected result:** Use the approved current version.

### Test 6: Citation Verification
**Input:** Ask a policy question requiring several details.  
**Expected result:** Each important policy claim is supported by relevant retrieved passages; citations are not fabricated.

### Test 7: Prompt Injection in Retrieved Documents
**Input:** Include document text that attempts to override the agent's rules or request secrets.  
**Expected result:** Treat retrieved text as evidence, not privileged instructions, and preserve safety controls.

## 9. Evaluation Metrics

- **Retrieval success rate:** Share of supported questions for which relevant approved passages are retrieved.
- **Citation accuracy:** Share of citations that refer to real, retrieved, approved documents.
- **Grounded claim rate:** Share of material policy claims supported by retrieved evidence.
- **Unsupported-claim rate:** Share of policy claims lacking sufficient source support.
- **Abstention accuracy:** Whether the agent declines to provide official answers when evidence is insufficient.
- **Document freshness compliance:** Whether sources comply with document-version and effective-date rules.
- **Latency:** Time required for retrieval and response generation.

Evaluate these metrics against a manually reviewed test set. Agree on numerical targets before claiming that the system meets them.

## 10. Implementation Priorities

1. Establish an approved, version-controlled collection of Makerere documents.
2. Implement document processing and retrieval.
3. Modify the LLM harness to provide retrieved evidence as context.
4. Require source-supported answers and verifiable citations.
5. Implement controlled abstention and unsupported-query handling.
6. Add automated tests for the seven scenarios above.
7. Compare the improved implementation with the original US-01 to US-10 baseline.
8. Retain test results and execution traces for regression testing.

## 11. Conclusion

The analysis identified a significant limitation in the current baseline: the agent can generate detailed institutional guidance, but the evaluated execution path did not demonstrate retrieval and verification of approved Makerere University documents. The previous evaluation showed this weakness in registration, missing examination marks, retake policies, unsupported queries, and programme transfers.

The recommended solution is to introduce a RAG pipeline based on approved documents, enforce evidence-grounded generation, validate citations, and use controlled fallback responses when information cannot be verified.

As Quality & Security Lead, the priority is to ensure that responses are not judged only by how convincing they sound, but by whether they are supported by authoritative evidence, traceable, appropriately qualified, and safe for students to rely on.

**Expected outcome:** A student-support agent that provides verifiable guidance, identifies evidence gaps, avoids unsupported policy claims, and escalates uncertain or high-impact matters appropriately.

## 12. Evidence and Project References

This analysis is based on the previous US-01 to US-10 evaluation and the current baseline implementation.

- `src/core/llm_harness.py` — LLM execution and tracing.
- `src/api/llm.py` — LLM execution API endpoint.
- `src/schemas/llm.py` — request and response schemas.
- `evidence/traces/llm_execution.jsonl` — execution traces, where retained locally.

The `.env` file containing the Gemini API key must remain excluded from version control.

**Prepared by:** Lubega Lawrence Kiribwa  
**Role:** Quality & Security Lead  
**Project:** Makerere Student Support & Onboarding Triage Agent  
**Course:** BSE4104 – Emerging Trends in Software Engineering
