import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from src.main import app
from src.core.llm_harness import TRACE_FILE_PATH

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_trace_file():
    """Ensure trace file is clean before each test."""
    if TRACE_FILE_PATH.exists():
        TRACE_FILE_PATH.unlink()
    yield
    if TRACE_FILE_PATH.exists():
        TRACE_FILE_PATH.unlink()

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_abc123_secret")

def test_execute_schema_validation():
    """Test that the endpoint requires a query field."""
    # Missing query
    response = client.post("/api/v1/llm/execute", json={"session_id": "123"})
    assert response.status_code == 422
    
    # Invalid type
    response = client.post("/api/v1/llm/execute", json={"query": {"not": "a string"}})
    assert response.status_code == 422

@patch("src.core.llm_harness.genai.Client")
def test_execute_success_and_trace_logging(mock_client_class):
    """Test successful execution, latency tracking, token extraction, request_id, and JSONL logging."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    
    # Mock the Gemini GenerateContentResponse
    mock_response = MagicMock()
    mock_response.text = "Hello, world!"
    
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 10
    mock_usage.candidates_token_count = 5
    mock_response.usage_metadata = mock_usage
    
    mock_instance.models.generate_content.return_value = mock_response

    payload = {"query": "Say hello", "session_id": "test-session"}
    response = client.post("/api/v1/llm/execute", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["raw_output"] == "Hello, world!"
    assert data["prompt_tokens"] == 10
    assert data["completion_tokens"] == 5
    assert data["total_tokens"] == 15
    assert "request_id" in data
    assert len(data["request_id"]) > 0
    assert "latency_ms" in data
    assert data["latency_ms"] > 0
    
    # Verify the JSONL trace log includes request_id and total_tokens
    assert TRACE_FILE_PATH.exists()
    with open(TRACE_FILE_PATH, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        trace = json.loads(lines[0])
        
        assert trace["query"] == "Say hello"
        assert trace["raw_output"] == "Hello, world!"
        assert trace["session_id"] == "test-session"
        assert trace["prompt_tokens"] == 10
        assert trace["total_tokens"] == 15
        assert "request_id" in trace

@patch("src.core.llm_harness.genai.Client")
def test_execute_missing_token_metadata(mock_client_class):
    """Test that when Gemini omits usage_metadata, token fields are null (not 0)."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    
    mock_response = MagicMock()
    mock_response.text = "Response without metadata"
    mock_response.usage_metadata = None  # Gemini omits metadata
    
    mock_instance.models.generate_content.return_value = mock_response

    payload = {"query": "Test missing metadata"}
    response = client.post("/api/v1/llm/execute", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["raw_output"] == "Response without metadata"
    assert data["prompt_tokens"] is None
    assert data["completion_tokens"] is None
    assert data["total_tokens"] is None

@patch("src.core.llm_harness.genai.Client")
def test_execute_provider_error(mock_client_class):
    """Test that provider errors are caught and return a 502 Bad Gateway."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    
    # Simulate a provider API exception (e.g. timeout or auth error)
    mock_instance.models.generate_content.side_effect = Exception("API Timeout")
    
    payload = {"query": "Will timeout"}
    response = client.post("/api/v1/llm/execute", json=payload)
    
    assert response.status_code == 502
    assert response.json()["detail"] == "LLM Provider API Error"

@patch("src.core.llm_harness.genai.Client")
def test_concurrency_trace_logging(mock_client_class):
    """Test that concurrent requests each produce their own trace entry."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    
    mock_response = MagicMock()
    mock_response.text = "concurrent response"
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 3
    mock_usage.candidates_token_count = 2
    mock_response.usage_metadata = mock_usage
    mock_instance.models.generate_content.return_value = mock_response

    def send_request(i):
        return client.post("/api/v1/llm/execute", json={"query": f"concurrent query {i}"})

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(send_request, i) for i in range(5)]
        results = [f.result() for f in futures]

    # All 5 should succeed
    assert all(r.status_code == 200 for r in results)
    
    # All 5 should have unique request_ids
    request_ids = [r.json()["request_id"] for r in results]
    assert len(set(request_ids)) == 5

    # Trace file should contain exactly 5 entries
    with open(TRACE_FILE_PATH, "r") as f:
        lines = f.readlines()
        assert len(lines) == 5

@patch("src.core.llm_harness.genai.Client")
def test_trace_does_not_leak_api_key(mock_client_class):
    """Test that the API key never appears in trace logs."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    
    mock_response = MagicMock()
    mock_response.text = "safe response"
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 1
    mock_usage.candidates_token_count = 1
    mock_response.usage_metadata = mock_usage
    mock_instance.models.generate_content.return_value = mock_response

    payload = {"query": "privacy test"}
    client.post("/api/v1/llm/execute", json=payload)

    assert TRACE_FILE_PATH.exists()
    trace_content = TRACE_FILE_PATH.read_text()
    
    # The API key must NEVER appear in trace logs
    assert "test_key_abc123_secret" not in trace_content
    assert "GEMINI_API_KEY" not in trace_content
