# Foundation Model Selection Note

**Project:** Makerere Student Support & Onboarding Triage Agent  
**Decision owner:** AI Engineering Lead / DevOps  
**Decision:** Use Google Gemini 1.5 Flash (`gemini-1.5-flash`) for the Week 2 baseline.

## Evaluation

Gemini 1.5 Flash is the best fit for an economical, policy-grounded baseline. Its
large context window (over 1M tokens, subject to the active API limit) supports
future ingestion of the 66 registered Makerere policy documents and primary
on-ground artifacts without prematurely introducing a vector database. It also
supports generation configuration for JSON MIME output, making the triage
contract machine-readable.

GPT-4o-mini is retained as an architectural comparator. Both models are viable
for low-latency classification and structured responses, but the final choice
must be confirmed against the current provider price sheets and a measured
Makerere evaluation set. Prices and TTFT are time-sensitive: the evaluation
record should capture input/output price per 1M tokens and p50/p95 TTFT at the
same prompt and output sizes rather than hard-code stale figures in this note.

| Criterion | Gemini 1.5 Flash | GPT-4o-mini comparator | Decision implication |
| --- | --- | --- | --- |
| Token pricing | Low-cost Flash tier; verify current input/output USD per 1M tokens | Low-cost mini tier; verify current input/output USD per 1M tokens | Measure total monthly cost using real prompt and policy-token volumes |
| TTFT | Expected low latency; benchmark p50/p95 in the target region | Expected low latency; benchmark with the same harness | Prefer the lower measured p95 that still meets answer quality |
| Context window | Greater than 1M tokens on the selected model/API configuration | Smaller context than Gemini 1.5 Flash | Gemini better supports complete policy ingestion in later phases |
| Structured output | `response_mime_type: "application/json"` and schema-oriented prompting | JSON response features available through the OpenAI API | Gemini fits the Week 2 direct-client contract |
| Makerere privacy | Send only approved, minimized context; keep API keys in environment/secret storage and review provider retention terms | Apply the same controls and review OpenAI terms | No student record should be sent without an approved data-handling decision |

## Hyperparameters and guardrails

- `temperature: 0.2` reduces variation so compliance guidance remains
  repeatable while allowing limited language flexibility.
- `top_p: 0.95` preserves useful wording diversity without materially widening
  the sampling distribution; it is held constant for comparable evaluations.
- `response_mime_type: "application/json"` is enabled for forced-JSON calls so
  downstream validation receives a machine-readable response. Parsing remains
  defensive because provider responses can still be malformed or interrupted.
- The baseline uses only the controlled `knowledge/source_register.json`
  corpus, currently 66 Makerere policy records, and approved primary
  on-ground artifacts. Full retrieval, tool calling, and persistent stores are
  deliberately deferred to Weeks 3-5.

This is a baseline engineering decision, not a claim that either provider is
approved for unrestricted student data. Before production use, the team must
complete privacy review, provider terms review, quota planning, and a blind
quality/latency/cost comparison against GPT-4o-mini.