# src/application/services/master_prompt_service.py

from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from domain.entities.master_prompt import MasterPrompt
from domain.ports.inbound.master_prompt_service_port import MasterPromptServicePort
from domain.ports.outbound.mongodb.master_prompt_repository_port import MasterPromptRepositoryPort


class MasterPromptService(MasterPromptServicePort):
    """
    Application service implementing business logic for master prompts.
    """

    def __init__(self, master_prompt_repo: MasterPromptRepositoryPort):
        self.master_prompt_repo = master_prompt_repo

    # ---------------------------------------------------------
    # READ OPERATIONS
    # ---------------------------------------------------------
    async def get_master_prompt(self, master_prompt_id: ObjectId) -> Optional[MasterPrompt]:
        return await self.master_prompt_repo.find_by_id(master_prompt_id)

    async def list_master_prompts(self) -> List[MasterPrompt]:
        return await self.master_prompt_repo.find_all()

    async def list_master_prompts_by_category(self, category: str) -> List[MasterPrompt]:
        return await self.master_prompt_repo.find_by_category(category)

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    async def create_master_prompt(self, master_prompt: MasterPrompt) -> MasterPrompt:
        # Business rule: category and subcategory must not be empty
        if not master_prompt.category or not master_prompt.subcategory:
            raise ValueError("Master prompt must have both category and subcategory.")

        # Set timestamps
        master_prompt.created_at = datetime.utcnow()
        master_prompt.updated_at = datetime.utcnow()

        return await self.master_prompt_repo.insert_one(master_prompt)

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    async def update_master_prompt(self, master_prompt_id: ObjectId, update_data: dict) -> Optional[MasterPrompt]:
        # Business rule: prevent empty category/subcategory
        if "category" in update_data and not update_data["category"]:
            raise ValueError("Category cannot be empty.")

        if "subcategory" in update_data and not update_data["subcategory"]:
            raise ValueError("Subcategory cannot be empty.")

        # Always update timestamp
        update_data["updatedAt"] = datetime.utcnow()

        return await self.master_prompt_repo.update_by_id(master_prompt_id, update_data)

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------
    async def delete_master_prompt(self, master_prompt_id: ObjectId) -> bool:
        return await self.master_prompt_repo.delete_by_id(master_prompt_id)
