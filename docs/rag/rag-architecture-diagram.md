# RAG Architecture Diagram

```mermaid
flowchart TB
    subgraph Sources[Approved Source Documents]
        S1[Policy PDFs / pages]
        S2[FAQs]
        S3[Procedures]
        S4[Approved guidance]
    end

    subgraph Ingestion[Offline Ingestion Pipeline]
        I1[Source discovery]
        I2[Document parsing]
        I3[Text cleaning]
        I4[Chunking and metadata tagging]
        I5[Embedding generation]
        I6[Vector index storage]
    end

    subgraph Retrieval[Online Retrieval Pipeline]
        Q1[Student question]
        Q2[Scope / route check]
        Q3[Vector retrieval]
        Q4[Re-ranking and filtering]
        Q5[Grounded context assembly]
        Q6[Prompt composition]
        Q7[LLM generation]
    end

    subgraph Validation[Grounding and Safety]
        V1[Evidence support check]
        V2[Conflict detection]
        V3[Answer safety gate]
        V4[Fallback / escalation]
    end

    subgraph Human[Human Approval Boundary]
        H1[Student-status verification]
        H2[Disciplinary / financial / eligibility decisions]
        H3[Ticket approval]
    end

    S1 --> I1
    S2 --> I1
    S3 --> I1
    S4 --> I1
    I1 --> I2 --> I3 --> I4 --> I5 --> I6

    Q1 --> Q2 --> Q3 --> Q4 --> Q5 --> Q6 --> Q7
    I6 --> Q3
    Q7 --> V1 --> V2 --> V3
    V3 -->|Supported| O1[Grounded answer]
    V3 -->|Unsupported| V4
    V4 --> H1
    V4 --> H2
    V4 --> H3

    Q7 --> Trace[Observability / trace log]
    I6 --> Trace
    V1 --> Trace
``` 

## Interpretation

This diagram shows the essential RAG loop:

- approved documents are loaded offline,
- text is chunked and vectorized,
- a student question triggers retrieval of relevant chunks,
- the retrieved evidence is inserted into the prompt,
- the LLM answers only from that evidence,
- the answer is validated and escalated if unsupported.
