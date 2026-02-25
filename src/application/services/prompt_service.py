# application/services/prompt_service.py
# Description: Application-level service that orchestrates prompt lifecycle operations and maintains channel–prompt consistency.

# Important Reminder:
# - Si un servicio A necesita otro servicio B, inyectar B en A por constructor desde el composition root (main.py) (A recibe B). Evitae que A importe y construya B por su cuenta (previene acoplamiento y ciclos).

from typing import Optional, List
from domain.entities.user_prompt import UserPrompt
from domain.entities.channel import Channel
from domain.ports.inbound.user_prompt_service_port import PromptServicePort
from domain.ports.outbound.mongodb.user_prompt_repository_port import PromptRepositoryPort
from domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort


class PromptService (PromptServicePort):
    """
    Application-level service responsible for orchestrating prompt-related operations.
    - Coordinates prompt and channel repositories.
    - Ensures domain rules are enforced (e.g., clearing selected_prompt_id when deleting a prompt).
    - Does NOT perform prompt composition (handled by PromptComposerService).
    """

    def __init__(self, prompt_repo: PromptRepositoryPort, channel_repo: ChannelRepositoryPort):
        self.prompt_repo = prompt_repo
        self.channel_repo = channel_repo

    async def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """
        Retrieve a prompt by ID.
        """
        return await self.prompt_repo.find_by_id(prompt_id)

    async def create_prompt(self, prompt: Prompt) -> str:
        """
        Create a new prompt and return its ID.
        """
        return await self.prompt_repo.save(prompt)

    async def update_prompt(self, prompt: Prompt) -> None:
        """
        Update an existing prompt.
        """
        await self.prompt_repo.update(prompt)

    async def delete_prompt(self, prompt_id: str) -> None:
        """
        Delete a prompt and clear selected_prompt_id in any channels referencing it.
        This ensures referential integrity at the application level.
        """
        # 1. Delete the prompt
        await self.prompt_repo.delete(prompt_id)

        # 2. Find channels that reference this prompt
        channels: List[Channel] = await self.channel_repo.find_by_selected_prompt_id(prompt_id)

        # 3. Clear selected_prompt_id for each affected channel
        for ch in channels:
            ch.selected_prompt_id = None
            await self.channel_repo.update(ch)

    async def delete_all_prompts(self) -> int:
        """
        Delete all prompts and clear selected_prompt_id in all channels.
        Returns the number of deleted prompts.
        """
        # 1. Delete all prompts
        deleted_count = await self.prompt_repo.delete_all()

        # 2. Clear selected_prompt_id in all channels
        channels: List[Channel] = await self.channel_repo.find_all()
        for ch in channels:
            if ch.selected_prompt_id:
                ch.selected_prompt_id = None
                await self.channel_repo.update(ch)

        return deleted_count

    async def set_selected_prompt_for_channel(self, channel_id: str, prompt_id: Optional[str]) -> None:
        """
        Assign or clear the selected prompt for a channel.
        - If prompt_id is None → clears the selection.
        - If prompt_id is provided → validates that the prompt exists and belongs to the same user.
        """
        # Retrieve channel
        channel = await self.channel_repo.find_by_id(channel_id)
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        # If clearing selection
        if prompt_id is None:
            channel.selected_prompt_id = None
            await self.channel_repo.update(channel)
            return

        # Validate prompt exists
        prompt = await self.prompt_repo.find_by_id(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        # Validate prompt belongs to same user
        if prompt.user_id != channel.user_id:
            raise ValueError(
                f"Prompt {prompt_id} does not belong to user {channel.user_id} "
                f"(prompt.user_id={prompt.user_id})"
            )

        # Assign selection
        channel.selected_prompt_id = prompt_id
        await self.channel_repo.update(channel)
