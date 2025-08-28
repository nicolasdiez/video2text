# src/application/services/ingestion_pipeline_service.py

import asyncio
from datetime import datetime
from typing import List
import inspect  # para trazas logging con print

from domain.ports.inbound.ingestion_pipeline_port import IngestionPipelinePort
from domain.ports.outbound.prompt_loader_port import PromptLoaderPort
from domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from domain.ports.outbound.mongodb.video_repository_port import VideoRepositoryPort
from domain.ports.outbound.video_source_port import VideoSourcePort, VideoMetadata
from domain.ports.outbound.mongodb.tweet_generation_repository_port import TweetGenerationRepositoryPort
from domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort
from domain.ports.outbound.transcription_port import TranscriptionPort
from domain.ports.outbound.openai_port import OpenAIPort

from domain.entities.video import Video
from domain.entities.channel import Channel
from domain.entities.tweet import Tweet
from domain.entities.tweet_generation import TweetGeneration, OpenAIRequest


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
        transcription_client: TranscriptionPort,
        openai_client: OpenAIPort,
        tweet_generation_repo: TweetGenerationRepositoryPort,
        tweet_repo: TweetRepositoryPort,
    ):
        self.prompt_loader = prompt_loader
        self.channel_repo = channel_repo
        self.video_source = video_source
        self.video_repo = video_repo
        self.transcription_client = transcription_client
        self.openai_client = openai_client
        self.tweet_generation_repo = tweet_generation_repo
        self.tweet_repo = tweet_repo

    async def run_for_user(self, user_id: str, user_id: str, prompt_file: str, max_videos: int = 2, max_tweets: int = 3) -> None:
        
        # 0. Validate that user_id actually exists on the system repo


        # 1. Load prompt base from file (without blocking thread)
        base_prompt = await self.prompt_loader.load_prompt(prompt_file)
        print(f"[IngestionPipelineService] Base prompt loaded (base prompt file: {prompt_file}")

        # 2. Fetch all channels the user is subscribed to
        channels: List[Channel] = await self.channel_repo.find_by_user_id(user_id)
        print(f"[IngestionPipelineService] {len(channels)} channels retrieved for user {user_id} from collection 'channels'")

        # 3. Process each channel independently
        for channel in channels:

            # 4. Fetch new videos for this channel
            videos_meta: List[VideoMetadata] = await self.video_source.fetch_new_videos(channel.youtube_channel_id, max_videos)
            print(f"[IngestionPipelineService] {len(videos_meta)} videos retrieved from channel {channel.title}")

            # 5. Process each video independently
            for video_meta in videos_meta:

                # 6. Map DTO VideoMetadata → to domain entity Video, and persist
                video = await self.video_repo.find_by_youtube_video_id_and_user_id(video_meta.videoId, user_id=user_id)
                if not video:
                    video = Video(
                        id=None,
                        user_id=user_id,
                        channel_id=channel.id,
                        youtube_video_id=video_meta.videoId,
                        title=video_meta.title,
                        url=video_meta.url,
                        transcript=None,
                        transcript_fetched_at=None,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    saved_id = await self.video_repo.save(video)
                    video.id = saved_id
                    print(f"[IngestionPipelineService] Video {video.id} saved in collection 'videos'")

                # 7. If video has no transcription yet, fetch it and update the record
                if not video.transcript_fetched_at:
                    transcript = await self.transcription_client.transcribe(video.youtube_video_id, language=['es'])
                    print(f"[PipelineService] Transcription received (video {video.id}, youtube_video_id {video.youtube_video_id}) with {len(transcript)} characters")
                    video.transcript = transcript
                    video.transcript_fetched_at = datetime.utcnow()
                    video.updated_at = datetime.utcnow()
                    # persist the updated video entity
                    await self.video_repo.update(video)
                    print(f"[IngestionPipelineService] Transcription saved for video {video.id} in collection 'videos'")

                # 8. If video has not been used for tweet generation yet, then generate tweets and update the record
                if not video.tweets_generated:

                    # 9. Generate complete prompt
                    prompt = f"{base_prompt.strip()}\n{video.transcript}"
                    print(f"[IngestionPipelineService] Prompt generated (base prompt + transcript)")

                    # 10. Generate raw texts for the video
                    model="gpt-3.5-turbo"
                    raw_tweets_text: List[str] = ["tweet de prueba 1", "tweet de prueba 2"]     #debugging
                    #raw_tweets_text: List[str] = await self.openai_client.generate_tweets(
                    #    prompt=prompt,
                    #    max_sentences=max_tweets,
                    #    model=model)
                    tweet_generation_ts = datetime.utcnow()
                    print(f"[IngestionPipelineService] {len(raw_tweets_text)} tweets generated for video {video.id}")
                    
                    # 11. Persist tweet generation metadata
                    openai_req = OpenAIRequest(
                        prompt=prompt,
                        model=model,
                        # TO DO:
                        # temperature=self.openai_service.default_temperature,
                        # max_tokens=self.openai_service.default_max_tokens
                    )
                    tweet_generation = TweetGeneration(
                        id=None,
                        user_id=user_id,
                        video_id=video.id,
                        openai_request=openai_req,
                        generated_at = tweet_generation_ts
                    )
                    generation_id = await self.tweet_generation_repo.save(tweet_generation)
                    print(f"[IngestionPipelineService] Tweet generation {generation_id} saved in collection 'tweet_generations'")

                    # 12. Map DTO raw_tweets_text List[str] → to domain entity Tweet
                    tweets: List[Tweet] = [
                        Tweet(
                            id=None,
                            user_id=user_id,
                            video_id=video.id,
                            generation_id=generation_id,
                            text=text,
                            index_in_generation=index,
                            published=False,
                            created_at=tweet_generation_ts
                        )
                        for index, text in enumerate(raw_tweets_text, start=1)
                    ]

                    # 13. Save Tweet entities (in batch)
                    await self.tweet_repo.save_all(tweets)
                    print(f"[IngestionPipelineService] {len(tweets)} tweets saved in collection 'tweets'")

                    # 14. Update video entity
                    video.tweets_generated = True
                    video.updated_at = datetime.utcnow()
                    await self.video_repo.update(video)

        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")

