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
    ) -> list[str]:

        if not prompt_system_message or not str(prompt_system_message).strip():
            raise ValueError("prompt_system_message must not be empty")

        if not prompt_user_message or not str(prompt_user_message).strip():
            raise ValueError("prompt_user_message must not be empty")

        return await asyncio.to_thread(
            self._call_and_process,
            prompt_user_message,
            prompt_system_message,
            model,
        )

    def _call_and_process(
        self,
        prompt_user_message: str,
        prompt_system_message: str,
        model: str
    ) -> list[str]:

        full_prompt = (
            f"SYSTEM INSTRUCTIONS:\n{prompt_system_message}\n\n"
            f"USER REQUEST:\n{prompt_user_message}"
        )

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

        # 5xx errors → transient
        except ServerError as e:
            logger.error("Gemini server error (5xx)", extra={"method": inspect.currentframe().f_code.co_name, "error": str(e)})

            http_code = getattr(e, "code", None)

            if http_code == 503:
                raise RuntimeError("Gemini temporarily unavailable (503)") from e

            raise RuntimeError(f"Gemini server error ({http_code})") from e

        # 4xx errors → invalid request, model not found, etc.
        except ClientError as e:
            logger.error("Gemini client error (4xx)", extra={"method": inspect.currentframe().f_code.co_name, "error": str(e)})
            http_code = getattr(e, "code", None)
            raise RuntimeError(f"Gemini client error ({http_code})") from e

        except APIError as e:
            logger.error(
                "Gemini API error",
                extra={"method": inspect.currentframe().f_code.co_name, "error": str(e)},
            )
            raise RuntimeError("Gemini API error") from e

        except Exception as e:
            logger.exception(
                "Unexpected Gemini error",
                extra={"method": inspect.currentframe().f_code.co_name, "error": str(e)},
            )
            raise RuntimeError("Unexpected Gemini error") from e

        # Parse output
        raw_output = response.text.strip()

        try:
            parsed = json.loads(raw_output)
            return {"tweets": parsed.get("tweets", [])}
        except Exception:
            pass

        start = raw_output.find("{")
        end = raw_output.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(raw_output[start:end+1])
                return {"tweets": parsed.get("tweets", [])}
            except Exception:
                pass

        raise RuntimeError("Gemini returned no valid JSON in the response.")
