# adapters/outbound/openai_client.py

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


    async def generate_tweets(self, prompt_user_message: str, prompt_system_message: str, max_sentences: int = 3, output_language: str = "Spanish (ESPAÑOL)", model: str = "gpt-3.5-turbo") -> list[str]:
        
        # validate API KEY
        if not self.api_key:
            logger.error("Missing OPENAI_API_KEY", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

        # validate inputs early and log context
        if not prompt_system_message or not str(prompt_system_message).strip():
            logger.error("Empty prompt_system_message provided; aborting OpenAI call", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise ValueError("prompt_system_message must not be empty")

        if not prompt_user_message or not str(prompt_user_message).strip():
            logger.error("Empty prompt_user_message provided; aborting OpenAI call", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise ValueError("prompt_user_message must not be empty")

        tweets = await asyncio.to_thread(self._call_and_process, prompt_user_message, prompt_system_message, max_sentences, output_language, model)

        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return tweets


    def _call_and_process(self, prompt_user_message: str, prompt_system_message: str, max_sentences: int, output_language: str, model: str) -> list[str]:
        
        client = OpenAI(api_key=self.api_key)

        # the only block of the prompt that is hard-coded
        objective_block = (
            f"=== OBJECTIVE ===\n"
            f"Based on the provided transcript, create exactly {max_sentences} short, standalone tweets in {output_language} language.\n\n"
        )

        # Build system_content respecting the input prompt_system_message
        system_content = prompt_system_message.rstrip() + "\n\n" + objective_block

        system_message = {"role": "system", "content": system_content}
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
