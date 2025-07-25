# adapters/outbound/file_prompt_loader.py


import os
import asyncio
from domain.ports.prompt_loader_port import PromptLoaderPort

class FilePromptLoader(PromptLoaderPort):
    """
    Implementación de PromptLoaderPort que lee desde el sistema de archivos.
    """

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir

    async def load_prompt(self, prompt_file_name: str) -> str:
        """
        Lee el fichero de prompt de forma no bloqueante.
        """
        path = os.path.join(self.prompts_dir, prompt_file_name)
        content = await asyncio.to_thread(self._read_file, path)
        print(f"[FilePromptLoader] Prompt loaded successfully from file: {prompt_file_name}")
        return content

    def _read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
