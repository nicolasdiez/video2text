# adapters/outbound/openai_client.py

import os
import re
import asyncio
import inspect  # para trazas logging con print

from openai import OpenAI
from domain.ports.outbound.openai_port import OpenAIPort

class OpenAIClient(OpenAIPort):
    """
    Implementación de OpenAIPort usando la librería oficial openai.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")


    async def generate_tweets(self, prompt: str, max_sentences: int = 3, model: str = "gpt-3.5-turbo") -> list[str]:
        
        if not self.api_key:
            raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

        clean = await asyncio.to_thread(self._call_and_process, prompt, max_sentences, model)

        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")

        return clean


    def _call_and_process(self, prompt: str, max_sentences: int, model: str) -> list[str]:
        
        client = OpenAI(api_key=self.api_key)

        system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant."
                "Summarize the following transcript into independent, education-focused sentences designed for Twitter." 
                "Output each sentence on its own line, without numbering or bullet points."
            )
        }
        user_message = {"role": "user", "content": prompt}

        response = client.chat.completions.create(
            model=model,
            messages=[system_message, user_message],
            temperature=0.7
        )

        raw_output = response.choices[0].message.content
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        clean = [re.sub(r"^[\d\.\-\)\s]+", "", line) for line in lines]

        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")

        return clean
