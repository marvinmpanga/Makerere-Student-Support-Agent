from typing import List, Dict
import time

class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class SessionMemoryStore:
    """
    Multi-Turn Session Memory Store
    Stores conversation history in-memory for different user sessions.
    """
    
    def __init__(self, max_history_tokens: int = 4000):
        # Maps session_id (str) to a list of Messages
        self._store: Dict[str, List[Message]] = {}
        self.max_history_tokens = max_history_tokens

    def get_session(self, session_id: str) -> List[Message]:
        """Retrieve the message history for a given session."""
        if session_id not in self._store:
            self._store[session_id] = []
        return self._store[session_id]

    def _approx_tokens(self, messages: list) -> int:
        return sum(len(m.content) // 4 for m in messages)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a new message to the session's history."""
        session = self.get_session(session_id)
        session.append(Message(role=role, content=content))
        
        # Trim oldest messages if approximate token count exceeds limit
        while self._approx_tokens(session) > self.max_history_tokens and len(session) > 1:
            session.pop(0)

    def get_formatted_history(self, session_id: str) -> List[Dict[str, str]]:
        """Return the history in the standard format expected by LLMs (list of dicts)."""
        return [msg.to_dict() for msg in self.get_session(session_id)]

    def clear_session(self, session_id: str) -> None:
        """Clear the history for a specific session."""
        if session_id in self._store:
            self._store[session_id] = []
            
    def delete_session(self, session_id: str) -> None:
         """Completely remove the session from the store."""
         if session_id in self._store:
             del self._store[session_id]

# Singleton instance to be used across the application
memory_store = SessionMemoryStore()

