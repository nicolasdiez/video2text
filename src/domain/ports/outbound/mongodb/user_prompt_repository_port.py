# domain/ports/outbound/mongodb/user_prompt_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.user_prompt import UserPrompt

class UserPromptRepositoryPort(ABC):
    """
    Outbound port: defines CRUD operations for the User Prompt entity in the persistence layer.
    """

    @abstractmethod
    async def save(self, prompt: UserPrompt) -> str:
        """
        Persist a new UserPrompt entity. Returns the generated document ID as a string.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, prompt_id: str) -> Optional[UserPrompt]:
        """
        Retrieve a UserPrompt by its ID. Returns None if not found.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[UserPrompt]:
        """
        List all UserPrompts associated with a given user ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, prompt: UserPrompt) -> None:
        """
        Update an existing UserPrompt document.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, prompt_id: str) -> None:
        """
        Delete a UserPrompt by its ID.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def delete_all(self) -> int:
        """
        Delete all documents in user_prompts collection. Returns number deleted.
        """
        raise NotImplementedError
