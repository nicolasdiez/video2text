# src/application/services/ingestion_pipeline_service.py

import asyncio
from datetime import datetime
from typing import List, Optional

# logging
import inspect
import logging

from domain.ports.inbound.ingestion_pipeline_port import IngestionPipelinePort
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort
from domain.ports.outbound.prompt_loader_port import PromptLoaderPort
from domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from domain.ports.outbound.mongodb.video_repository_port import VideoRepositoryPort
from domain.ports.outbound.video_source_port import VideoSourcePort, VideoMetadata
from domain.ports.outbound.mongodb.prompt_repository_port import PromptRepositoryPort
from domain.ports.outbound.openai_port import OpenAIPort
from domain.ports.outbound.mongodb.tweet_generation_repository_port import TweetGenerationRepositoryPort
from domain.entities.prompt import PromptContent
from domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort
from domain.ports.outbound.transcription_port import TranscriptionPort
from domain.ports.outbound.mongodb.user_scheduler_runtime_status_repository_port import UserSchedulerRuntimeStatusRepositoryPort

from domain.entities.video import Video
from domain.entities.channel import Channel
from domain.entities.prompt import Prompt
from domain.entities.tweet import Tweet
from domain.entities.tweet_generation import TweetGeneration, OpenAIRequest

from application.services.prompt_composer_service import PromptComposerService

# Specific logger for this module
logger = logging.getLogger(__name__)

