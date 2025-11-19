# adapters/outbound/openai_client.py

# Models available (code name) | Strength / Best for                 | Cost tier (qualitative) | Notes
# -----------------------------------------------------------------------------------------------
# gpt-4o                      | Highest-quality, large-context      | High                    | Use for very nuanced, long-context generations; premium per-token pricing.
# gpt-4o-mini                 | Strong creative quality, fast       | Moderate                | Best cost/quality trade-off for short creative outputs like tweets.
# gpt-4o-realtime             | Low-latency interactive generation  | High                    | Use when you need realtime responses (streaming/low latency).
# gpt-4o-32k                  | Large context window (32k tokens)   | High                    | Use when you must feed long transcripts; expensive but preserves context.
# gpt-3.5-turbo               | Cost-efficient, reliable            | Low                     | Good for bulk generation and templates; tune prompts for quality.
# -----------------------------------------------------------------------------------------------
# Practical guidance:
# - For tweet generation start with gpt-4o-mini (creative + reasonable cost).
# - Use gpt-4o or gpt-4o-32k only when transcript length or fidelity requires it.
# - Use gpt-3.5-turbo for high-volume, low-cost runs or A/B testing.
# - Costs scale with input + output tokens; output tokens dominate for short outputs.
# - Tune temperature (0.6-0.9) and penalties for variety; prompt engineering often beats switching to a pricier model.

import os
import re
import asyncio

# logging
import inspect
import logging

from openai import OpenAI
from domain.ports.outbound.openai_port import OpenAIPort

# Specific logger for this module
logger = logging.getLogger(__name__)


class OpenAIClient(OpenAIPort):
    """
    Implementación de OpenAIPort usando la librería oficial openai.
    """

    def __init__(self, api_key: str | None = None):
        
        # load api key
        if not api_key:
            raise RuntimeError("API key is required")
        self.api_key = api_key
        
        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})


    async def generate_tweets(self, prompt_user_message: str, prompt_system_message: str, model: str = "gpt-3.5-turbo") -> list[str]:
        
        # validate API KEY
        if not self.api_key:
            logger.error("Missing API key", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

        # validate inputs early and log context
        if not prompt_system_message or not str(prompt_system_message).strip():
            logger.error("Empty prompt_system_message provided; aborting OpenAI call", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise ValueError("prompt_system_message must not be empty")

        if not prompt_user_message or not str(prompt_user_message).strip():
            logger.error("Empty prompt_user_message provided; aborting OpenAI call", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise ValueError("prompt_user_message must not be empty")

        tweets = await asyncio.to_thread(self._call_and_process, prompt_user_message, prompt_system_message, model)

        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return tweets


    def _call_and_process(self, prompt_user_message: str, prompt_system_message: str, model: str) -> list[str]:
        
        client = OpenAI(api_key=self.api_key)

        system_message = {"role": "system", "content": prompt_system_message}
        user_message = {"role": "user", "content": prompt_user_message}

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[system_message, user_message],
                temperature=0.8,            #  0.0 to 2.0 --> Nivel de creatividad/aleatoriedad. Valores bajos → respuestas más deterministas y “seguras”. Valores altos → más creatividad y variación, pero también más riesgo de desviarse del tema.
                presence_penalty=0.3,       # -2.0 to 2.0 --> Penaliza o incentiva introducir nuevos temas no mencionados antes. Valores positivos → fomenta variedad temática. Valores negativos → favorece quedarse en los mismos temas.
                frequency_penalty=0.2       # -2.0 to 2.0 --> Penaliza o incentiva repetir las mismas palabras o frases. Valores positivos → reduce repeticiones. Valores negativos → permite o fomenta repeticiones.
            )
        except Exception as e:
            logger.exception("OpenAI API call failed", extra={"method": inspect.currentframe().f_code.co_name, "error": str(e)})
            raise RuntimeError(f"OpenAI API call failed: {e}") from e

        raw_output = response.choices[0].message.content
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        tweets = [re.sub(r"^[\d\.\-\)\s]+", "", line) for line in lines]

        return tweets
