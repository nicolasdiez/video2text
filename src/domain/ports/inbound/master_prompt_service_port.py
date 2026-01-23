# src/domain/ports/master_prompt_service_port.py

from abc import ABC, abstractmethod
from typing import List, Optional
from bson import ObjectId

from domain.entities.master_prompt import MasterPrompt


class MasterPromptServicePort(ABC):
    """
    Inbound port for master prompt operations.
    Exposes business-level actions for managing master prompts.
    """

    @abstractmethod
    async def get_master_prompt(self, master_prompt_id: ObjectId) -> Optional[MasterPrompt]:
        """
        Retrieve a master prompt by its ID.
        """
        pass

    @abstractmethod
    async def list_master_prompts(self) -> List[MasterPrompt]:
        """
        Retrieve all master prompts.
        """
        pass

    @abstractmethod
    async def list_master_prompts_by_category(self, category: str) -> List[MasterPrompt]:
        """
        Retrieve all master prompts belonging to a given category.
        """
        pass

    @abstractmethod
    async def create_master_prompt(self, master_prompt: MasterPrompt) -> MasterPrompt:
        """
        Create a new master prompt.
        """
        pass

    @abstractmethod
    async def update_master_prompt(self, master_prompt_id: ObjectId, update_data: dict) -> Optional[MasterPrompt]:
        """
        Update an existing master prompt.
        """
        pass

    @abstractmethod
    async def delete_master_prompt(self, master_prompt_id: ObjectId) -> bool:
        """
        Delete a master prompt by ID.
        """
        pass
