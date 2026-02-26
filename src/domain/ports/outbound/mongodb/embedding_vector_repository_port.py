# src/domain/ports/outbound/mongodb/embedding_vector_repository_port.py

from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.value_objects.embedding_vector import EmbeddingVector
from src.domain.value_objects.embedding_type import EmbeddingType


class EmbeddingVectorRepositoryPort(ABC):
    """
    Port that abstracts persistence operations for embedding vectors.
    """

    @abstractmethod
    async def save(self, embedding: EmbeddingVector) -> str:
        """
        Persist a new embedding vector and return its generated ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_tweet_and_type(self, tweet_id: str, type: EmbeddingType) -> Optional[EmbeddingVector]:
        """
        Retrieve an embedding vector for a given tweet and embedding type.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_by_tweet(self, tweet_id: str) -> None:
        """
        Delete all embeddings associated with a given tweet.
        """
        raise NotImplementedError
