# domain/ports/openai_port.py

from abc import ABC, abstractmethod

class OpenAIPort(ABC):
    """
    Puerto que abstrae la generación de texto vía OpenAI.
    """

    @abstractmethod
    async def generate_sentences(self, prompt: str, max_sentences: int, model: str) -> list[str]:
        """
        Envía el prompt a un modelo de OpenAI y devuelve una lista de oraciones limpias.

        :param prompt: texto de entrada para el modelo
        :param max_sentences: número máximo de oraciones de salida
        :param model: identificador del modelo OpenAI
        :return: lista de oraciones sin numeración ni viñetas
        """
        pass
