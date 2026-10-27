from fastapi import APIRouter
from src.core.memory import memory_store
from typing import List, Dict

router = APIRouter(tags=["memory"])

@router.get("/{session_id}", response_model=List[Dict[str, str]])
def get_history(session_id: str):
    """Retrieve formatted conversation history for a session."""
    return memory_store.get_formatted_history(session_id)

@router.delete("/{session_id}")
def clear_history(session_id: str):
    """Clear all messages for a session (does not delete the session key)."""
    memory_store.clear_session(session_id)
    return {"status": "cleared"}

@router.delete("/{session_id}/delete")
def delete_session(session_id: str):
    """Permanently remove a session from the memory store."""
    memory_store.delete_session(session_id)
    return {"status": "deleted"}

