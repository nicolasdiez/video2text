# src/domain/ports/outbound/mongodb/channel_repository_port.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from bson import ObjectId
from domain.entities.channel import Channel


class ChannelRepositoryPort(ABC):
    """
    Outbound port: defines CRUD operations and queries for the Channel aggregate in the persistence layer.
    """

    @abstractmethod
    async def save(self, channel: Channel) -> str:
        """
        Persist a new Channel entity. Returns the generated document ID as a string.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, channel_id: str) -> Optional[Channel]:
        """
        Retrieve a Channel by its ID. Returns None if not found.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Channel]:
        """
        List all Channels associated with a given user ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_youtube_channel_id(
        self, youtube_channel_id: str
    ) -> Optional[Channel]:
        """
        Retrieve a Channel by its YouTube channel ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_selected_prompt_id(self, prompt_id: str) -> List[Channel]:
        """
        Retrieve channels that reference the given user prompt ID in selected_prompt_id.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_all(self) -> List[Channel]:
        """
        Retrieve all channels.
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, channel: Channel) -> None:
        """
        Update an existing Channel document using a full Channel entity.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_by_id(self, channel_id: ObjectId, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a channel document by its ID.

        :param channel_id: ObjectId of the channel to update.
        :param update_data: Dict with fields to update (partial updates supported).
        :return: The updated channel document or None if not found.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, channel_id: str) -> None:
        """
        Delete a Channel by its ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> int:
        """
        Delete all documents in channels collection. Returns number deleted.
        """
        raise NotImplementedError