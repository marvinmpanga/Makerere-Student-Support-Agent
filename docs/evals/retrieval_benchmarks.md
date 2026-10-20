# Retrieval Benchmarking Report (Precision@k, MRR, Hit Rate)

- **Owner:** Mpanga Marvin Joseph (AI Engineering Lead & DevOps)
- **Date:** 2026-10-19
- **Vector Collection:** `makerere_policies` (`src/rag/vectorstore/`)
- **Corpus Size:** 45 indexed Makerere University policy PDFs (1,045 semantic chunks at 512 tokens, 10% overlap)
- **Embedding Model:** `all-MiniLM-L6-v2` (ONNX local embedder) / `gemini-embedding-001`
- **Evaluation Runner:** [`src/eval/runner.py`](../../src/eval/runner.py)

---

## 1. Aggregate Retrieval & Pipeline Metrics

| Metric | Score | Target Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Mean Reciprocal Rank (MRR)** | **1.0000** | $\ge 0.80$ | **PASS** |
| **Precision@3 (`P@3`)** | **0.8889 (88.89%)** | $\ge 0.75$ | **PASS** |
| **Top-3 Hit Rate (`Recall@3 > 0`)** | **100.0% (3/3)** | $\ge 90.0\%$ | **PASS** |
| **Citation Compliance Rate (`[Doc_ID, Page N]`)** | **100.0%** | $100.0\%$ | **PASS** |
| **Tool Call Accuracy (`search_policy_docs`)** | **100.0%** | $\ge 95.0\%$ | **PASS** |
| **Adversarial Safety Refusal Rate** | **100.0%** | $100.0\%$ | **PASS** |
| **Latency P50 / P95** | **440.3 ms / 2,629.3 ms** | $< 3,000\text{ ms}$ | **PASS** |

---

## 2. Per-Query Retrieval Breakdown (`k = 3`)

| Scenario ID | Student Query | Top-3 Retrieved Citations | Expected Policy IDs | Hit@3 | Reciprocal Rank (`RR`) | `Precision@3` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `EVAL-01` | *What are the rules and penalties for examination malpractice?* | `[mak-policy-0066, Pages 1-3]`, `[mak-policy-0056, Pages 7-8]`, `[mak-policy-0043, Pages 127-129]` | `mak-policy-0066`, `mak-policy-0056`, `mak-policy-0043` | `1.0` | `1.0000` | `1.0000` |
| `EVAL-02` | *How is student hostel and hall accommodation allocated?* | `[mak-policy-0010, Pages 64-65]`, `[mak-policy-0055, Pages 11-12]`, `[mak-policy-0043, Pages 17-19]` | `mak-policy-0055`, `mak-policy-0010`, `mak-policy-0043` | `1.0` | `1.0000` | `1.0000` |
| `EVAL-03` | *When must tuition and functional fees be paid by students?* | `[mak-policy-0043, Pages 72-74]`, `[mak-policy-0043, Pages 78-79]`, `[mak-policy-0043, Pages 74-75]` | `mak-policy-0043`, `mak-policy-0002` | `1.0` | `1.0000` | `0.6667` |

---

## 3. Key Findings & Failure Analysis Notes
1. **High First-Rank Precision (`MRR = 1.0`):** Every evaluated student policy query ranked a verified relevant Makerere policy chunk at rank 1.
2. **Scanned PDF Gap (`mak-policy-0002`):** In `EVAL-03`, `mak-policy-0043` (*Makerere Academic Policies Manual Revised 2025*) returned the fee payment rules because `mak-policy-0002` (*Makerere University Fees Policy 2016*) is one of 21 scanned image-only PDFs that require OCR pre-processing during ingestion.
