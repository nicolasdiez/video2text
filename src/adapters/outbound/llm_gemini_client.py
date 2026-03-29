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
from domain.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


class LLMGeminiClient(LLMPort):
    """
    Implementation of LLMPort using the new Google Gemini API (google.genai).
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
    ) -> list[str]:

        # Validate inputs
        if not prompt_system_message or not str(prompt_system_message).strip():
            logger.error("Empty prompt_system_message provided; aborting Gemini call")
            raise ValueError("prompt_system_message must not be empty")

        if not prompt_user_message or not str(prompt_user_message).strip():
            logger.error("Empty prompt_user_message provided; aborting Gemini call")
            raise ValueError("prompt_user_message must not be empty")

        # Run Gemini call in a separate thread (SDK is sync)
        tweets = await asyncio.to_thread(
            self._call_and_process,
            prompt_user_message,
            prompt_system_message,
            model,
        )

        logger.info(
            "Finished OK",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

        return tweets


    def _call_and_process(
        self,
        prompt_user_message: str,
        prompt_system_message: str,
        model: str
    ) -> list[str]:

        # Combine system + user into one structured prompt
        full_prompt = (
            f"SYSTEM INSTRUCTIONS:\n{prompt_system_message}\n\n"
            f"USER REQUEST:\n{prompt_user_message}"
        )

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=full_prompt,
                config={
                    "temperature": 1.3,
                    "top_p": 0.9,
                    "top_k": 40,
                },
            )
        except Exception as e:
            logger.exception(
                "Gemini API call failed",
                extra={"method": inspect.currentframe().f_code.co_name, "error": str(e)},
            )
            raise RuntimeError(f"Gemini API call failed: {e}") from e

        raw_output = response.text.strip()

        # Try direct JSON parsing
        try:
            parsed = json.loads(raw_output)
            return parsed.get("tweets", [])
        except Exception:
            pass

        # Try to extract JSON object from mixed output
        start = raw_output.find("{")
        end = raw_output.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = raw_output[start : end + 1]
            try:
                parsed = json.loads(candidate)
                return parsed.get("tweets", [])
            except Exception:
                logger.error(
                    "JSON parsing failed after extraction attempt. Raw output: %s",
                    raw_output,
                )
                raise RuntimeError("Gemini returned non-parseable JSON even after extraction attempt.")

        logger.error(
            "JSON parsing failed. Raw output has no JSON object. Raw output: %s",
            raw_output,
        )
        raise RuntimeError("Gemini returned no JSON object in the response.")
