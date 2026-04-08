# /src/main_2.py


import os
import asyncio
import sys

import config

# set twitter credentials for user Nico (TEMPORATY: UNTIL API AND FRONTEND READY) 
from domain.entities.user import UserTwitterCredentials

# logger
import logging
import inspect
from infrastructure.logging.request_context import set_user_id

# WebServer
import uvicorn      # ASGI ligero y de alto rendimiento (Asynchronous Server Gateway Interface server)

# Fast API framework
from fastapi import FastAPI

# Routes
from api.routes.auth_routes import router as auth_router
from api.routes.twitter_oauth2_routes import router as twitter_oauth2_router

# Mongo DB
from infrastructure.mongodb import db

# APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

# Controllers
# import pipeline_controller to later inject the GenerationPipelineService/PublishingPipelineService instances with all the created adapters into pipeline_controller.generation_pipeline_service/publishing_pipeline_service
import adapters.inbound.http.pipeline_controller as pipeline_controller 

# Generation pipeline
from application.services.generation_pipeline_service import GenerationPipelineService
from adapters.outbound.mongodb.user_repository import MongoUserRepository
from adapters.outbound.file_prompt_loader import FilePromptLoader
from adapters.outbound.mongodb.channel_repository import MongoChannelRepository
from adapters.outbound.youtube_video_client import YouTubeVideoClient
from adapters.outbound.mongodb.video_repository import MongoVideoRepository
from adapters.outbound.transcription_client_captions_api import YouTubeTranscriptionClientOfficialCaptionsAPI
from adapters.outbound.transcription_client_data_api import YouTubeTranscriptionClientOfficialDataAPI
from adapters.outbound.transcription_client_public_player_api_ASR import YouTubeTranscriptionClientOfficialPublicPlayerAPI_ASR
from adapters.outbound.transcription_client_android_player_api_ASR import YouTubeTranscriptionClientAndroidPlayerAPI_ASR
from adapters.outbound.mongodb.user_prompt_repository import MongoUserPromptRepository
from domain.services.prompt_resolver_service import PromptResolverService
from adapters.outbound.llm_openai_client import LLMOpenAIClient
from adapters.outbound.llm_gemini_client import LLMGeminiClient
from adapters.outbound.mongodb.tweet_generation_repository import MongoTweetGenerationRepository
from adapters.outbound.mongodb.tweet_repository import MongoTweetRepository
from adapters.outbound.mongodb.user_scheduler_runtime_status_repository import MongoUserSchedulerRuntimeStatusRepository

# Publishing pipeline
from application.services.publishing_pipeline_service import PublishingPipelineService
from adapters.outbound.twitter_publication_client_oauth1 import TwitterPublicationClientOAuth1
from adapters.outbound.twitter_publication_client_oauth2 import TwitterPublicationClientOAuth2
from infrastructure.auth.twitter_oauth2_service import TwitterOAuth2Service

# Repository adapters (for wiring with DB instance)
from adapters.outbound.mongodb.app_config_repository import MongoAppConfigRepository
from adapters.outbound.mongodb.master_prompt_repository import MongoMasterPromptRepository

# Application Services ()
from application.services.channel_service import ChannelService
from domain.services.prompt_composer_service import PromptComposerService
from domain.services.tweet_outpout_guardrail_service import TweetOutputGuardrailService

# factory to get a youtube_client resource for consuming Youtube Data API (to retrieve video transcriptions) 
from infrastructure.auth.youtube_credentials import get_youtube_client

# specific logger for this module
logger = logging.getLogger(__name__)

# create a youtube_client resource to inject as dependency into YouTubeTranscriptionClientOfficialDataAPI
try:
    youtube_client = get_youtube_client(client_id=config.YOUTUBE_OAUTH_CLIENT_ID, client_secret=config.YOUTUBE_OAUTH_CLIENT_SECRET, refresh_token=config.YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN)
except RuntimeError as exc:
    logger.error("YouTube client could not be constructed (to use as input for YouTubeTranscriptionClientOfficialDataAPI): %s", str(exc), extra={"mod": __name__})
    youtube_client = None

# --- Repo adapters & service instantiation ---

