# application/ports/outbound/tweet_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.tweet import Tweet

class TweetRepositoryPort(ABC):
    @abstractmethod
    async def save(self, tweet: Tweet) -> str:
        """
        Persiste un Tweet y devuelve el nuevo _id como cadena.
        """
        ...

    @abstractmethod
    async def find_by_id(self, tweet_id: str) -> Optional[Tweet]:
        """
        Recupera un Tweet por su _id.
        """
        ...

    @abstractmethod
    async def find_by_generation_id(self, generation_id: str) -> List[Tweet]:
        """
        Lista todos los Tweets asociados a una generación de tweets.
        """
        ...

    @abstractmethod
    async def update(self, tweet: Tweet) -> None:
        """
        Actualiza un Tweet existente.
        """
        ...
