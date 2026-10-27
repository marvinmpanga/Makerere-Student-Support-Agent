"""Policy document retrieval API endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from src.schemas.api import PolicyHitItem, PolicySearchRequest, PolicySearchResponse
from src.tools.policy_search import search_policy_docs

router = APIRouter(tags=["Policies & RAG"])


@router.post("/policy/search", response_model=PolicySearchResponse)
def handle_policy_search(payload: PolicySearchRequest) -> PolicySearchResponse:
    """Execute grounded semantic search over Makerere University policy corpus."""
    result = search_policy_docs(
        query=payload.query,
        top_k=payload.top_k,
        category=payload.category,
    )

    hits = [
        PolicyHitItem(
            doc_id=h.doc_id,
            citation=h.citation,
            title=h.title,
            category=h.category,
            score=round(h.score, 4),
            text_snippet=h.text,
        )
        for h in result.hits
    ]

    return PolicySearchResponse(
        status=result.status,
        total_hits=result.total_hits,
        citations=result.citations,
        hits=hits,
        formatted_context=result.formatted_context,
    )
