# src/domain/ports/outbound/embedding_vector_port.py

from abc import ABC, abstractmethod
from typing import List


class EmbeddingVectorPort(ABC):
    """
    Port that abstracts the generation of embedding vectors from text.
    Implementations may use OpenAI, Mistral, Cohere, or any other provider.
    """

    @abstractmethod
    async def get_embedding(self, text: str, model: str) -> List[float]:
        """
        Generate an embedding vector for the given text.

        :param text: input text to embed
        :param model: identifier of the embedding model to use
        :return: list of floats representing the embedding vector
        """
        raise NotImplementedError