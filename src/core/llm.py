"""Direct Gemini baseline client for structured Makerere support responses."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core import exceptions as google_exceptions

load_dotenv()


class GeminiBaselineClient:
    """Small, observable adapter around the Gemini content-generation API."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set to initialize the Gemini client")

        self.model_name = os.getenv("BASE_MODEL_NAME", "gemini-1.5-flash")
        self.temperature = float(os.getenv("MODEL_TEMPERATURE", "0.2"))
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))
        genai.configure(api_key=api_key)

    def generate_response(
        self,
        system_instruction: str,
        user_query: str,
        context_documents: str | None = None,
        force_json: bool = False,
    ) -> dict[str, Any]:
        """Generate a response and return provider usage and failure telemetry."""
        started_at = time.perf_counter()
        result: dict[str, Any] = {
            "status": "error",
            "model": self.model_name,
            "latency_seconds": 0.0,
            "response_text": "",
            "structured_output": None,
            "raw_usage": {"prompt_token_count": None, "candidates_token_count": None},
            "error_message": None,
        }

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
            )
            prompt = user_query
            if context_documents:
                prompt = f"Approved context documents:\n{context_documents}\n\nQuery:\n{user_query}"
            generation_config: dict[str, Any] = {
                "temperature": self.temperature,
                "top_p": 0.95,
                "max_output_tokens": self.max_output_tokens,
            }
            if force_json:
                generation_config["response_mime_type"] = "application/json"

            response = model.generate_content(prompt, generation_config=generation_config)
            result["response_text"] = response.text
            usage = getattr(response, "usage_metadata", None)
            if usage:
                result["raw_usage"] = {
                    "prompt_token_count": getattr(usage, "prompt_token_count", None),
                    "candidates_token_count": getattr(
                        usage, "candidates_token_count", None
                    ),
                }
            result["status"] = "success"
            if force_json:
                try:
                    result["structured_output"] = json.loads(result["response_text"])
                except (TypeError, json.JSONDecodeError) as error:
                    result["status"] = "error"
                    result["error_message"] = f"Invalid JSON model response: {error}"
        except (
            google_exceptions.GoogleAPIError,
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as error:
            result["error_message"] = str(error)
        finally:
            result["latency_seconds"] = time.perf_counter() - started_at

        return result