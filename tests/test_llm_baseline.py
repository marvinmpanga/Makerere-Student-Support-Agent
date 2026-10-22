import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.core.llm import GeminiBaselineClient


def test_client_initialization_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiBaselineClient()


def test_generate_response_mocked_success(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    payload = {"category": "Fees", "confidence_score": 0.9}
    response = SimpleNamespace(
        text=json.dumps(payload),
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=8),
    )

    with patch("src.core.llm.genai.configure") as configure, patch(
        "src.core.llm.genai.GenerativeModel"
    ) as model_class:
        model_class.return_value.generate_content.return_value = response
        client = GeminiBaselineClient()
        result = client.generate_response("You are helpful.", "How do I pay?", force_json=True)

    configure.assert_called_once_with(api_key="test-key")
    assert result["status"] == "success"
    assert result["latency_seconds"] >= 0
    assert result["structured_output"] == payload
    assert result["raw_usage"] == {"prompt_token_count": 12, "candidates_token_count": 8}


def test_generate_response_json_decode_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    response = SimpleNamespace(text="not-json", usage_metadata=None)

    with patch("src.core.llm.genai.configure"), patch(
        "src.core.llm.genai.GenerativeModel"
    ) as model_class:
        model_class.return_value.generate_content.return_value = response
        client = GeminiBaselineClient()
        result = client.generate_response("You are helpful.", "Question", force_json=True)

    assert result["status"] == "error"
    assert result["structured_output"] is None
    assert result["response_text"] == "not-json"
    assert "Invalid JSON model response" in result["error_message"]