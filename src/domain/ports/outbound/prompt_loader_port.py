# src/domain/ports/outbound/prompt_loader_port.py


from abc import ABC, abstractmethod

class PromptLoaderPort(ABC):
    """
    Puerto que define la abstracción para cargar un template de prompt.
    """

    @abstractmethod
    async def load_prompt(self, prompt_file_name: str) -> str:
        """
        Devuelve el contenido completo del fichero de prompt.

        :param prompt_file_name: nombre del archivo en el directorio de prompts
        :return: texto plano del prompt
        """
        raise NotImplementedError
