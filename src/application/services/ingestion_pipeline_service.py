# src/application/services/ingestion_pipeline_service.py

import asyncio
from datetime import datetime
from typing import List

from src.domain.ports.inbound.ingestion_pipeline_port import IngestionPipelinePort
from src.domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from src.domain.ports.outbound.mongodb.video_repository_port import VideoRepositoryPort
from src.domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort
from src.domain.ports.outbound.transcription_port import TranscriptionPort
from src.domain.ports.outbound.openai_port import OpenAIPort
from src.domain.entities.video import Video
from src.domain.entities.channel import Channel


class IngestionPipelineService(IngestionPipelinePort):
    """
    Orchestrates the ingestion pipeline:
      1. Retrieve channels for a user
      2. For each channel:
         a) Find new videos
         b) Transcribe missing videos
         c) Generate tweets for each video
         d) Persist generated tweets
    """

    def __init__(
        self,
        channel_repo: ChannelRepositoryPort,
        video_repo: VideoRepositoryPort,
        transcription_service: TranscriptionPort,
        openai_service: OpenAIPort,
        tweet_repo: TweetRepositoryPort,
    ):
        self.channel_repo = channel_repo
        self.video_repo = video_repo
        self.transcription_service = transcription_service
        self.openai_service = openai_service
        self.tweet_repo = tweet_repo

    async def run(self, user_id: str) -> None:
        # 1. Fetch all channels the user is subscribed to
        channels: List[Channel] = await self.channel_repo.find_by_user_id(user_id)

        for channel in channels:
            # 2. Load new videos for this channel
            videos: List[Video] = await self.video_repo.find_new_videos(channel.id)

            for video in videos:
                # 3. If the video has no transcription yet, fetch it and update the record
                if not video.transcript_fetched_at:
                    transcript = await self.transcription_service.fetch_transcript(video)
                    video.transcript = transcript
                    video.transcript_fetched_at = datetime.utcnow()
                    # persist the updated video entity
                    await self.video_repo.save(video)

                # 4. Generate tweet texts for the video
                tweet_texts: List[str] = await self.openai_service.generate_for_video(video)

                # 5. Build tweet records for batch saving
                tweet_records = [
                    {
                        "video_id": video.id,
                        "text": text,
                        "generated_at": datetime.utcnow(),
                    }
                    for text in tweet_texts
                ]

                # 6. Save all generated tweets in MongoDB
                await self.tweet_repo.save_all(tweet_records)
