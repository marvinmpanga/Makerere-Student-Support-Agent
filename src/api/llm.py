from fastapi import APIRouter
from src.schemas.llm import LLMExecuteRequest, LLMExecuteResponse
from src.core.llm_harness import execute_llm_query

router = APIRouter(tags=["llm"])

@router.post("/execute", response_model=LLMExecuteResponse)
def execute_query(request: LLMExecuteRequest):
    """
    Executes a structured query against the baseline LLM harness.
    Records tracing observability metrics (latency, tokens, raw output).
    """
    return execute_llm_query(request)
