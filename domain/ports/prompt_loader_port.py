# domain/ports/prompt_loader_port.py
# La convención de usar “Client” suele estar reservada para adaptadores que consumen un servicio externo, como una API HTTP o una base de datos. En cambio, cuando la funcionalidad del adaptador es leer algo (como cargar ficheros), es común usar nombres como *Loader, *Reader, o *Fetcher para que el nombre refleje más precisamente lo que hace.

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
        pass
