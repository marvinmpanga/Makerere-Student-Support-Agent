from fastapi import APIRouter

from src.core.rag_pipeline import KnowledgeIndex, RAGAnswerRequest, RAGAnswerResponse

router = APIRouter(tags=["rag"])

INDEX = KnowledgeIndex()
INDEX.ingest_directory("knowledge/raw/mak-policies")


@router.post("/answer", response_model=RAGAnswerResponse)
def answer_question(request: RAGAnswerRequest):
    """Answer a student question using the approved knowledge index."""
    return INDEX.answer(request)


@router.get("/health")
def rag_health() -> dict[str, str]:
    return {"status": "ok", "chunk_count": str(len(INDEX.chunks)), "document_count": str(len(INDEX.documents))}
