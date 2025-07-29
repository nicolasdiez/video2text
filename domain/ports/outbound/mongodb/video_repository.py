# application/ports/outbound/video_repository.py

from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from domain.entities.video import VideoMetadata
from domain.entities.video import TranscriptSegment

class VideoRepositoryPort(ABC):
    @abstractmethod
    async def save_video(
        self,
        channel_id: str,
        video_metadata: VideoMetadata,
        transcript: str,
        transcript_segments: List[TranscriptSegment],
        transcript_fetched_at: datetime,
        tweets_generated: bool,
        created_at: datetime,
        updated_at: datetime
    ) -> str:
        """
        Inserta un documento en la colección 'videos' con la forma:
        {
          channelId: ObjectId, 
          youtubeVideoId: str, 
          title: str, 
          url: str,
          transcript: str,
          transcriptSegments: [{ start, duration, text }, …],
          transcriptFetchedAt: datetime,
          tweetsGenerated: bool,
          createdAt: datetime,
          updatedAt: datetime
        }
        Devuelve el _id (string) del documento insertado.
        """
        ...
