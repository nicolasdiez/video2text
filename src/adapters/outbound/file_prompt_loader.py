# adapters/outbound/file_prompt_loader.py

import os
import asyncio

# logging
import inspect
import logging

from domain.ports.outbound.prompt_loader_port import PromptLoaderPort

# Specific logger for this module
logger = logging.getLogger(__name__)

class FilePromptLoader(PromptLoaderPort):
    """
    Implementación de PromptLoaderPort que lee el propmt desde el sistema de archivos.
    """
    
    def __init__(self, prompts_dir: str = "../prompts"):
        self.prompts_dir = prompts_dir
        
        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        # print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")


    async def load_prompt(self, prompt_file_name: str) -> str:
        """
        Lee el fichero de prompt de forma no bloqueante.
        """
        path = os.path.join(self.prompts_dir, prompt_file_name)
        content = await asyncio.to_thread(self._read_file, path)
        
        # Logging
        logger.info("Prompt loaded successfully (prompt_file: %s)", prompt_file_name, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        # print(f"[FilePromptLoader] Prompt loaded successfully from file: {prompt_file_name}")
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        
        return content
    

    def _read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            # Logging
            # print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")
            logger.info("File read successfully (file_path: %s)", path, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return f.read()
