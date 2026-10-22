import uuid
from typing import Optional
from pydantic import BaseModel, Field


class LLMExecuteRequest(BaseModel):
    """Structured request for LLM execution."""
    
    query: str = Field(..., description="The main prompt or user query to send to the LLM.")
    session_id: Optional[str] = Field(
        default=None, 
        description="Optional correlation ID for tracing multi-turn conversations (logging passthrough)."
    )


class LLMExecuteResponse(BaseModel):
    """Structured response containing raw output and execution metrics."""
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this execution request.")
    raw_output: str = Field(..., description="The exact unmodified text returned by the LLM.")
    latency_ms: float = Field(..., description="Time taken for the execution in milliseconds.")
    prompt_tokens: Optional[int] = Field(default=None, description="Number of tokens in the prompt, or null if unavailable.")
    completion_tokens: Optional[int] = Field(default=None, description="Number of tokens in the response, or null if unavailable.")
    total_tokens: Optional[int] = Field(default=None, description="Total tokens (prompt + completion), or null if unavailable.")
