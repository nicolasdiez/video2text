# src/domain/ports/inbound/user_prompt_port.py

from abc import ABC, abstractmethod
from typing import Optional, List

from domain.entities.user_prompt import UserPrompt
from domain.entities.channel import Channel


class UserPromptPort(ABC):
    """
    Inbound port for user prompt-related operations.
    Defines the application-level actions that the PromptService must implement.
    """

    @abstractmethod
    async def get_prompt(self, prompt_id: str) -> Optional[UserPrompt]:
        """
        Retrieve a UserPrompt by its ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def create_prompt(self, prompt: UserPrompt) -> str:
        """
        Create a new UserPrompt and return its ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_prompt(self, prompt: UserPrompt) -> None:
        """
        Update an existing UserPrompt.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_prompt(self, prompt_id: str) -> None:
        """
        Delete a UserPrompt and clear selected_prompt_id in any channels referencing it.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_all_prompts(self) -> int:
        """
        Delete all UserPrompts and clear selected_prompt_id in all channels.
        Returns the number of deleted UserPrompts.
        """
        raise NotImplementedError

    @abstractmethod
    async def set_selected_prompt_for_channel(self, channel_id: str, prompt_id: Optional[str]) -> None:
        """
        Assign or clear the selected prompt for a channel.
        - If prompt_id is None → clears the selection.
        - If prompt_id is provided → validates that the prompt exists and belongs to the same user.
        """
        raise NotImplementedError
