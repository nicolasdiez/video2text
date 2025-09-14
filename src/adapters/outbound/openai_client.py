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
                f"You are a witty, insightful financial educator who writes engaging, human-sounding tweets "
                f"that spark curiosity and conversation. Based on the transcript, create exactly {max_sentences} "
                f"short, standalone tweets in Spanish (ESPAÑOL) that feel personal and relatable. "
                f"Use a conversational tone, occasional emojis, and relevant hashtags. "
                f"Each tweet should have a hook or insight that makes people want to reply or share. "
                f"Do not number them — put each tweet on its own line."
                f"You must reference specific details from the transcript, such as names, events, strategies, and outcomes. Avoid generic advice. Each tweet must clearly connect to the video's story."
                f"Write as if you are live-tweeting the key moments of the story, with a mix of intrigue and insight. Use hooks that make readers curious about the full story."
            )
        }
        user_message = {"role": "user", "content": prompt}

        response = client.chat.completions.create(
            model=model,
            messages=[system_message, user_message],
            temperature=0.9,            # 0.9 for more creativity
            presence_penalty=0.3,       # Slightly positive (e.g., 0.3) to encourage varied ideas.
            frequency_penalty=0.2       # Slightly positive (e.g., 0.2) to avoid repetitive phrasing.
        )

        raw_output = response.choices[0].message.content
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        clean = [re.sub(r"^[\d\.\-\)\s]+", "", line) for line in lines]

        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")

        return clean
