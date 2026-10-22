"""W4-02: Deterministic ``search_policy_docs`` tool over the Makerere ChromaDB index.

Queries the ``makerere_policies`` vector collection built by ``src/rag/ingest.py``,
enforces type-safe Pydantic input/output contracts, supports optional category
filtering, and returns traceable ``[Doc_ID, Page N]`` citations for every hit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.rag.ingest import (
    DEFAULT_VECTORSTORE,
    Embedder,
    get_collection,
    get_embedder,
)

ALLOWED_CATEGORIES: set[str] = {
    "financial-management-policies",
    "general-policies",
    "governance-policies",
    "human-resource-policies",
    "ict-policies",
    "information-management-policies",
    "manuals",
    "research-policies",
    "student-affairs-policies",
    "teaching-and-learning-policies",
}


class PolicySearchArgs(BaseModel):
    """Strict input contract for the ``search_policy_docs`` tool."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural-language student or administrative policy question.",
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of policy chunks to retrieve (1-10).",
    )
    category: str | None = Field(
        default=None,
        description="Optional Makerere policy category filter.",
    )

    @field_validator("category")
    @classmethod
    def _validate_category(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if value not in ALLOWED_CATEGORIES:
            allowed = ", ".join(sorted(ALLOWED_CATEGORIES))
            raise ValueError(f"Unsupported category '{value}'. Allowed: {allowed}")
        return value


class PolicySearchHit(BaseModel):
    """Single retrieved policy chunk with mandatory citation metadata."""

    chunk_id: str
    doc_id: str
    title: str
    category: str
    page_start: int
    page_end: int
    citation: str
    score: float
    source_url: str = ""
    text: str


class PolicySearchResult(BaseModel):
    """Structured output returned by ``search_policy_docs``."""

    status: str = "ok"
    query: str
    total_hits: int
    citations: list[str] = Field(default_factory=list)
    hits: list[PolicySearchHit] = Field(default_factory=list)
    formatted_context: str = ""
    error_message: str | None = None


def _format_citation(meta: dict[str, Any]) -> str:
    existing = meta.get("citation")
    if isinstance(existing, str) and existing.startswith("[") and existing.endswith("]"):
        return existing
    doc_id = meta.get("doc_id", "unknown-doc")
    p_start = int(meta.get("page_start", 1))
    p_end = int(meta.get("page_end", p_start))
    if p_start == p_end:
        return f"[{doc_id}, Page {p_start}]"
    return f"[{doc_id}, Pages {p_start}-{p_end}]"


def search_policy_docs(
    query: str,
    top_k: int = 4,
    category: str | None = None,
    *,
    persist_dir: Path = DEFAULT_VECTORSTORE,
    embedder: Embedder | None = None,
    collection: Any | None = None,
) -> PolicySearchResult:
    """Search the Makerere policy vector store and return cited chunks.

    Parameters
    ----------
    query:
        The policy search query string.
    top_k:
        Maximum chunks to return (validated within 1..10).
    category:
        Optional category filter matching ``source_register.json`` categories.
    persist_dir:
        ChromaDB persistence directory (defaults to ``src/rag/vectorstore``).
    embedder:
        Optional ``Embedder`` instance (defaults to ``LocalEmbedder`` so queries
        run offline without consuming Gemini API quota).
    collection:
        Optional pre-initialized Chroma collection (used in unit tests).
    """
    args = PolicySearchArgs(query=query, top_k=top_k, category=category)
    active_embedder = embedder or get_embedder("local")
    active_collection = collection if collection is not None else get_collection(persist_dir)

    total_indexed = active_collection.count()
    if total_indexed == 0:
        return PolicySearchResult(
            status="empty_index",
            query=args.query,
            total_hits=0,
            formatted_context="No policy documents are currently indexed in ChromaDB.",
        )

    where_filter: dict[str, Any] | None = {"category": args.category} if args.category else None
    n_results = min(args.top_k, total_indexed)
    query_vec = active_embedder.embed_query(args.query)

    raw = active_collection.query(
        query_embeddings=[query_vec],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    ids = (raw.get("ids") or [[]])[0]
    docs = (raw.get("documents") or [[]])[0]
    metas = (raw.get("metadatas") or [[]])[0]
    distances = (raw.get("distances") or [[]])[0]

    hits: list[PolicySearchHit] = []
    citations: list[str] = []
    context_blocks: list[str] = []

    for idx, chunk_id in enumerate(ids):
        meta = metas[idx] if idx < len(metas) and metas[idx] else {}
        text = docs[idx] if idx < len(docs) and docs[idx] else ""
        dist = float(distances[idx]) if idx < len(distances) and distances[idx] is not None else 0.0
        # Chroma cosine distance is in [0, 2]; convert to similarity in [0, 1].
        similarity = round(max(0.0, 1.0 - dist), 4)
        citation = _format_citation(meta)

        hit = PolicySearchHit(
            chunk_id=str(chunk_id),
            doc_id=str(meta.get("doc_id", "unknown-doc")),
            title=str(meta.get("title", "")),
            category=str(meta.get("category", "")),
            page_start=int(meta.get("page_start", 1)),
            page_end=int(meta.get("page_end", 1)),
            citation=citation,
            score=similarity,
            source_url=str(meta.get("source_url", "")),
            text=text,
        )
        hits.append(hit)
        if citation not in citations:
            citations.append(citation)
        context_blocks.append(f"{citation} ({hit.title}): {hit.text}")

    return PolicySearchResult(
        status="ok",
        query=args.query,
        total_hits=len(hits),
        citations=citations,
        hits=hits,
        formatted_context="\n\n".join(context_blocks),
    )
