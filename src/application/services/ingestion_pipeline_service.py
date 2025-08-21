# src/application/services/ingestion_pipeline_service.py

import asyncio
from datetime import datetime
from typing import List

from src.domain.ports.inbound.ingestion_pipeline_port import IngestionPipelinePort
from src.domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from src.domain.ports.outbound.mongodb.video_repository_port import VideoRepositoryPort
from src.domain.ports.outbound.video_source_port import VideoSourcePort, VideoMetadata
from src.domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort
from src.domain.ports.outbound.transcription_port import TranscriptionPort
from src.domain.ports.outbound.openai_port import OpenAIPort
from src.domain.entities.video import Video
from src.domain.entities.channel import Channel
from src.domain.entities.tweet import Tweet


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
        video_source: VideoSourcePort,
        video_repo: VideoRepositoryPort,
        transcription_service: TranscriptionPort,
        openai_service: OpenAIPort,
        tweet_repo: TweetRepositoryPort,
    ):
        self.channel_repo = channel_repo
        self.video_source = video_source
        self.video_repo = video_repo
        self.transcription_service = transcription_service
        self.openai_service = openai_service
        self.tweet_repo = tweet_repo

    async def run_for_user(self, user_id: str, channel_id: str, prompt_file: str, max_videos: int = 10, max_tweets: int = 5) -> None:
        
         # 1. Load prompt base from file (without blocking thread)
        base_prompt = await self.prompt_loader.load_prompt(prompt_file)
        print(f"[IngestionPipelineService] Prompt cargado: {prompt_file}")

        # 2. Fetch all channels the user is subscribed to
        channels: List[Channel] = await self.channel_repo.find_by_user_id(user_id)

        # 3. Process each channel independently
        for channel in channels:
            # 4. Fetch new videos for this channel
            videos: List[Video] = await self.video_source.fetch_new_videos(channel.youtube_channel_id, max_videos)

            # 5. Process each video independently
            for video in videos:
                # 6. Save video in DB (if doesnt exist yet)
                video = await self.video_repo.find_by_id(video.id)
                if not video:
                    video = Video(
                        id=None,
                        video_id=video.id,
                        channel_id=channel.id,
                        title=video.title,
                        url=video.url,
                        transcript=None,
                        transcript_fetched_at=None,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    saved_id = await self.video_repo.save(video)
                    video.id = saved_id

                # 7. If the video has no transcription yet, fetch it and update the record
                if not video.transcript_fetched_at:
                    transcript = await self.transcription_service.transcribe(video)
                    video.transcript = transcript
                    video.transcript_fetched_at = datetime.utcnow()
                    # persist the updated video entity
                    await self.video_repo.update_video(video)

                # 8. Generate complete prompt
                prompt = f"{base_prompt.strip()}\n{video.transcript}"

                # 4. Generate tweet texts for the video
                tweets: List[Tweet] = await self.openai_service.generate_tweets(
                    prompt=prompt,
                    max_sentences=max_tweets,
                    model="gpt-3.5-turbo")

                print(f"[IngestionPipelineService] {len(tweets)} tweets generados para video {video.id}")
                
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
