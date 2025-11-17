# domain/ports/outbound/mongodb/channel_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Optional
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
        ...

    @abstractmethod
    async def find_by_id(self, channel_id: str) -> Optional[Channel]:
        """
        Retrieve a Channel by its ID. Returns None if not found.
        """
        ...

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Channel]:
        """
        List all Channels associated with a given user ID.
        """
        ...

    @abstractmethod
    async def find_by_youtube_channel_id(
        self, youtube_channel_id: str
    ) -> Optional[Channel]:
        """
        Retrieve a Channel by its YouTube channel ID.
        """
        ...

    @abstractmethod
    async def update(self, channel: Channel) -> None:
        """
        Update an existing Channel document.
        """
        ...

    @abstractmethod
    async def delete(self, channel_id: str) -> None:
        """
        Delete a Channel by its ID.
        """
        ...

    @abstractmethod
    async def delete_all(self) -> int:
        """
        Delete all documents in channels collection. Returns number deleted.
        """
        ...

