"""W3-04: Retrieval Engine & Grounded Citation Context Injector.

Queries the ChromaDB ``makerere_policies`` collection built by ``src/rag/ingest.py``
and formats a grounded prompt block that guarantees every retrieved policy excerpt
carries its ``[Doc_ID, Page N]`` / ``[Doc_ID, Pages N-M]`` citation tag.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.rag.ingest import DEFAULT_VECTORSTORE, Embedder
from src.tools.policy_search import PolicySearchHit, search_policy_docs


@dataclass
class GroundedRetrievalPayload:
    """Grounded retrieval output ready for LLM prompt injection."""

    query: str
    grounded: bool
    citations: list[str] = field(default_factory=list)
    chunks: list[PolicySearchHit] = field(default_factory=list)
    injected_prompt: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["chunks"] = [c.model_dump() for c in self.chunks]
        return payload


class PolicyRetriever:
    """Retrieves top-k policy chunks and injects mandatory [Doc_ID, Page] citations."""

    def __init__(
        self,
        persist_dir: Path = DEFAULT_VECTORSTORE,
        embedder: Embedder | None = None,
        collection: Any | None = None,
        min_score: float = 0.15,
    ) -> None:
        self.persist_dir = Path(persist_dir)
        self.embedder = embedder
        self.collection = collection
        self.min_score = min_score

    def retrieve_and_inject(
        self,
        query: str,
        top_k: int = 4,
        category: str | None = None,
    ) -> GroundedRetrievalPayload:
        result = search_policy_docs(
            query=query,
            top_k=top_k,
            category=category,
            persist_dir=self.persist_dir,
            embedder=self.embedder,
            collection=self.collection,
        )
        filtered = [h for h in result.hits if h.score >= self.min_score]
        if not filtered:
            return GroundedRetrievalPayload(
                query=query,
                grounded=False,
                citations=[],
                chunks=[],
                injected_prompt=(
                    "SYSTEM GROUNDING NOTICE: No verified Makerere University policy "
                    "document matched the student query above the minimum confidence "
                    "threshold. Refuse to guess and advise the student to contact the "
                    "Academic Registrar or College office."
                ),
            )

        citations: list[str] = []
        blocks: list[str] = []
        for idx, hit in enumerate(filtered, start=1):
            if hit.citation not in citations:
                citations.append(hit.citation)
            blocks.append(
                f"Excerpt {idx} {hit.citation} — {hit.title} (score={hit.score}):\n{hit.text}"
            )

        evidence_block = "\n\n".join(blocks)
        injected_prompt = (
            "You are the Makerere University Student Support & Onboarding Triage Agent.\n"
            "Answer the student query strictly using ONLY the verified policy excerpts below.\n"
            "Every factual statement in your response MUST append its exact source tag "
            "(e.g., [mak-policy-XXXX, Page N]). If the excerpts do not answer the query, "
            "state clearly that the policy corpus does not cover it.\n\n"
            f"VERIFIED POLICY CONTEXT:\n{evidence_block}\n\n"
            f"STUDENT QUERY: {query}\n"
            f"REQUIRED CITATION TAGS TO USE: {', '.join(citations)}"
        )

        return GroundedRetrievalPayload(
            query=query,
            grounded=True,
            citations=citations,
            chunks=filtered,
            injected_prompt=injected_prompt,
        )
