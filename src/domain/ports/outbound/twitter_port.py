# src/domain/ports/twitter_port.py

from abc import ABC, abstractmethod

class TwitterPort(ABC):
    """
    Puerto que abstrae la publicación de tweets (X).
    """

    @abstractmethod
    async def publish(self, text: str) -> str:
        """
        Publica un tweet con el texto dado y devuelve el tweet ID.
        
        :param text: contenido del tweet
        :return: ID del tweet publicado
        """
        pass
