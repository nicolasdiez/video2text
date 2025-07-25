from abc import ABC, abstractmethod
from typing import List, Protocol

class VideoMetadata(Protocol):
    videoId: str
    title: str
    url: str

class VideoSourcePort(ABC):
    @abstractmethod
    async def fetch_new_videos(self, channel_id: str) -> List[VideoMetadata]:
        ...
