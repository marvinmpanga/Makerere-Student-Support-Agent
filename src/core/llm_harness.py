import os
import time
import json
import logging
import threading
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import types

from src.schemas.llm import LLMExecuteRequest, LLMExecuteResponse

logger = logging.getLogger(__name__)

# Load .env file so os.environ.get() can read GEMINI_API_KEY and GEMINI_MODEL
load_dotenv()

# Trace file destination
TRACE_FILE_PATH = Path("evidence/traces/llm_execution.jsonl")
_trace_lock = threading.Lock()

def get_gemini_client() -> genai.Client:
    """Initialize Gemini client with explicit timeout."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    # Configure explicitly with HTTP options for timeout (unit: milliseconds)
    http_options = types.HttpOptions(timeout=30_000)  # 30 seconds
    return genai.Client(api_key=api_key, http_options=http_options)

def execute_llm_query(request: LLMExecuteRequest) -> LLMExecuteResponse:
    """
    Executes a prompt against the LLM, tracks latency and tokens, 
    and logs the exact execution trace.
    """
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    try:
        client = get_gemini_client()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=500, detail="LLM Provider not configured")

    start_time = time.perf_counter()
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=request.query
        )
    except Exception as e:
        logger.error(f"LLM API failure: {str(e)}")
        # In a real system, we might log failed traces too, but for baseline we'll just raise
        raise HTTPException(status_code=502, detail="LLM Provider API Error")

    latency_ms = (time.perf_counter() - start_time) * 1000
    
    # Extract token usage from the Gemini response metadata
    # Use None (not 0) when metadata is unavailable to avoid misleading counts
    prompt_tokens = None
    completion_tokens = None
    total_tokens = None
    if response.usage_metadata:
        prompt_tokens = response.usage_metadata.prompt_token_count
        completion_tokens = response.usage_metadata.candidates_token_count
        if prompt_tokens is not None and completion_tokens is not None:
            total_tokens = prompt_tokens + completion_tokens
        
    raw_output = response.text or ""

    llm_response = LLMExecuteResponse(
        raw_output=raw_output,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens
    )

    # Append to trace file
    _log_trace(request, llm_response, model_name)

    return llm_response

def _log_trace(request: LLMExecuteRequest, response: LLMExecuteResponse, model: str):
    """Appends a trace record to the JSONL trace file."""
    # Ensure directory exists
    TRACE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    trace_record = {
        "timestamp": time.time(),
        "request_id": response.request_id,
        "model": model,
        "session_id": request.session_id,
        "query": request.query,
        "raw_output": response.raw_output,
        "latency_ms": response.latency_ms,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "total_tokens": response.total_tokens
    }
    
    try:
        with _trace_lock:
            with open(TRACE_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace_record) + "\n")
    except Exception as e:
        logger.error(f"Failed to write trace to {TRACE_FILE_PATH}: {e}")
        # We generally shouldn't crash the user request if tracing fails, but log it loudly
