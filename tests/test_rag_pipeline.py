from pathlib import Path

from src.core.rag_pipeline import KnowledgeIndex, RAGAnswerRequest, RAGAnswerResponse, build_grounded_prompt


def test_rag_indexing_creates_chunks_and_metadata(tmp_path):
    source_dir = tmp_path / "policies"
    source_dir.mkdir()
    policy_file = source_dir / "fees-policy.txt"
    policy_file.write_text(
        "Makerere University tuition and registration policy. "
        "Students must pay tuition before examination results are released. "
        "Late registration is allowed only with department approval.",
        encoding="utf-8",
    )

    index = KnowledgeIndex()
    result = index.ingest_directory(source_dir)

    assert result["chunk_count"] > 0
    assert result["document_count"] == 1
    assert index.chunks
    assert all("source_path" in chunk.metadata for chunk in index.chunks)
    assert index.chunks[0].content


def test_grounded_prompt_includes_evidence_and_question():
    prompt = build_grounded_prompt(
        question="When are exam results released?",
        context_chunks=[
            {"content": "Students must pay tuition before examination results are released.", "source": "fees-policy.txt"},
            {"content": "Late registration requires department approval.", "source": "registration-policy.txt"},
        ],
    )

    assert "When are exam results released?" in prompt
    assert "Students must pay tuition before examination results are released." in prompt
    assert "fees-policy.txt" in prompt


def test_rag_answer_retrieval_returns_supporting_sources_for_matching_question():
    source_dir = Path("knowledge/raw/mak-policies")
    index = KnowledgeIndex()
    index.ingest_directory(source_dir)

    request = RAGAnswerRequest(
        question="What is the policy for late registration?",
        top_k=3,
    )
    response = index.answer(request)

    assert response.grounded is True
    assert response.supporting_sources
    assert response.answer


def test_rag_answer_rejects_unrelated_question_without_support():
    index = KnowledgeIndex()
    index.ingest_texts(
        [
            {
                "document_id": "doc-1",
                "title": "Tuition and registration policy",
                "source_path": "fees-policy.txt",
                "content": "Students must pay tuition before examination results are released.",
            }
        ]
    )

    request = RAGAnswerRequest(question="What is the capital city of France?", top_k=3)
    response = index.answer(request)

    assert response.grounded is False
    assert response.answer.startswith("I cannot answer") or response.answer.lower().startswith("i cannot")
