# src/application/services/ingestion_pipeline_service.py

import asyncio
from datetime import datetime
from typing import List

from src.domain.ports.inbound.ingestion_pipeline_port import IngestionPipelinePort
from src.domain.ports.outbound.prompt_loader_port import PromptLoaderPort
from src.domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from src.domain.ports.outbound.mongodb.video_repository_port import VideoRepositoryPort
from src.domain.ports.outbound.video_source_port import VideoSourcePort, VideoMetadata
from src.domain.ports.outbound.mongodb.tweet_generation_repository_port import TweetGenerationRepositoryPort
from src.domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort
from src.domain.ports.outbound.transcription_port import TranscriptionPort
from src.domain.ports.outbound.openai_port import OpenAIPort

from src.domain.entities.video import Video
from src.domain.entities.channel import Channel
from src.domain.entities.tweet import Tweet
from src.domain.entities.tweet_generation import TweetGeneration, OpenAIRequest


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
        prompt_loader: PromptLoaderPort,
        channel_repo: ChannelRepositoryPort,
        video_source: VideoSourcePort,
        video_repo: VideoRepositoryPort,
        transcription_service: TranscriptionPort,
        openai_service: OpenAIPort,
        tweet_generation_repo: TweetGenerationRepositoryPort,
        tweet_repo: TweetRepositoryPort,
    ):
        self.prompt_loader = prompt_loader
        self.channel_repo = channel_repo
        self.video_source = video_source
        self.video_repo = video_repo
        self.transcription_service = transcription_service
        self.openai_service = openai_service
        self.tweet_generation_repo = tweet_generation_repo
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
            videos_metadata: List[VideoMetadata] = await self.video_source.fetch_new_videos(channel.youtube_channel_id, max_videos)

            # 5. Process each video independently
            for video_metadata in videos_metadata:
                # 6. Map DTO VideoMetadata → domain entity Video
                video = await self.video_repo.find_by_id(video_metadata.id)
                if not video:
                    video = Video(
                        id=None,
                        channel_id=channel.id,
                        youtube_video_id=video_metadata.videoId,
                        title=video_metadata.title,
                        url=video_metadata.url,
                        transcript=None,
                        transcript_fetched_at=None,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    saved_id = await self.video_repo.save(video)
                    video.id = saved_id

                # 7. If the video has no transcription yet, fetch it and update the record
                if not video.transcript_fetched_at:
                    transcript = await self.transcription_service.transcribe(video.id, language=['es'])
                    print(f"[PipelineService] Transcripción recibida (video {video.id}), {len(transcript)} caracteres")
                    video.transcript = transcript
                    video.transcript_fetched_at = datetime.utcnow()
                    # persist the updated video entity
                    await self.video_repo.update(video)

                # 8. Generate complete prompt
                prompt = f"{base_prompt.strip()}\n{video.transcript}"

                # 9. Generate raw texts for the video
                model="gpt-3.5-turbo"
                raw_tweets_text: List[str] = await self.openai_service.generate_tweets(
                    prompt=prompt,
                    max_sentences=max_tweets,
                    model=model)
                tweet_generation_ts = datetime.utcnow()

                print(f"[IngestionPipelineService] {len(tweets)} tweets generados para video {video.id}")
                
                # 10. Persist tweet generation metadata
                openai_req = OpenAIRequest(
                    prompt=prompt,
                    model=model,
                    # TO DO:
                    # temperature=self.openai_service.default_temperature,
                    # max_tokens=self.openai_service.default_max_tokens
                )
                generation = TweetGeneration(
                    id=None,
                    user_id=user_id,
                    video_id=video.id,
                    openai_request=openai_req,
                    generated_at = tweet_generation_ts
                )
                generation_id = await self.tweet_generation_repo.save(generation)                

                # 11. Map DTO raw_tweets_text (List[str]) → domain entity Tweet
                tweets: List[Tweet] = [
                    Tweet(
                        id=None,
                        user_id=user_id,
                        video_id=video.id,
                        generation_id=generation_id,
                        text=text,
                        index=index,
                        published=False,
                        created_at=tweet_generation_ts
                    )
                    for index, text in enumerate(raw_tweets_text, start=1)
                ]

                # 12. Batch save Tweet entities
                await self.tweet_repo.save_all(tweets)
