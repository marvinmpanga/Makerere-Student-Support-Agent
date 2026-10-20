from fastapi.testclient import TestClient
from src.main import app
from src.core.memory import memory_store

client = TestClient(app)

def setup_function():
    # Ensure memory store is empty before each test
    memory_store._store.clear()

def test_memory_store_truncation():
    # Set a very low limit to easily hit truncation (10 tokens = ~40 chars)
    memory_store.max_history_tokens = 10
    
    memory_store.add_message("test_sess", "user", "Hello World! This is a long message.")
    memory_store.add_message("test_sess", "assistant", "Hi there!")
    
    history = memory_store.get_formatted_history("test_sess")
    # Because of truncation, the oldest message should be dropped
    assert len(history) == 1
    assert history[0]["role"] == "assistant"
    
    # Reset limit for other tests
    memory_store.max_history_tokens = 4000

def test_api_get_history():
    memory_store.add_message("sess_1", "user", "What is the policy?")
    response = client.get("/api/v1/memory/sess_1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "user"
    assert data[0]["content"] == "What is the policy?"

def test_api_clear_history():
    memory_store.add_message("sess_2", "user", "Hello")
    response = client.delete("/api/v1/memory/sess_2")
    assert response.status_code == 200
    
    history = memory_store.get_formatted_history("sess_2")
    assert len(history) == 0

def test_api_delete_session():
    memory_store.add_message("sess_3", "user", "Hello")
    assert "sess_3" in memory_store._store
    
    response = client.delete("/api/v1/memory/sess_3/delete")
    assert response.status_code == 200
    
    assert "sess_3" not in memory_store._store

