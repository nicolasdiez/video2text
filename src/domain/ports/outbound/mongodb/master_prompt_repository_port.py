# src/domain/ports/outboud/mongodb/master_prompt_repository_port.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from bson import ObjectId

from domain.entities.master_prompt import MasterPrompt


class MasterPromptRepositoryPort(ABC):
    """
    Outbound port for accessing master prompts.
    The domain/application layer depends on this interface,
    while infrastructure (Mongo, etc.) implements it.
    """

    @abstractmethod
    async def find_by_id(self, master_prompt_id: ObjectId) -> Optional[MasterPrompt]:
        """
        Retrieve a master prompt by its ID.
        """
        pass

    @abstractmethod
    async def find_all(self) -> List[MasterPrompt]:
        """
        Retrieve all master prompts.
        """
        pass

    @abstractmethod
    async def find_by_category(self, category: str) -> List[MasterPrompt]:
        """
        Retrieve all master prompts belonging to a given category.
        """
        pass

    @abstractmethod
    async def insert_one(self, master_prompt: MasterPrompt) -> MasterPrompt:
        """
        Insert a new master prompt and return the stored entity.
        """
        pass

    @abstractmethod
    async def update_by_id(self, master_prompt_id: ObjectId, update_data: Dict[str, Any]) -> Optional[MasterPrompt]:
        """
        Update an existing master prompt and return the updated entity.
        """
        pass

    @abstractmethod
    async def delete_by_id(self, master_prompt_id: ObjectId) -> bool:
        """
        Delete a master prompt by ID.
        Returns True if a document was deleted.
        """
        pass
