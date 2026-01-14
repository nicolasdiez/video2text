class PromptServicePort(ABC):

    async def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        ...