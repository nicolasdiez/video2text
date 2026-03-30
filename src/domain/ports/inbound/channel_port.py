# src/domain/ports/inbound/channel_port.py

from abc import ABC, abstractmethod
from typing import Optional


class ChannelPort(ABC):
    """
    Inbound port for channel-related operations.
    Defines the application-level actions that ChannelService must implement.
    """

    @abstractmethod
    async def update_channel_prompt(
        self,
        channel_id: str,
        selected_prompt_id: Optional[str] = None,
        selected_master_prompt_id: Optional[str] = None,
    ) -> None:
        """
        Update the selected prompt for a channel.
        Business rules enforced by the implementation:
        - A channel cannot select both a user prompt and a master prompt.
        - A channel must select at least one of them.
        """
        raise NotImplementedError
