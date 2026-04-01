# src/adapters/outbound/llm_gemini_client.py

# Google Gemini Models (code name) | Strength / Best for                          | Cost tier (qualitative) | Notes
# ---------------------------------------------------------------------------------------------------------------
# gemini-2.0-pro                   | Highest reasoning quality, deep analysis     | High                    | Best for complex logic, multi-step reasoning, and high-fidelity content.
# gemini-2.0-flash                 | Fast, lightweight, strong creative output    | Low–Moderate            | Best cost/quality trade-off for short creative outputs like tweets.
# gemini-2.0-flash-lite            | Ultra-fast, very cheap                       | Very Low                | Good for bulk generation, simple templates, or low-cost A/B testing.
# gemini-2.0-flash-thinking-exp    | "Thinking" mode (frontend)                   | High                    | Experimental chain-of-thought style model; excels at creativity, nuance,
#                                                                                 |                         | and generating engaging, high-impact tweets.
# gemini-1.5-pro                   | Large context window, strong reasoning       | High                    | Use when you need long transcripts or multi-document context.
# gemini-1.5-flash                 | Large context window, fast                   | Moderate                | Good balance for long inputs + fast generation.
# ---------------------------------------------------------------------------------------------------------------
# Practical guidance:
# - For highest-quality, most engaging tweet generation, prefer gemini-2.0-flash-thinking-exp.
# - For a strong cost/quality trade-off on short creative outputs, start with gemini-2.0-flash.
# - Use gemini-1.5-pro or gemini-1.5-flash only when transcript length requires a very large context window.
# - Use gemini-2.0-flash-lite for high-volume, low-cost runs or A/B testing.
# - Gemini models tend to be more verbose by default; tune temperature (0.6–1.2) and prompt constraints for tighter outputs.
# - "Thinking" mode (gemini-2.0-flash-thinking-exp) is experimental but excellent for creativity, nuance, and engagement.


import json
import asyncio
import inspect
import logging

import google.genai as genai
from google.genai.errors import ClientError, ServerError, APIError

from domain.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


class LLMGeminiClient(LLMPort):
    """
    Implementation of LLMPort using the new Google Gemini API (google.genai),
    with controlled error handling for transient and client/server errors.
    """

    def __init__(self, api_key: str | None = None):
        if not api_key:
            raise RuntimeError("API key (Gemini) is required")

        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

        logger.info(
            "Finished OK",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

    async def generate_tweets(
        self,
        prompt_user_message: str,
        prompt_system_message: str,
        model: str
    ) -> dict:
        """
        Call Gemini and return the same format as LLMOpenAIClient:
        - A dict parsed from JSON (e.g. {"tweets":[...], ...})
        - Raises RuntimeError if it cannot obtain parseable JSON
        """
        if not prompt_system_message or not str(prompt_system_message).strip():
            raise ValueError("prompt_system_message must not be empty")

        if not prompt_user_message or not str(prompt_user_message).strip():
            raise ValueError("prompt_user_message must not be empty")

        # Run the blocking call in a thread to avoid blocking the event loop
        return await asyncio.to_thread(
            self._call_and_process,
            prompt_user_message,
            prompt_system_message,
            model,
        )

    def _truncate(self, s: str, n: int = 1000) -> str:
        try:
            if s is None:
                return ""
            s = str(s)
            return s if len(s) <= n else s[:n] + "...(truncated)"
        except Exception:
            return "<unprintable>"

    def _call_and_process(
        self,
        prompt_user_message: str,
        prompt_system_message: str,
        model: str
    ) -> dict:
        """
        Call Gemini and return a dict parsed from JSON.
        Parsing behavior: try json.loads(raw); if that fails, extract the first {...} and try again.
        If no valid JSON is found, raise RuntimeError (same behavior as the OpenAI client).
        """
        full_prompt = (
            f"SYSTEM INSTRUCTIONS:\n{prompt_system_message}\n\n"
            f"USER REQUEST:\n{prompt_user_message}"
        )

        logger.info("Calling Gemini model=%s", model, extra={"method": inspect.currentframe().f_code.co_name})
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=full_prompt,
                config={
                    "temperature": 1.5,
                    "top_p": 0.98,
                    "top_k": 40,
                },
            )
        except ServerError as e:
            http_code = getattr(e, "code", None)
            logger.error("Gemini server error (5xx) code=%s error=%s", http_code, str(e), extra={"method": inspect.currentframe().f_code.co_name})
            if http_code == 503:
                raise RuntimeError("Gemini temporarily unavailable (503)") from e
            raise RuntimeError(f"Gemini server error ({http_code})") from e
        except ClientError as e:
            http_code = getattr(e, "code", None)
            logger.error("Gemini client error (4xx) code=%s error=%s", http_code, str(e), extra={"method": inspect.currentframe().f_code.co_name})
            raise RuntimeError(f"Gemini client error ({http_code})") from e
        except APIError as e:
            logger.error("Gemini API error: %s", str(e), extra={"method": inspect.currentframe().f_code.co_name})
            raise RuntimeError("Gemini API error") from e
        except Exception as e:
            logger.exception("Unexpected Gemini error: %s", str(e), extra={"method": inspect.currentframe().f_code.co_name})
            raise RuntimeError("Unexpected Gemini error") from e

        # Safely extract raw text from the response
        raw_output = None
        try:
            if hasattr(response, "text"):
                raw_output = response.text
            elif hasattr(response, "content"):
                raw_output = response.content.decode() if isinstance(response.content, (bytes, bytearray)) else str(response.content)
            else:
                raw_output = str(response)
        except Exception as e:
            logger.warning("Failed to extract raw text from Gemini response: %s", str(e), extra={"method": inspect.currentframe().f_code.co_name})
            raw_output = str(response)

        raw_output = raw_output.strip() if isinstance(raw_output, str) else str(raw_output)
        logger.debug("Gemini raw response (truncated): %s", self._truncate(raw_output), extra={"method": inspect.currentframe().f_code.co_name})

        # Try direct JSON parsing first
        try:
            json_response = json.loads(raw_output)
            return json_response
        except Exception:
            # If direct parsing fails, try to extract the first JSON object { ... }
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw_output[start:end + 1]
                try:
                    json_response = json.loads(candidate)
                    return json_response
                except Exception:
                    logger.error("JSON parsing failed after extraction attempt. Raw output (truncated): %s", self._truncate(raw_output), extra={"method": inspect.currentframe().f_code.co_name})
                    raise RuntimeError("Gemini returned non-parseable JSON even after extraction attempt.")
            else:
                logger.error("JSON parsing failed. Raw output has no JSON object. Raw output (truncated): %s", self._truncate(raw_output), extra={"method": inspect.currentframe().f_code.co_name})
                raise RuntimeError("Gemini returned no JSON object in the response.")


