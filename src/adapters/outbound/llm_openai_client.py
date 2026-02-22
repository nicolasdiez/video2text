# src/adapters/outbound/openai_client.py

# Models available (code name) | Strength / Best for                 | Cost tier (qualitative) | Notes
# -----------------------------------------------------------------------------------------------
# gpt-4                       | Highest-quality, creative writing   | Very High               | Top-tier for nuanced, high-impact copy and style fidelity; use for best tweet quality.
# gpt-4o                      | Highest-quality, large-context      | High                    | Use for very nuanced, long-context generations; premium per-token pricing.
# gpt-4o-mini                 | Strong creative quality, fast       | Moderate                | Best cost/quality trade-off for short creative outputs like tweets.
# gpt-4o-realtime             | Low-latency interactive generation  | High                    | Use when you need realtime responses (streaming/low latency).
# gpt-4o-32k                  | Large context window (32k tokens)   | High                    | Use when you must feed long transcripts; expensive but preserves context.
# gpt-3.5-turbo               | Cost-efficient, reliable            | Low                     | Good for bulk generation and templates; tune prompts for quality.
# -----------------------------------------------------------------------------------------------
# Practical guidance:
# - For highest-quality tweet generation prefer gpt-4 or gpt-4o (best creative fidelity).
# - For a strong cost/quality trade-off on short creative outputs start with gpt-4o-mini.
# - Use gpt-4o-32k only when transcript length or fidelity requires a very large context window.
# - Use gpt-3.5-turbo for high-volume, low-cost runs or A/B testing.
# - Costs scale with input + output tokens; output tokens dominate for short outputs.
# - Tune temperature (0.6-0.9) and penalties for variety; prompt engineering and few-shot examples often beat switching to a pricier model.

import os
import re
import json
import asyncio

# logging
import inspect
import logging

from openai import OpenAI
from domain.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


class LLMOpenAIClient(LLMPort):
    """
    Implementation of LLMPort using the official openai library.
    """

    def __init__(self, api_key: str | None = None):
        
        # Load API key
        if not api_key:
            raise RuntimeError("API key (OpenAI) is required")
        
        self.api_key = api_key
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

    async def generate_tweets(self, prompt_user_message: str, prompt_system_message: str, model: str = "gpt-3.5-turbo") -> dict:
        # Validate API key
        if not self.api_key:
            logger.error("Missing API key", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

        # Validate inputs
        if not prompt_system_message or not str(prompt_system_message).strip():
            logger.error("Empty prompt_system_message provided; aborting OpenAI call", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise ValueError("prompt_system_message must not be empty")

        if not prompt_user_message or not str(prompt_user_message).strip():
            logger.error("Empty prompt_user_message provided; aborting OpenAI call", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise ValueError("prompt_user_message must not be empty")

        # Run OpenAI call in a separate thread
        json_response = await asyncio.to_thread(self._call_and_process, prompt_user_message, prompt_system_message, model)

        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        return json_response


    def _call_and_process(self, prompt_user_message: str, prompt_system_message: str, model: str) -> dict:
        # Initialize OpenAI client
        client = OpenAI(api_key=self.api_key)

        # Build messages
        system_message = {"role": "system", "content": prompt_system_message}
        user_message = {"role": "user", "content": prompt_user_message}

        # Call OpenAI Chat Completions API
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[system_message, user_message],
                temperature=1.3,
                presence_penalty=0.5,
                frequency_penalty=0.4
            )
        except Exception as e:
            logger.exception("OpenAI API call failed", extra={"method": inspect.currentframe().f_code.co_name, "error": str(e)})
            raise RuntimeError(f"OpenAI API call failed: {e}") from e

        # Extract raw content from the first choice
        raw_output = response.choices[0].message.content

        # Best-effort cleanup: strip whitespace
        raw_output = raw_output.strip()

        # Try to parse JSON directly
        try:
            json_response = json.loads(raw_output)
            return json_response
        except Exception:
            # If direct parsing fails, try to extract the first JSON object from the text
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw_output[start:end + 1]
                try:
                    json_response = json.loads(candidate)
                    return json_response
                except Exception:
                    logger.error("JSON parsing failed after extraction attempt. Raw output: %s", raw_output)
                    raise RuntimeError("OpenAI returned non-parseable JSON even after extraction attempt.")
            else:
                logger.error("JSON parsing failed. Raw output has no JSON object. Raw output: %s", raw_output)
                raise RuntimeError("OpenAI returned no JSON object in the response.")
