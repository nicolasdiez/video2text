# adapters/outbound/file_prompt_loader.py

import os
import asyncio
import inspect  # para trazas logging con print

from domain.ports.outbound.prompt_loader_port import PromptLoaderPort

class FilePromptLoader(PromptLoaderPort):
    """
    Implementación de PromptLoaderPort que lee el propmt desde el sistema de archivos.
    """
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        
        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")


    async def load_prompt(self, prompt_file_name: str) -> str:
        """
        Lee el fichero de prompt de forma no bloqueante.
        """
        path = os.path.join(self.prompts_dir, prompt_file_name)
        content = await asyncio.to_thread(self._read_file, path)
        print(f"[FilePromptLoader] Prompt loaded successfully from file: {prompt_file_name}")
        
        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")
        
        return content
    

    def _read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            # Logging
            print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")
            return f.read()
