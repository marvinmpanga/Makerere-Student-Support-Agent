from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

STOPWORDS = {
    "what", "when", "where", "which", "who", "why", "how", "is", "are", "the", "a", "an",
    "of", "for", "to", "in", "on", "and", "or", "with", "without", "from", "by", "it",
    "this", "that", "these", "those", "be", "as", "at", "if", "then", "about"
}


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    source_path: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeIndex:
    """Simple in-memory retrieval index for the Makerere RAG design."""

    def __init__(self):
        self.chunks: list[DocumentChunk] = []
        self.documents: dict[str, dict[str, Any]] = {}

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _extract_keywords(self, question: str) -> set[str]:
        tokens = re.findall(r"[A-Za-z0-9]+", question.lower())
        return {token for token in tokens if token not in STOPWORDS and len(token) > 2}

    def _seed_default_corpus(self) -> None:
        default_documents = [
            {
                "document_id": "mak-demo-001",
                "title": "Late registration and examination policy",
                "source_path": "knowledge/raw/mak-policies/late-registration-policy.txt",
                "content": "Late registration is allowed only with department approval. Students must complete registration before examination results are released. Registration procedures are governed by the Office of the Academic Registrar.",
                "metadata": {"category": "academic-registration"},
            },
            {
                "document_id": "mak-demo-002",
                "title": "Tuition and fee policy",
                "source_path": "knowledge/raw/mak-policies/tuition-policy.txt",
                "content": "Students must pay tuition before examination results are released. The university may withhold results for non-payment of approved fees and charges.",
                "metadata": {"category": "finance"},
            },
            {
                "document_id": "mak-demo-003",
                "title": "Student support and guidance",
                "source_path": "knowledge/raw/mak-policies/student-support-policy.txt",
                "content": "Students seeking guidance should contact Student Affairs or the relevant academic office. Policy questions must be answered using approved University documents.",
                "metadata": {"category": "student-support"},
            },
        ]
        self.ingest_texts(default_documents)

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
        cleaned = self._normalize_text(text)
        if not cleaned:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(cleaned):
            end = min(start + chunk_size, len(cleaned))
            chunk = cleaned[start:end]
            chunks.append(chunk)
            if end == len(cleaned):
                break
            start = max(start + chunk_size - overlap, end - overlap)
        return chunks

    def ingest_directory(self, directory: str | Path) -> dict[str, Any]:
        source_dir = Path(directory)
        if not source_dir.exists():
            raise FileNotFoundError(f"Knowledge directory not found: {source_dir}")

        documents: list[dict[str, Any]] = []
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in {".txt", ".md", ".csv", ".json"}:
                try:
                    text = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                documents.append(
                    {
                        "document_id": f"doc-{len(documents) + len(self.documents) + 1:04d}",
                        "title": file_path.stem.replace("-", " ").title(),
                        "source_path": str(file_path),
                        "content": text,
                        "metadata": {"source_type": "policy_document", "file_type": file_path.suffix.lower().lstrip(".")},
                    }
                )

        if not documents:
            self._seed_default_corpus()
            return {"document_count": len(self.documents), "chunk_count": len(self.chunks), "status": "seeded_default_corpus"}

        return self.ingest_texts(documents)

    def ingest_texts(self, documents: list[dict[str, Any]]) -> dict[str, Any]:
        chunk_count = 0
        for document in documents:
            document_id = document.get("document_id") or f"doc-{len(self.documents) + 1:04d}"
            title = document.get("title") or Path(document.get("source_path", "unknown")).stem
            source_path = document.get("source_path") or "unknown"
            content = document.get("content") or ""
            metadata = document.get("metadata") or {}
            self.documents[document_id] = {
                "document_id": document_id,
                "title": title,
                "source_path": source_path,
                "metadata": metadata,
            }

            chunks = self._chunk_text(content)
            for index, chunk in enumerate(chunks):
                chunk_id = f"{document_id}-chunk-{index + 1}"
                self.chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        source_path=source_path,
                        title=title,
                        content=chunk,
                        metadata={**metadata, "chunk_index": index, "source_path": source_path},
                    )
                )
                chunk_count += 1

        return {"document_count": len(self.documents), "chunk_count": chunk_count, "status": "indexed"}

    def retrieve(self, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.chunks:
            return []

        question_terms = self._extract_keywords(question)
        if not question_terms:
            return []

        scored: list[tuple[float, DocumentChunk]] = []
        for chunk in self.chunks:
            text = (chunk.content + " " + chunk.title).lower()
            matched_terms = [term for term in question_terms if term in text]
            if not matched_terms:
                continue
            score = len(matched_terms) / max(len(question_terms), 1)
            score += 0.1 if any(term in text for term in {"policy", "registration", "tuition", "student", "results", "approval"}) else 0
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, chunk in scored[:top_k]:
            results.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "title": chunk.title,
                    "source": chunk.source_path,
                    "content": chunk.content,
                    "score": round(score, 4),
                }
            )
        return results

    def answer(self, request: "RAGAnswerRequest") -> "RAGAnswerResponse":
        context = self.retrieve(request.question, top_k=request.top_k)
        if not context:
            return RAGAnswerResponse(
                answer="I cannot answer this question because no relevant document in the approved knowledge base matches it.",
                grounded=False,
                supporting_sources=[],
                retrieval_results=[],
            )

        question_terms = self._extract_keywords(request.question)
        supported = any(
            any(term in (item["content"] + " " + item["title"]).lower() for term in question_terms)
            for item in context
        )
        if not supported:
            return RAGAnswerResponse(
                answer="I cannot answer this question because the retrieved evidence does not support it.",
                grounded=False,
                supporting_sources=[],
                retrieval_results=context,
            )

        prompt = build_grounded_prompt(request.question, context)
        answer_text = "Based on the retrieved policy context: " + context[0]["content"]
        response = RAGAnswerResponse(
            answer=answer_text,
            grounded=True,
            supporting_sources=[item["source"] for item in context],
            retrieval_results=context,
            prompt_version="rag.prompt.v1",
            evidence_summary=prompt,
        )
        return response


class RAGAnswerRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    session_id: str | None = None


class RAGAnswerResponse(BaseModel):
    answer: str
    grounded: bool
    supporting_sources: list[str] = Field(default_factory=list)
    retrieval_results: list[dict[str, Any]] = Field(default_factory=list)
    prompt_version: str | None = None
    evidence_summary: str | None = None


def build_grounded_prompt(question: str, context_chunks: list[dict[str, Any]]) -> str:
    evidence = "\n\n".join(
        f"[Source: {chunk.get('source', 'unknown')}]: {chunk.get('content', '')}"
        for chunk in context_chunks
    )
    return (
        "You are a Makerere Student Support assistant. Answer using only the approved evidence below. "
        "If the evidence does not support the answer, say so clearly and do not guess.\n\n"
        f"Student question: {question}\n\n"
        f"Approved evidence:\n{evidence}\n\n"
        "Answer in a concise, factual manner. Cite the supporting document names if available."
    )


def _create_demo_index() -> KnowledgeIndex:
    index = KnowledgeIndex()
    index.ingest_texts(
        [
            {
                "document_id": "doc-001",
                "title": "Tuition and registration policy",
                "source_path": "knowledge/raw/mak-policies/fees-policy.txt",
                "content": "Students must pay tuition before examination results are released. Late registration is allowed only with department approval.",
                "metadata": {"category": "finance"},
            },
            {
                "document_id": "doc-002",
                "title": "Student support and appeals policy",
                "source_path": "knowledge/raw/mak-policies/support-policy.txt",
                "content": "Students may request support or guidance through the Student Affairs office. Policy questions must be answered from approved documents.",
                "metadata": {"category": "student-affairs"},
            },
        ]
    )
    return index


if __name__ == "__main__":
    index = _create_demo_index()
    request = RAGAnswerRequest(question="What happens if a student misses registration?", top_k=3)
    print(json.dumps(index.answer(request).model_dump(), indent=2, ensure_ascii=False))
