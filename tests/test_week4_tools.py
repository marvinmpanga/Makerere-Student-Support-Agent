"""Tests for W4-02 (search_policy_docs) and W4-05 (ToolDispatcher & telemetry loop)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, Field, ValidationError

from src.core.dispatcher import ToolDispatcher, ToolSpecification
from src.rag.ingest import Chunk, HashEmbedder, get_collection, index_chunks
from src.tools.policy_search import PolicySearchArgs, search_policy_docs


def _seed_test_collection(tmp_path: Path):
    store = tmp_path / "vs"
    embedder = HashEmbedder()
    col = get_collection(store, reset=True)
    chunks = [
        Chunk(
            chunk_id="mak-policy-0002::c0000",
            doc_id="mak-policy-0002",
            title="Makerere University Fees Policy 2016",
            category="financial-management-policies",
            text="Students must pay tuition and functional fees before examination results.",
            page_start=4,
            page_end=4,
            chunk_index=0,
            source_url="https://policies.mak.ac.ug/fees",
        ),
        Chunk(
            chunk_id="mak-policy-0055::c0000",
            doc_id="mak-policy-0055",
            title="Makerere Students Accommodation Policy",
            category="student-affairs-policies",
            text="Hostel and hall accommodation allocation prioritizes first-year students.",
            page_start=2,
            page_end=3,
            chunk_index=0,
            source_url="https://policies.mak.ac.ug/accommodation",
        ),
    ]
    index_chunks(col, chunks, embedder)
    return store, embedder, col


def test_search_policy_docs_returns_cited_hits(tmp_path: Path) -> None:
    store, embedder, col = _seed_test_collection(tmp_path)
    result = search_policy_docs(
        "tuition functional fees examination results",
        top_k=2,
        persist_dir=store,
        embedder=embedder,
        collection=col,
    )
    assert result.status == "ok"
    assert result.total_hits == 2
    assert result.hits[0].doc_id == "mak-policy-0002"
    assert result.hits[0].citation == "[mak-policy-0002, Page 4]"
    assert "[mak-policy-0002, Page 4]" in result.formatted_context


def test_search_policy_docs_category_filter(tmp_path: Path) -> None:
    store, embedder, col = _seed_test_collection(tmp_path)
    result = search_policy_docs(
        "accommodation hall allocation",
        top_k=5,
        category="student-affairs-policies",
        persist_dir=store,
        embedder=embedder,
        collection=col,
    )
    assert result.total_hits == 1
    assert result.hits[0].doc_id == "mak-policy-0055"
    assert result.hits[0].citation == "[mak-policy-0055, Pages 2-3]"


def test_search_policy_docs_rejects_invalid_args() -> None:
    with pytest.raises(ValidationError):
        PolicySearchArgs(query="ab", top_k=4)  # too short
    with pytest.raises(ValidationError):
        PolicySearchArgs(query="valid query", top_k=99)  # exceeds max 10
    with pytest.raises(ValidationError):
        PolicySearchArgs(query="valid query", category="not-a-valid-category")


def test_dispatcher_executes_registered_tool_and_logs_telemetry(tmp_path: Path) -> None:
    store, embedder, col = _seed_test_collection(tmp_path)
    log_path = tmp_path / "dispatch.jsonl"
    dispatcher = ToolDispatcher(telemetry_log_path=log_path, register_defaults=False)
    dispatcher.register(
        ToolSpecification(
            name="search_policy_docs",
            description="Search policies",
            args_schema=PolicySearchArgs,
            handler=lambda **kw: search_policy_docs(
                **kw, persist_dir=store, embedder=embedder, collection=col
            ),
        )
    )

    record = dispatcher.dispatch(
        "search_policy_docs",
        {"query": "tuition fees policy", "top_k": 1},
    )
    assert record.status == "success"
    assert record.output is not None
    assert record.output["citations"] == ["[mak-policy-0002, Page 4]"]
    assert log_path.is_file()
    logged = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert logged["tool_name"] == "search_policy_docs"
    assert logged["status"] == "success"


def test_dispatcher_handles_unknown_tool_and_malformed_args_gracefully(tmp_path: Path) -> None:
    dispatcher = ToolDispatcher(telemetry_log_path=tmp_path / "dispatch.jsonl")

    unknown = dispatcher.dispatch("delete_student_grades", {"student_id": "123"})
    assert unknown.status == "unknown_tool"
    assert "not registered" in (unknown.error_message or "")

    bad_schema = dispatcher.dispatch("search_policy_docs", {"query": "x", "top_k": 50})
    assert bad_schema.status == "validation_error"

    bad_json = dispatcher.dispatch("search_policy_docs", "{not-valid-json")
    assert bad_json.status == "validation_error"


def test_dispatcher_run_loop_feeds_observation_back_to_model(tmp_path: Path) -> None:
    class EchoArgs(BaseModel):
        student_number: str = Field(..., min_length=3)

    dispatcher = ToolDispatcher(telemetry_log_path=tmp_path / "loop.jsonl", register_defaults=False)
    dispatcher.register(
        ToolSpecification(
            name="get_student_status",
            description="Read-only student status lookup",
            args_schema=EchoArgs,
            handler=lambda student_number: {
                "student_number": student_number,
                "registration_status": "REGISTERED",
            },
        )
    )

    def fake_llm(messages: list[dict[str, Any]]) -> dict[str, Any]:
        if len(messages) == 1:
            return {
                "tool_call": {
                    "name": "get_student_status",
                    "arguments": {"student_number": "2400712345"},
                }
            }
        tool_obs = messages[-1]["observation"]
        return {
            "final_answer": f"Status is {tool_obs['registration_status']}",
            "structured_output": tool_obs,
        }

    loop_res = dispatcher.run_loop(fake_llm, "Check my registration status", max_iterations=4)
    assert loop_res.status == "completed"
    assert loop_res.iterations == 2
    assert loop_res.final_response == "Status is REGISTERED"
    assert len(loop_res.tool_traces) == 1


def test_dispatcher_run_loop_enforces_max_iterations(tmp_path: Path) -> None:
    dispatcher = ToolDispatcher(telemetry_log_path=tmp_path / "loop_max.jsonl")

    def runaway_llm(_messages: list[dict[str, Any]]) -> dict[str, Any]:
        return {"tool_call": {"name": "nonexistent_tool", "arguments": {}}}

    res = dispatcher.run_loop(runaway_llm, "Loop forever", max_iterations=3)
    assert res.status == "max_iterations_exceeded"
    assert res.iterations == 3
    assert len(res.tool_traces) == 3
