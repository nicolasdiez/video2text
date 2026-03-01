# src/adapters/outbound/embedding_vector_openai_client.py

# Modelos actuales recomendados:
#   text-embedding-3-small → 1536 dimensiones
#   text-embedding-3-large → 3072 dimensiones

import aiohttp
from typing import List
from domain.ports.outbound.embedding_vector_port import EmbeddingVectorPort

# logging
import inspect
import logging

logger = logging.getLogger(__name__)


class EmbeddingVectorOpenAIClient(EmbeddingVectorPort):
    """
    Adapter that communicates with OpenAI's embedding API to generate embedding vectors.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        
        # Load API key
        if not api_key:
            raise RuntimeError("API key (OpenAI) is required")
        
        self.api_key = api_key
        self.base_url = base_url


    async def get_embedding(self, text: str, model: str) -> List[float]:
        """
        Generate an embedding vector for the given text using OpenAI's embedding API.
        """
        # Validate API key
        if not self.api_key:
            logger.error("Missing API key", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")
        
        # compose URL and headers
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # payload
        payload = {
            "model": model,
            "input": text,
        }

        # consume openAI to get embedding vector of the 'text'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    body = await response.text()
                    raise RuntimeError(
                        f"OpenAI embedding API error {response.status}: {body}"
                    )

                data = await response.json()

                # Extract the embedding vector
                try:
                    return data["data"][0]["embedding"]
                except Exception as e:
                    raise RuntimeError(
                        f"Unexpected embedding API response format: {data}"
                    ) from e
