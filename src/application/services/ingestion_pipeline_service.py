# src/application/services/ingestion_pipeline_service.py

import asyncio
from datetime import datetime
from typing import List

from src.domain.ports.outbound.prompt_loader_port import PromptLoaderPort
from src.domain.ports.inbound.ingestion_pipeline_port import IngestionPipelinePort
from src.domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from src.domain.ports.outbound.mongodb.video_repository_port import VideoRepositoryPort
from src.domain.ports.outbound.video_source_port import VideoSourcePort
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
            videos: List[Video] = await self.video_source.fetch_new_videos(channel.youtube_channel_id, max_videos)

            # 5. Process each video independently
            for video in videos:
                # 6. Save video in MongoDB (if doesnt exist yet)
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
                    transcript = await self.transcription_service.transcribe(video.videoId, language=['es'])
                    print(f"[PipelineService] Transcripción recibida (video {video.videoId}), {len(transcript)} caracteres")
                    video.transcript = transcript
                    video.transcript_fetched_at = datetime.utcnow()
                    # persist the updated video entity
                    await self.video_repo.update_video(video)

                # 8. Generate complete prompt
                prompt = f"{base_prompt.strip()}\n{video.transcript}"

                # 9. Generate tweet texts for the video
                model="gpt-3.5-turbo"
                tweets: List[Tweet] = await self.openai_service.generate_tweets(
                    prompt=prompt,
                    max_sentences=max_tweets,
                    model=model)
                tweets_generation_ts = datetime.utcnow()

                print(f"[IngestionPipelineService] {len(tweets)} tweets generados para video {video.id}")
                
                # 9.1 Persist tweet generation metadata
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
                    generated_at = tweets_generation_ts
                )
                generation_id = await self.tweet_generation_repo.save(generation)                

                # 10. Build tweet records for batch saving
                tweet_records = [
                    {
                        "user_id": user_id,
                        "video_id": video.id,
                        "text": tweet.text,
                        "createdat": tweets_generation_ts,
                    }
                    for tweet in tweets
                ]

                # 11. Save all generated tweets in MongoDB
                await self.tweet_repo.save_all(tweet_records)
