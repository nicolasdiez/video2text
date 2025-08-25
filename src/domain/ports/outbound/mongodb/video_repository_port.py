# domain/ports/outbound/mongodb/video_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.video import Video


class VideoRepositoryPort(ABC):
    @abstractmethod
    async def save(self, video: Video) -> str:
        """
        Persist a new video.
        Returns the generated video ID.
        """
        ...

    @abstractmethod
    async def find_by_id(self, video_id: str) -> Optional[Video]:
        """
        Retrieve a single video by its ID.
        """
        ...

    @abstractmethod
    async def find_by_youtube_video_id(self, youtube_video_id: str) -> Optional[Video]:
        """
        Fetch one video by its YouTube video identifier.
        """
        ...

    @abstractmethod
    async def find_by_channel(
        self,
        channel_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Video]:
        """
        List videos for a given channel, with optional pagination.
        """
        ...

    @abstractmethod
    async def find_videos_pending_tweets(
        self,
        limit: int = 50
    ) -> List[Video]:
        """
        List videos that haven't had tweets generated yet.
        """
        ...

    @abstractmethod
    async def update(self, video: Video) -> None:
        """
        Update an existing video.
        """
        ...

    @abstractmethod
    async def delete(self, video_id: str) -> None:
        """
        Delete a video by its ID.
        """
        ...
