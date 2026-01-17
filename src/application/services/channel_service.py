# src/application/services/channel_service.py

# Important Reminder:
# - Si un servicio A necesita otro servicio B, inyectar B en A por constructor desde el composition root (main.py) (A recibe B). Evitae que A importe y construya B por su cuenta (previene acoplamiento y ciclos).


from datetime import datetime
from typing import Optional

from domain.ports.inbound.channel_service_port import ChannelServicePort
from domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort


class ChannelService(ChannelServicePort):
    """
    Application-level service responsible for channel-related operations.
    Enforces business rules around prompt selection and delegates persistence
    to the channel repository.
    """

    def __init__(self, channel_repo: ChannelRepositoryPort):
        self.channel_repo = channel_repo

    async def update_channel_prompt(
        self,
        channel_id: str,
        selected_prompt_id: Optional[str] = None,
        selected_master_prompt_id: Optional[str] = None,
    ) -> None:
        """
        Update the selected prompt for a channel while enforcing business rules:
        - A channel cannot select both a user prompt and a master prompt.
        - A channel must select at least one of them.
        """

        # Business rule: mutually exclusive
        if selected_prompt_id and selected_master_prompt_id:
            raise ValueError(
                "A channel cannot select both a user prompt and a master prompt."
            )

        # Business rule: require at least one
        if not selected_prompt_id and not selected_master_prompt_id:
            raise ValueError(
                "A channel must select either a user prompt or a master prompt."
            )

        # Persist changes
        await self.channel_repo.update_by_id(
            channel_id,
            {
                "selectedPromptId": selected_prompt_id,
                "selectedMasterPromptId": selected_master_prompt_id,
                "updatedAt": datetime.utcnow(),
            },
        )
