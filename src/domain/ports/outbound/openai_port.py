# src/domain/ports/openai_port.py

from abc import ABC, abstractmethod

class OpenAIPort(ABC):
    """
    Puerto que abstrae la generación de texto vía OpenAI.
    """

    @abstractmethod
    async def generate_tweets(self, prompt: str, max_tweets: int, model: str) -> list[str]:
        """
        Envía el prompt a un modelo de OpenAI y devuelve una lista de oraciones tweets limpias.

        :param prompt: texto de entrada para el modelo
        :param max_tweets: número máximo de oraciones tweet de salida
        :param model: identificador del modelo OpenAI
        :return: lista de oraciones sin numeración ni viñetas
        """
        pass
