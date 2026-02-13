# src/domain/ports/inbound/prompt_service_port.py

from abc import ABC, abstractmethod
from typing import Optional, List

from domain.entities.prompt import Prompt
from domain.entities.channel import Channel


class PromptServicePort(ABC):
    """
    Inbound port for prompt-related operations.
    Defines the application-level actions that the PromptService must implement.
    """

    @abstractmethod
    async def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """
        Retrieve a prompt by its ID.
        """
        pass

    @abstractmethod
    async def create_prompt(self, prompt: Prompt) -> str:
        """
        Create a new prompt and return its ID.
        """
        pass

    @abstractmethod
    async def update_prompt(self, prompt: Prompt) -> None:
        """
        Update an existing prompt.
        """
        pass

    @abstractmethod
    async def delete_prompt(self, prompt_id: str) -> None:
        """
        Delete a prompt and clear selected_prompt_id in any channels referencing it.
        """
        pass

    @abstractmethod
    async def delete_all_prompts(self) -> int:
        """
        Delete all prompts and clear selected_prompt_id in all channels.
        Returns the number of deleted prompts.
        """
        pass

    @abstractmethod
    async def set_selected_prompt_for_channel(self, channel_id: str, prompt_id: Optional[str]) -> None:
        """
        Assign or clear the selected prompt for a channel.
        - If prompt_id is None → clears the selection.
        - If prompt_id is provided → validates that the prompt exists and belongs to the same user.
        """
        pass