# Generation, Publishing, Stats, Embeddings pipelines 
user_repo                                   = MongoUserRepository(database=db)
prompt_loader                               = FilePromptLoader(prompts_dir="prompts")
channel_repo                                = MongoChannelRepository(database=db)
video_source                                = YouTubeVideoClient(api_key=config.YOUTUBE_API_KEY)
video_repo                                  = MongoVideoRepository(database=db)
transcription_client_captions_api           = YouTubeTranscriptionClientOfficialCaptionsAPI(default_language="es")
transcription_client_data_api               = YouTubeTranscriptionClientOfficialDataAPI(youtube_client=youtube_client) if youtube_client else None
transcription_client_public_player_api_asr  = YouTubeTranscriptionClientOfficialPublicPlayerAPI_ASR(model_name="tiny", device="cpu")
transcription_client_android_player_api_asr = YouTubeTranscriptionClientAndroidPlayerAPI_ASR(model_name="small", device="cpu")
user_prompt_repo                            = MongoUserPromptRepository(database=db)
prompt_resolver_service                     = PromptResolverService()
llm_openai_client                           = LLMOpenAIClient(api_key=config.OPENAI_API_KEY)
llm_gemini_client                           = LLMGeminiClient(api_key=config.GEMINI_API_KEY)
tweet_output_guardrail_service              = TweetOutputGuardrailService()
tweet_generation_repo                       = MongoTweetGenerationRepository(db=db)
tweet_repo                                  = MongoTweetRepository(database=db)
user_scheduler_runtime_repo                 = MongoUserSchedulerRuntimeStatusRepository(database=db)
master_prompt_repo                          = MongoMasterPromptRepository(database=db) 
channel_service                             = ChannelService(channel_repo, user_prompt_repo, master_prompt_repo, prompt_resolver_service)
prompt_composer_service                     = PromptComposerService()
twitter_publication_client_oauth1           = TwitterPublicationClientOAuth1(oauth1_api_key=config.X_OAUTH1_API_KEY, oauth1_api_secret=config.X_OAUTH1_API_SECRET)
oauth2_service                              = TwitterOAuth2Service(user_repo=user_repo)
twitter_publication_client_oauth2           = TwitterPublicationClientOAuth2(user_repo=user_repo, oauth2_service=oauth2_service)

# Create an instance of GenerationPipelineService with the concrete implementations of the ports (i.e., inject Adapters into the Ports of GenerationPipelineService)
generation_pipeline_service_instance = GenerationPipelineService(
    user_repo                       = user_repo,
    prompt_loader                   = prompt_loader,
    channel_repo                    = channel_repo,
    video_source                    = video_source,
    video_repo                      = video_repo,
    transcription_client            = transcription_client_captions_api,
    transcription_client_fallback   = transcription_client_public_player_api_asr,
    transcription_client_fallback_2 = transcription_client_data_api,
    tweet_generation_client         = llm_gemini_client,
    tweet_output_guardrail_service  = tweet_output_guardrail_service,
    tweet_generation_repo           = tweet_generation_repo,
    tweet_repo                      = tweet_repo,
    user_scheduler_runtime_repo     = user_scheduler_runtime_repo,
    channel_service                 = channel_service,
    prompt_composer_service         = prompt_composer_service
)

# Inject the instance of GenerationPipelineService (with all the Adapters) into the pipeline controller 
pipeline_controller.generation_pipeline_service = generation_pipeline_service_instance

# Create an instance of PublishingPipelineService with the concrete implementations of the ports (i.e., inject Adapters into the Ports of PublishingPipelineService)
publishing_pipeline_service_instance = PublishingPipelineService(
    user_repo                       = user_repo,
    tweet_repo                      = tweet_repo,
    twitter_publication_client      = twitter_publication_client_oauth2,
    user_scheduler_runtime_repo     = user_scheduler_runtime_repo,
)

# Inject the instance of PublishingPipelineService (with all the Adapters) into the pipeline controller 
pipeline_controller.publishing_pipeline_service = publishing_pipeline_service_instance

# --- AppConfig adapter ---
app_config_repo = MongoAppConfigRepository(database=db)

# APScheduler instance
scheduler = AsyncIOScheduler()

