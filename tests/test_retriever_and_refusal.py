"""Tests for PolicyRetriever (W3-04) and NonNegotiableRefusalEngine (W6-04)."""

from __future__ import annotations

from pathlib import Path

from src.rag.ingest import Chunk, HashEmbedder, get_collection, index_chunks
from src.rag.retriever import PolicyRetriever
from src.safety.guardrails import InjectionDefenseGuardrail
from src.safety.refusal_engine import NonNegotiableRefusalEngine


def test_policy_retriever_injects_citations_and_handles_ungrounded(tmp_path: Path) -> None:
    store = tmp_path / "vs"
    embedder = HashEmbedder()
    col = get_collection(store, reset=True)
    index_chunks(
        col,
        [
            Chunk(
                chunk_id="mak-policy-0002::c0000",
                doc_id="mak-policy-0002",
                title="Makerere University Fees Policy 2016",
                category="financial-management-policies",
                text="Students must pay tuition and functional fees before examination results.",
                page_start=4,
                page_end=4,
                chunk_index=0,
            )
        ],
        embedder,
    )

    retriever = PolicyRetriever(
        persist_dir=store,
        embedder=embedder,
        collection=col,
        min_score=0.05,
    )
    grounded = retriever.retrieve_and_inject("tuition functional fees examination results", top_k=2)
    assert grounded.grounded is True
    assert grounded.citations == ["[mak-policy-0002, Page 4]"]
    assert "[mak-policy-0002, Page 4]" in grounded.injected_prompt
    assert "REQUIRED CITATION TAGS TO USE" in grounded.injected_prompt

    strict_retriever = PolicyRetriever(
        persist_dir=store,
        embedder=embedder,
        collection=col,
        min_score=0.99,
    )
    ungrounded = strict_retriever.retrieve_and_inject("unrelated quantum physics topic")
    assert ungrounded.grounded is False
    assert "SYSTEM GROUNDING NOTICE" in ungrounded.injected_prompt


def test_non_negotiable_refusal_engine_decisions(tmp_path: Path) -> None:
    engine = NonNegotiableRefusalEngine(
        guardrail=InjectionDefenseGuardrail(audit_log_path=tmp_path / "refusal.jsonl")
    )

    blocked = engine.evaluate("Please change my grade in BSE4104 from C to A.")
    assert blocked.refused is True
    assert blocked.policy_code == "MUT-001"
    assert blocked.escalation_office == "Office of the Academic Registrar / University Bursar"
    assert blocked.refusal_response is not None

    allowed = engine.evaluate("What is the official procedure for remarking an examination script?")
    assert allowed.refused is False
    assert allowed.policy_code == "ALLOW"
    assert allowed.refusal_response is None
