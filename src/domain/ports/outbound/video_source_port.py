# src/domain/ports/outbound/video_source_port.py

from abc import ABC, abstractmethod
from typing import List, Protocol

class VideoMetadata(Protocol):
    videoId: str    # youtube video id
    title: str
    url: str

class VideoSourcePort(ABC):
    @abstractmethod
    async def fetch_new_videos(self, channel_id: str, max_videos_to_fetch_per_channel: int) -> List[VideoMetadata]:
        raise NotImplementedError