# Lifespan context manager (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):

    async def generation_job():
        # 1. Get pipeline execution frequency at app config level
        app_config = await app_config_repo.get_config()
        # app_frequency_minutes = float(app_config.scheduler_config.generation_pipeline_frequency_minutes)
        default_user_frequency_minutes = 1440

        users = await user_repo.find_all()
        now = datetime.utcnow()

        for user in users:
            try:
                # Set user_id for this iteration to make it available for logging
                set_user_id(str(user.id))

                # 2. Check if pipeline is enabled (user config takes priority, then app config)
                user_scheduler_config = getattr(user, "scheduler_config", None)
                if user_scheduler_config and hasattr(user_scheduler_config, "is_generation_pipeline_enabled") and user_scheduler_config.is_generation_pipeline_enabled is False:
                    logger.info("Skipping Generation pipeline (disabled by user config)", extra={"job": "generation"})
                    continue

                app_scheduler_config = app_config.scheduler_config
                if not app_scheduler_config or not hasattr(app_scheduler_config, "is_generation_pipeline_enabled") or app_scheduler_config.is_generation_pipeline_enabled is False:
                    logger.info("Skipping Generation pipeline (disabled by app_config or app_config missing)", extra={"job": "generation"})
                    continue

                # 3. Determine effective pipeline frequency (user config takes priority, then app config)
                user_frequency_minutes = getattr(user.scheduler_config, "generation_pipeline_frequency_minutes", None)
                effective_frequency_minutes = float(user_frequency_minutes) if user_frequency_minutes is not None else default_user_frequency_minutes #app_frequency_minutes

                # 4. Retrieve runtime status for this user
                user_runtime_status = await user_scheduler_runtime_repo.get_by_user_id(user.id)
                generation_last_started_at = getattr(user_runtime_status, "last_generation_pipeline_started_at", None) if user_runtime_status else None
                is_running = getattr(user_runtime_status, "is_generation_pipeline_running", False) if user_runtime_status else False

                # 5. Determine if pipeline should run
                elapsed_minutes = (now - generation_last_started_at).total_seconds() / 60.0 if generation_last_started_at else None
                # normal condition: enough time has passed AND pipeline is not running
                enough_time_passed = elapsed_minutes is not None and elapsed_minutes > effective_frequency_minutes and not is_running
                # protection condition: pipeline stuck (elapsed > 1x frequency)
                stuck_protection = elapsed_minutes is not None and elapsed_minutes > (effective_frequency_minutes * 1)
                # first run condition: no previous execution recorded 
                first_run = elapsed_minutes is None
                
                should_run = first_run or enough_time_passed or stuck_protection
                
                # normalizo valor de elapsed_minutes para el caso de que sea None no falle el logger
                elapsed_minutes = f"{elapsed_minutes:.2f}" if elapsed_minutes is not None else "N/A"
                decision = "Yes" if should_run else "No"
                logger.info("Generation pipeline: Configured freq %s mins, Last start %s mins ago", effective_frequency_minutes, elapsed_minutes, extra={"job": "generation"})
                logger.info("Generation pipeline should run now? %s", decision, extra={"job": "generation"})

                if not should_run:
                    logger.info("Skipping Generation pipeline (already running or within freq)", extra={"job": "generation"})
                    continue

                # 6. Run pipeline
                logger.info("Generation pipeline starting", extra={"job": "generation"})
                set_user_id(user.id) # se aplica a todos los logs del job
                await generation_pipeline_service_instance.run_for_user(user_id=user.id)
                logger.info("Generation pipeline finished", extra={"job": "generation"})
                
                # 7. Update the time for next pipeline initiation using the effective frequency (user or app)
                finish_time = datetime.utcnow()
                next_start = finish_time + timedelta(minutes=effective_frequency_minutes)
                await user_scheduler_runtime_repo.update_by_user_id(user.id, {"nextScheduledGenerationPipelineStartingAt": next_start})
                logger.info("Next user's scheduled Generation pipeline starting at: %s", next_start.isoformat(), extra={"job": "generation"})
            
            except Exception as e:
                logger.error("Generation pipeline failed: %s", str(e), extra={"job": "generation"})
    
        # 8. Refresh app config from repository and reschedule job if frequency changed
        # get current app job/pipeline frequency
        job = scheduler.get_job("generation_job")
        current_generation_frequency_minutes = job.trigger.interval.total_seconds() / 60
        logger.debug("Checking if Generation pipeline app config frequency has changed (current freq: %s mins)", current_generation_frequency_minutes, extra={"job": "generation"})
        # get app configuration frequency from repo
        new_app_config = await app_config_repo.get_config()
        new_generation_frequency_minutes = new_app_config.scheduler_config.generation_pipeline_frequency_minutes
        # if there is a new app pipeline config then reschedule job
        if float(new_generation_frequency_minutes) != float(current_generation_frequency_minutes):
            try:
                scheduler.reschedule_job("generation_job", trigger="interval", minutes=new_generation_frequency_minutes)
                logger.info("Rescheduled Generation pipeline app config frequency to %s minutes", new_generation_frequency_minutes, extra={"job": "generation"})
            except Exception as ex:
                logger.warning("Failed to reschedule Generation pipeline app config frequency: %s", str(ex), extra={"job": "generation"})
        else:
            logger.debug("Generation pipeline app config frequency has not changed (current freq: %s mins)", current_generation_frequency_minutes, extra={"job": "generation"})

    async def publishing_job():
        # 1. Get pipeline execution frequency at app config level
        app_config = await app_config_repo.get_config()
        # app_frequency_minutes = float(app_config.scheduler_config.publishing_pipeline_frequency_minutes)
        default_user_frequency_minutes = 1440

        users = await user_repo.find_all()
        now = datetime.utcnow()

        for user in users:
            try:
                # Set user_id for this iteration to make it available for logging
                set_user_id(str(user.id))
                
                # 2. Check if pipeline is enabled (user config takes priority, then app config)
                user_scheduler_config = getattr(user, "scheduler_config", None)
                if user_scheduler_config and hasattr(user_scheduler_config, "is_publishing_pipeline_enabled") and user_scheduler_config.is_publishing_pipeline_enabled is False:
                    logger.info("Skipping Publishing pipeline (disabled by user config)", extra={"job": "publishing"})
                    continue

                app_scheduler_config = app_config.scheduler_config
                if not app_scheduler_config or not hasattr(app_scheduler_config, "is_publishing_pipeline_enabled") or app_scheduler_config.is_publishing_pipeline_enabled is False:
                    logger.info("Skipping Publishing pipeline (disabled by app_config or app_config missing)", extra={"job": "publishing"})
                    continue

                # 3. Determine effective pipeline frequency (user config takes priority, then app config)
                user_frequency_minutes = getattr(user.scheduler_config, "publishing_pipeline_frequency_minutes", None)
                effective_frequency_minutes = float(user_frequency_minutes) if user_frequency_minutes is not None else default_user_frequency_minutes #app_frequency_minutes

                # 4. Retrieve runtime status for this user
                user_runtime_status = await user_scheduler_runtime_repo.get_by_user_id(user.id)
                publishing_last_started_at = getattr(user_runtime_status, "last_publishing_pipeline_started_at", None) if user_runtime_status else None
                is_running = getattr(user_runtime_status, "is_publishing_pipeline_running", False) if user_runtime_status else False

                # 5. Determine if pipeline should run
                elapsed_minutes = (now - publishing_last_started_at).total_seconds() / 60.0 if publishing_last_started_at else None
                # normal condition: enough time has passed AND pipeline is not running
                enough_time_passed = elapsed_minutes is not None and elapsed_minutes > effective_frequency_minutes and not is_running
                # protection condition: pipeline stuck (elapsed > 1x frequency)
                stuck_protection = elapsed_minutes is not None and elapsed_minutes > (effective_frequency_minutes * 1)
                # first run condition: no previous execution recorded 
                first_run = elapsed_minutes is None

                should_run = first_run or enough_time_passed or stuck_protection

                # normalizo valor de elapsed_minutes para el caso de que sea None no falle el logger
                elapsed_minutes = f"{elapsed_minutes:.2f}" if elapsed_minutes is not None else "N/A"
                decision = "Yes" if should_run else "No"
                logger.info("Publishing pipeline: Configured freq %s mins, Last start %s mins ago", effective_frequency_minutes, elapsed_minutes, extra={"job": "publishing"})
                logger.info("Publishing pipeline should run now? %s", decision, extra={"job": "publishing"})
                
                if not should_run:
                    logger.info("Skipping Publishing pipeline (already running or within freq)", extra={"job": "publishing"})
                    continue

                # 6. Run pipeline
                logger.info("Publishing pipeline starting", extra={"job": "publishing"})
                set_user_id(user.id) # se aplica a todos los logs del job
                await publishing_pipeline_service_instance.run_for_user(user_id=user.id)
                logger.info("Publishing pipeline finished", extra={"job": "publishing"})

                # 7. Update the time for next pipeline initiation using the effective frequency (user or app)
                finish_time = datetime.utcnow()
                next_start = finish_time + timedelta(minutes=effective_frequency_minutes)
                await user_scheduler_runtime_repo.update_by_user_id(user.id, {"nextScheduledPublishingPipelineStartingAt": next_start})
                logger.info("Next user's scheduled Publishing pipeline starting at: %s", next_start.isoformat(), extra={"job": "publishing"})

            except Exception as e:
                logger.error("Publishing pipeline failed: %s", str(e), extra={"job": "publishing"})

        # 8. Refresh app config from repository and reschedule job if frequency changed
        # get current app job/pipeline frequency
        job = scheduler.get_job("publishing_job")
        current_publishing_frequency_minutes = job.trigger.interval.total_seconds() / 60
        logger.debug("Checking if Publishing pipeline app config frequency has changed (current freq: %s mins)", current_publishing_frequency_minutes, extra={"job": "publishing"})
        # get app configuration frequency from repo
        new_app_config = await app_config_repo.get_config()
        new_publishing_frequency_minutes = new_app_config.scheduler_config.publishing_pipeline_frequency_minutes
        # if there is a new app pipeline config then reschedule job
        if float(new_publishing_frequency_minutes) != float(current_publishing_frequency_minutes):
            try:
                scheduler.reschedule_job("publishing_job", trigger="interval", minutes=new_publishing_frequency_minutes)
                logger.info("Rescheduled Publishing pipeline app config frequency to %s minutes", new_publishing_frequency_minutes, extra={"job": "publishing"})
            except Exception as ex:
                logger.warning("Failed to reschedule Publishing pipeline app config frequency: %s", str(ex), extra={"job": "publishing"})
        else:   
            logger.debug("Publishing pipeline app config frequency has not changed (current freq: %s mins)", current_publishing_frequency_minutes, extra={"job": "publishing"})

    # load appConfig from repo
    app_config = await app_config_repo.get_config()
    generation_pipeline_frequency_minutes = app_config.scheduler_config.generation_pipeline_frequency_minutes
    publishing_pipeline_frequency_minutes = app_config.scheduler_config.publishing_pipeline_frequency_minutes
    stats_pipeline_frequency_minutes = app_config.scheduler_config.stats_pipeline_frequency_minutes
    embeddings_pipeline_frequency_minutes = app_config.scheduler_config.embeddings_pipeline_frequency_minutes
    logger.info("Loaded DB App config: generation_freq=%s min, publishing_freq=%s min, stats_freq=%s min, embeddings_freq=%s min", generation_pipeline_frequency_minutes, publishing_pipeline_frequency_minutes, stats_pipeline_frequency_minutes, embeddings_pipeline_frequency_minutes)
    
    # setup job execution frequency
    scheduler.add_job(generation_job, "interval", minutes=generation_pipeline_frequency_minutes, id="generation_job")
    scheduler.add_job(publishing_job, "interval", minutes=publishing_pipeline_frequency_minutes, id="publishing_job")
    # scheduler.add_job(stats_job, "interval", minutes=stats_pipeline_frequency_minutes, id="stats_job")
    # scheduler.add_job(embeddings_job, "interval", minutes=embeddings_pipeline_frequency_minutes, id="embeddings_job")

    # start scheduler.
    scheduler.start()
    logger.info("APScheduler started")

    yield  # Application runs here
    logger.info("Lifespan shutdown: scheduler left running intentionally")
    
    # shutdown scheduler
    scheduler.shutdown()
    logger.info("APScheduler stopped")


# Start FastAPI application
app = FastAPI(
    title       = "Pipelines: | Generation | Publishing | Stats | Embeddings |",
    version     = "1.0.0",
    description = "",
    lifespan    = lifespan   # start the scheduler
)
logger.info("FastApi App started")

# Register routes
app.include_router(pipeline_controller.router)
app.include_router(auth_router)
app.include_router(twitter_oauth2_router)


if __name__ == "__main__":
    # wrap ASGI server start-up under if __name__ == "__main__":, so the run doesnt double-execute
    uvicorn.run("main:app", host="0.0.0.0", port=8081)       # En PRO --> reload=False