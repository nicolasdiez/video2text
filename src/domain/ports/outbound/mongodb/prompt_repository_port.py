# domain/ports/outbound/mongodb/prompt_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.prompt import Prompt

class PromptRepositoryPort(ABC):
    """
    Outbound port: defines CRUD operations for the Prompt entity in the persistence layer.
    """

    @abstractmethod
    async def save(self, prompt: Prompt) -> str:
        """
        Persist a new Prompt entity. Returns the generated document ID as a string.
        """
        ...

    @abstractmethod
    async def find_by_id(self, prompt_id: str) -> Optional[Prompt]:
        """
        Retrieve a Prompt by its ID. Returns None if not found.
        """
        ...

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Prompt]:
        """
        List all Prompts associated with a given user ID.
        """
        ...

    @abstractmethod
    async def find_by_channel_id(self, channel_id: str) -> List[Prompt]:
        """
        List all Prompts associated with a given channel ID.
        """
        ...

    @abstractmethod
    async def find_by_user_and_channel(self, user_id: str, channel_id: str) -> Optional[Prompt]:
        """
        Retrieve a single Prompt by both user_id and channel_id.
        Returns None if not found.
        """
        ...

    @abstractmethod
    async def update(self, prompt: Prompt) -> None:
        """
        Update an existing Prompt document.
        """
        ...

    @abstractmethod
    async def delete(self, prompt_id: str) -> None:
        """
        Delete a Prompt by its ID.
        """
        ...
