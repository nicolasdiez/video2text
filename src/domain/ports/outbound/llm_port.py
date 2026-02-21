# src/domain/ports/openai_port.py

from abc import ABC, abstractmethod

class OpenAIPort(ABC):
    """
    Puerto que abstrae la generación de texto vía OpenAI.
    """

    @abstractmethod
    async def generate_tweets(self, prompt_user_message: str, prompt_system_message: str, max_tweets: int, output_language: str, model: str) -> list[str]:
        """
        Envía el prompt a un modelo de OpenAI y devuelve una lista de oraciones tweets limpias.

        :param prompt_user_message: actual query or request from the person interacting with the model
        :param prompt_system_message: sets the overall behavior, tone, or rules for the model
        :param max_tweets: número máximo de oraciones tweet de salida
        :param model: identificador del modelo OpenAI
        :return: lista de oraciones sin numeración ni viñetas
        """
        pass
