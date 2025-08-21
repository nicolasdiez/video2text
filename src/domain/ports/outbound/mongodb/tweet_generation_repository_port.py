# domain/ports/outbound/mongodb/tweet_generation_repository_port.py

from typing import Optional, List
from domain.entities.tweet_generation import TweetGeneration

class TweetGenerationRepositoryPort:
    async def save(self, tweet_generation: TweetGeneration) -> str:
        """
        Persiste un registro de generación de tweet y devuelve el nuevo _id como cadena.
        """
        ...

    async def find_by_id(self, tg_id: str) -> Optional[TweetGeneration]:
        """
        Recupera una generación de tweet por su _id.
        """
        ...

    async def find_by_video_id(self, video_id: str) -> List[TweetGeneration]:
        """
        Lista todas las generaciones de tweet asociadas a un mismo video.
        """
        ...