class IngestionPipelineService(IngestionPipelinePort):
    """
    Orchestrates the ingestion pipeline:
      - Retrieve channels for a user
      - For each channel:
         a) Find new videos
         b) Transcribe missing videos
         c) Generate tweets for each video
         d) Persist generated tweets
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        prompt_loader: PromptLoaderPort,
        channel_repo: ChannelRepositoryPort,
        video_source: VideoSourcePort,
        video_repo: VideoRepositoryPort,
        transcription_client: TranscriptionPort,
        transcription_client_fallback: Optional[TranscriptionPort],
        transcription_client_fallback_2: Optional[TranscriptionPort],
        prompt_repo: PromptRepositoryPort,
        openai_client: OpenAIPort,
        tweet_generation_repo: TweetGenerationRepositoryPort,
        tweet_repo: TweetRepositoryPort,
        user_scheduler_runtime_repo: UserSchedulerRuntimeStatusRepositoryPort,
    ):
        self.user_repo = user_repo
        self.prompt_loader = prompt_loader
        self.channel_repo = channel_repo
        self.video_source = video_source
        self.video_repo = video_repo
        self.transcription_client = transcription_client
        self.transcription_client_fallback: Optional[TranscriptionPort] = transcription_client_fallback
        self.transcription_client_fallback_2: Optional[TranscriptionPort] = transcription_client_fallback_2
        self.prompt_repo = prompt_repo
        self.openai_client = openai_client
        self.tweet_generation_repo = tweet_generation_repo
        self.tweet_repo = tweet_repo
        self.prompt_composer = PromptComposerService()
        self.user_scheduler_runtime_repo = user_scheduler_runtime_repo

    async def run_for_user(self, user_id: str) -> None:
        try:
            # 0. Starting pipeline
            try:
                await self.user_scheduler_runtime_repo.mark_ingestion_started(user_id, datetime.utcnow())
                logger.info("Starting...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            except Exception:
                logger.exception("Failed to mark ingestion pipeline started", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                raise

            # 1. Validate that user actually exists on the repo
            user = await self.user_repo.find_by_id(user_id)
            if user is None:
                raise LookupError(f"User {user_id} not found")
            logger.info("User found (username: %s)", user.username, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 2. Fetch all channels the user is subscribed to
            channels: List[Channel] = await self.channel_repo.find_by_user_id(user_id)
            logger.info("%s channels retrieved from 'channels'", len(channels), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 3. Process each channel independently
            for index, channel in enumerate(channels, start=1):

                # 4. Fetch new videos for this channel
                logger.info("Channel %s/%s - Fetching max %s videos from channel %s", index, len(channels), channel.max_videos_to_fetch_from_channel, channel.title, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                videos_meta: List[VideoMetadata] = await self.video_source.fetch_new_videos(channel.youtube_channel_id, channel.max_videos_to_fetch_from_channel)
                
                # extract video IDs (limit if there are a lot)
                video_ids = [v.videoId for v in videos_meta]
                max_show = 20
                video_ids_to_show = video_ids if len(video_ids) <= max_show else video_ids[:max_show] + ["...(+%d)" % (len(video_ids) - max_show)]
                logger.info("%s videos retrieved from channel %s (%s) — youtube_videoIds: %s", len(videos_meta), channel.youtube_channel_id, channel.title, video_ids_to_show, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

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
                        logger.info("Video %s saved in 'videos' (title: '%s')", video.id, video.title, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                    # 7. If video has no transcription yet, fetch it and update the record
                    if not video.transcript_fetched_at:
                        transcript = None

                        # Try primary transcription client (YouTube Captions API -timedtext-)
                        try:
                            logger.info("Attempting primary transcription (YouTube Official Captions API -timedtext-) for video %s", video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},)
                            transcript = await self.transcription_client.transcribe(video.youtube_video_id, language=['en','es'])
                        except Exception as e:
                            logger.warning("Primary transcription client failed for video %s: %s", video.id, str(e), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},)

                        # If primary didn't return a usable transcript try first fallback, but only if client exists
                        if self.transcription_client_fallback:
                            if not transcript:
                                logger.info("Primary transcription unavailable, attempting 1st fallback (Youtube Official Data API) for video %s", video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},)
                                try:
                                    transcript = await self.transcription_client_fallback.transcribe(video.youtube_video_id, language=['en','es'])
                                except Exception as e:
                                    logger.warning("First fallback transcription client failed for video %s: %s", video.id, str(e), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},)

                        # If secondary didn't return a usable transcript (or client didn't even exist), try second fallback, but only if client exists
                        if self.transcription_client_fallback_2:                    
                            if not transcript:
                                logger.info("Seconday transcription unavailable, attempting 2nd fallback (Youtube Official Public Player API -ytInitialPlayerResponse-) for video %s", video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},)
                                try:
                                    transcript = await self.transcription_client_fallback_2.transcribe(video.youtube_video_id, language=['en','es'])
                                except Exception as e:
                                    logger.warning("Secondary fallback transcription client failed for video %s: %s", video.id, str(e), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},)

                        if not transcript:
                            logger.info("No transcription obtained for video %s after primary, seconday and tertiary fallback attempts; skipping transcript persistence", video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},)
                        else:
                            logger.info("Transcription received (%s chars) (video: %s)", len(transcript), video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},)
                            video.transcript = transcript
                            video.transcript_fetched_at = datetime.utcnow()
                            video.updated_at = datetime.utcnow()
                        
                            # persist the updated video entity
                            await self.video_repo.update(video)
                            logger.info("Transcription saved for video %s in 'videos'", video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                    # 8. If video has not been used for tweet generation yet, and video has a valid transcript, then generate tweets from the video and update the record
                    if (not video.tweets_generated) and video.transcript:

                        # 9. Retrieve Prompt entity for this user and channel
                        prompt = await self.prompt_repo.find_by_user_and_channel(user_id=user_id, channel_id=channel.id)
                        if not prompt:
                            logger.info("No prompt found for user %s and channel %s, skipping video %s", user_id, channel.id, video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                            continue

                        # 10. Load and prepare user and system messages for the prompt
                        # user message
                        prompt_user_message = self.prompt_composer.add_transcript(message=prompt.prompt_content.user_message, transcript=video.transcript)
                        logger.info("Prompt user message loaded (+ transcript), for video %s", video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                        # system message
                        prompt_system_message_with_objective = self.prompt_composer.add_objective(message=prompt.prompt_content.system_message, max_sentences=prompt.max_tweets_to_generate_per_video)
                        prompt_system_message = self.prompt_composer.add_output_language(message=prompt_system_message_with_objective, output_language=prompt.language_to_generate_tweets)
                        logger.info("Prompt system message loaded (+ objective + output language) for video %s", video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                    # 11. Generate raw texts for the video
                        model="gpt-4o-mini"
                        # raw_tweets_text: List[str] = ["tweet de prueba 1", "tweet de prueba 2"]     #debugging
                        raw_tweets_text: List[str] = await self.openai_client.generate_tweets(
                            prompt_user_message=prompt_user_message,
                            prompt_system_message=prompt_system_message,
                            model=model)
                        tweet_generation_ts = datetime.utcnow()
                        logger.info("%s tweets generated for video %s", len(raw_tweets_text), video.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                        # 12. Persist tweet generation metadata
                        openai_req = OpenAIRequest(
                            prompt_content=PromptContent(
                                system_message=prompt_system_message,
                                user_message=prompt_user_message
                            ),
                            model=model,
                            # temperature=self.openai_service.default_temperature,  # TODO
                            # max_tokens=self.openai_service.default_max_tokens     # TODO
                        )
                        tweet_generation = TweetGeneration(
                            id=None,
                            user_id=user_id,
                            video_id=video.id,
                            openai_request=openai_req,
                            generated_at = tweet_generation_ts
                        )
                        generation_id = await self.tweet_generation_repo.save(tweet_generation)
                        logger.info("Tweet generation %s saved in 'tweet_generations'", generation_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                        # 13. Map DTO raw_tweets_text List[str] → to domain entity Tweet
                        tweets: List[Tweet] = [
                            Tweet(
                                id=None,
                                user_id=user_id,
                                video_id=video.id,
                                generation_id=generation_id,
                                text=text,
                                index_in_generation=index,
                                published=False,
                                created_at=tweet_generation_ts,
                                updated_at=tweet_generation_ts
                            )
                            for index, text in enumerate(raw_tweets_text, start=1)
                        ]

                        # 14. Save Tweet entities (in batch)
                        await self.tweet_repo.save_all(tweets)
                        logger.info("%s tweets saved in 'tweets'", len(tweets), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})                    

                        # 15. Update video entity
                        video.tweets_generated = True
                        video.updated_at = datetime.utcnow()
                        await self.video_repo.update(video)
                    
                channel.last_polled_at = datetime.utcnow()
                channel.updated_at = datetime.utcnow()
                await self.channel_repo.update(channel)
                logger.info("Channel %s last_polled_at updated to %s", channel.youtube_channel_id, channel.last_polled_at, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 16-a. Finishing pipeline OK
            await self.user_scheduler_runtime_repo.mark_ingestion_finished(user_id, datetime.utcnow(), success=True)
            await self.user_scheduler_runtime_repo.reset_ingestion_failures(user_id)
            logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        
        # 16-b. Finishing pipeline KO
        except Exception:
            # increment failure counter and mark as finished with failure
            try:
                await self.user_scheduler_runtime_repo.increment_ingestion_failures(user_id, by=1)
                await self.user_scheduler_runtime_repo.mark_ingestion_finished(user_id, datetime.utcnow(), success=False)
            except Exception:
                logger.exception("Failed updating user runtime status after ingestion pipeline error", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            logger.exception("Ingestion pipeline failed", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise

