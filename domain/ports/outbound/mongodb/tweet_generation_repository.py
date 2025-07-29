# application/ports/outbound/tweet_generation_repository.py

from abc import ABC, abstractmethod
from domain.entities.tweet_generation import TweetGeneration

class TweetGenerationRepositoryPort(ABC):
    @abstractmethod
    async def save_generation(self, generation: TweetGeneration) -> str:
        """
        Inserta un documento en 'tweet_generations' con la forma:
        {
          userId: ObjectId,
          videoId: ObjectId,
          openaiRequest: {
            prompt: str,
            model: str,
            temperature: float,
            maxTokens: int
          },
          generatedAt: datetime
        }
        Devuelve el _id (string) del documento creado.
        """
        ...
