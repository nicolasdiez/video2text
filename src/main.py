# /src/main.py

# TODO:
# - endpoints de consumo desde front para CRUD entities: users, channels, prompts, app_config, prompts_master.
# - modify transcription_client.py from using deprecated get_transcript() to use fetch()
# - create a new collection {prompts_master} to store master prompts of the application, not dependent on userId or channelId.
# - refactor ingestion_pipeline_service constructor to use a Composite pattern for the transcription clients/adapters (crear un CompositeTranscriptionClient que reciba [primary, fallback1, fallback2...] y pruebe cada uno en orden hasta obtener resultado válido. Mantiene Inversion of Control y SRP.)
# - in GCP VM, convert./run.sh into a persistent service, so it runs in background all time, not foreground execution needed anymore

import os
import asyncio
import sys

# import config
import config

# set twitter credentials for user Nico (TEMPORATY: UNTIL API AND FRONTEND READY) 
from domain.entities.user import UserTwitterCredentials

# logger
import logging
import inspect

# WebServer
import uvicorn      # ASGI ligero y de alto rendimiento (Asynchronous Server Gateway Interface server)

# Fast API framework
from fastapi import FastAPI

# Mongo DB
from infrastructure.mongodb import db

# APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

# Controllers
# import pipeline_controller to later inject the IngestionPipelineService/PublishingPipelineService instances with all the created adapters into pipeline_controller.ingestion_pipeline_service/publishing_pipeline_service
import adapters.inbound.http.pipeline_controller as pipeline_controller 

# Ingestion pipeline
from application.services.ingestion_pipeline_service import IngestionPipelineService
from adapters.outbound.mongodb.user_repository import MongoUserRepository
from adapters.outbound.file_prompt_loader import FilePromptLoader
from adapters.outbound.mongodb.channel_repository import MongoChannelRepository
from adapters.outbound.youtube_video_client import YouTubeVideoClient
from adapters.outbound.mongodb.video_repository import MongoVideoRepository
from adapters.outbound.transcription_client import YouTubeTranscriptionClientOfficialCaptionsAPI
from adapters.outbound.transcription_client_official import YouTubeTranscriptionClientOfficialDataAPI
from adapters.outbound.transcription_client_ASR import YouTubeTranscriptionClientOfficialPublicPlayerAPI_ASR
from adapters.outbound.mongodb.prompt_repository import MongoPromptRepository
from adapters.outbound.openai_client import OpenAIClient
from adapters.outbound.mongodb.tweet_generation_repository import MongoTweetGenerationRepository
from adapters.outbound.mongodb.tweet_repository import MongoTweetRepository
from adapters.outbound.mongodb.user_scheduler_runtime_status_repository import MongoUserSchedulerRuntimeStatusRepository

# Publishing pipeline
from application.services.publishing_pipeline_service import PublishingPipelineService
from adapters.outbound.twitter_client import TwitterClient

# appConfig adapter
from adapters.outbound.mongodb.app_config_repository import MongoAppConfigRepository

# factory to get a youtube_client resource for consuming Youtube Data API to retrieve video transcriptions 
from infrastructure.auth.youtube_credentials import get_youtube_client

# specific logger for this module
logger = logging.getLogger(__name__)


# create a youtube_client resource to inject as dependency into YouTubeTranscriptionClientOfficialDataAPI
try:
    youtube_client = get_youtube_client(client_id=config.YOUTUBE_OAUTH_CLIENT_ID, client_secret=config.YOUTUBE_OAUTH_CLIENT_SECRET, refresh_token=config.YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN)
except RuntimeError as exc:
    logger.error("YouTube client could not be constructed: %s", str(exc), extra={"mod": __name__})
    # if instanciation fails, then rely on the transcription fallback service
    youtube_client = None

# --- Ingestion Pipeline adapters & service instantiation ---
user_repo                       = MongoUserRepository(database=db)
prompt_loader                   = FilePromptLoader(prompts_dir="prompts")
channel_repo                    = MongoChannelRepository(database=db)
video_source                    = YouTubeVideoClient(api_key=config.YOUTUBE_API_KEY)
video_repo                      = MongoVideoRepository(database=db)
transcription_client            = YouTubeTranscriptionClientOfficialCaptionsAPI(default_language="es")
transcription_client_fallback   = YouTubeTranscriptionClientOfficialDataAPI(youtube_client=youtube_client) if youtube_client else None
transcription_client_fallback_2 = YouTubeTranscriptionClientOfficialPublicPlayerAPI_ASR(model_name="tiny", device="cpu")
prompt_repo                     = MongoPromptRepository(database=db)
openai_client                   = OpenAIClient(api_key=config.OPENAI_API_KEY)
tweet_generation_repo           = MongoTweetGenerationRepository(db=db)
tweet_repo                      = MongoTweetRepository(database=db)
user_scheduler_runtime_repo     = MongoUserSchedulerRuntimeStatusRepository(database=db)

# if no official Youtube API transcription client, warn in log
if transcription_client is None:
    logger.warning("YouTube official transcription client not configured; using ASR fallback only", extra={"mod": __name__})

# Create an instance of IngestionPipelineService with the concrete implementations of the ports (i.e., inject Adapters into the Ports of IngestionPipelineService)
ingestion_pipeline_service_instance = IngestionPipelineService(
    user_repo                       = user_repo,
    prompt_loader                   = prompt_loader,
    channel_repo                    = channel_repo,
    video_source                    = video_source,
    video_repo                      = video_repo,
    transcription_client            = transcription_client,
    transcription_client_fallback   = transcription_client_fallback,
    transcription_client_fallback_2 = transcription_client_fallback,
    prompt_repo                     = prompt_repo,
    openai_client                   = openai_client,
    tweet_generation_repo           = tweet_generation_repo,
    tweet_repo                      = tweet_repo,
    user_scheduler_runtime_repo     = user_scheduler_runtime_repo,
)

# Inject the instance of IngestionPipelineService (with all the Adapters) into the pipeline controller 
pipeline_controller.ingestion_pipeline_service = ingestion_pipeline_service_instance


# --- Publishing adapters & service instantiation ---
twitter_client = TwitterClient(
    oauth1_api_key      = config.X_OAUTH1_API_KEY,
    oauth1_api_secret   = config.X_OAUTH1_API_SECRET
)

# Create an instance of PublishingPipelineService with the concrete implementations of the ports (i.e., inject Adapters into the Ports of PublishingPipelineService)
publishing_pipeline_service_instance = PublishingPipelineService(
    user_repo                       = user_repo,
    tweet_repo                      = tweet_repo,
    twitter_client                  = twitter_client,
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

    # ===== START TEMPORARY BLOCK =====
    # =================================================================================
    # Escribir en el document del USER_ID las credentials de usuario que temporalmente están en .env
    # TODO: remove this block when frontend/endpoints for user credential management is ready
    USER_ID = "000000000000000000000001" # Nico
    bootstrap_user_id = USER_ID
    # Retrieve USER's X credentials from env (either .env file or Github Environment secrets) and save them encrypted to mongoDB user collection
    creds = UserTwitterCredentials(
        # credentials related to THE USER of the application:
        oauth1_access_token=config.X_OAUTH1_ACCESS_TOKEN,
        oauth1_access_token_secret=config.X_OAUTH1_ACCESS_TOKEN_SECRET,
        oauth2_access_token=config.X_OAUTH2_ACCESS_TOKEN,
        oauth2_access_token_expires_at=config.X_OAUTH2_ACCESS_TOKEN_EXPIRES_AT,
        oauth2_refresh_token=config.X_OAUTH2_REFRESH_TOKEN,
        oauth2_refresh_token_expires_at=config.X_OAUTH2_REFRESH_TOKEN_EXPIRES_AT,
        screen_name=config.X_SCREEN_NAME
    )
    await user_repo.update_twitter_credentials(bootstrap_user_id, creds)
    logger.info("TEMPORARY --> Twitter user credentials written in MongoDB for bootstrap user: %s", bootstrap_user_id)
    # =================================================================================
    # ===== END TEMPORARY BLOCK =====


    # Inline async function for INGESTION
    async def ingestion_job():
        # 1. Get pipeline execution frequency at app config level
        app_config = await app_config_repo.get_config()
        # app_frequency_minutes = float(app_config.scheduler_config.ingestion_pipeline_frequency_minutes)
        default_user_frequency_minutes = 1440

        users = await user_repo.find_all()
        now = datetime.utcnow()

        for user in users:
            try:
                # 2. Check if pipeline is enabled (user config takes priority, then app config)
                user_scheduler_config = getattr(user, "scheduler_config", None)
                if user_scheduler_config and hasattr(user_scheduler_config, "is_ingestion_pipeline_enabled") and user_scheduler_config.is_ingestion_pipeline_enabled is False:
                    logger.info("Skipping ingestion pipeline (user: %s disabled by user config)", user.id, extra={"job": "ingestion"})
                    continue

                app_scheduler_config = app_config.scheduler_config
                if not app_scheduler_config or not hasattr(app_scheduler_config, "is_ingestion_pipeline_enabled") or app_scheduler_config.is_ingestion_pipeline_enabled is False:
                    logger.info("Skipping ingestion pipeline (user: %s disabled by app_config or app_config missing)", user.id, extra={"job": "ingestion"})
                    continue

                # 3. Determine effective pipeline frequency (user config takes priority, then app config)
                user_frequency_minutes = getattr(user.scheduler_config, "ingestion_pipeline_frequency_minutes", None)
                effective_frequency_minutes = float(user_frequency_minutes) if user_frequency_minutes is not None else default_user_frequency_minutes #app_frequency_minutes

                # 4. Retrieve runtime status for this user
                user_runtime_status = await user_scheduler_runtime_repo.get_by_user_id(user.id)
                ingestion_last_started_at = getattr(user_runtime_status, "last_ingestion_pipeline_started_at", None) if user_runtime_status else None
                is_running = getattr(user_runtime_status, "is_ingestion_pipeline_running", False) if user_runtime_status else False

                # 5. Determine if pipeline should run
                elapsed_minutes = (now - ingestion_last_started_at).total_seconds() / 60.0 if ingestion_last_started_at else None
                # normal condition: enough time has passed AND pipeline is not running
                enough_time_passed = elapsed_minutes is not None and elapsed_minutes > effective_frequency_minutes and not is_running
                # protection condition: pipeline stuck (elapsed > 2x frequency)
                stuck_protection = elapsed_minutes is not None and elapsed_minutes > (effective_frequency_minutes * 2)
                # first run condition: no previous execution recorded 
                first_run = elapsed_minutes is None
                
                should_run = first_run or enough_time_passed or stuck_protection
                logger.info("Ingestion pipeline scheduling check (user %s): Configured frequency is %s mins, Last run started %s mins ago.", user.id, effective_frequency_minutes, f"{elapsed_minutes:.2f}", extra={"job": "ingestion"})

                if not should_run:
                    logger.info("Skipping ingestion pipeline (user: %s already running or within frequency window)", user.id, extra={"job": "ingestion"})
                    continue

                # 6. Run pipeline
                logger.info("Ingestion pipeline starting (user: %s)", user.id, extra={"job": "ingestion"})
                await ingestion_pipeline_service_instance.run_for_user(user_id=user.id)
                logger.info("Ingestion pipeline finished (user: %s)", user.id, extra={"job": "ingestion"})
                
                # 7. Update the time for next pipeline initiation using the effective frequency (user or app)
                finish_time = datetime.utcnow()
                next_start = finish_time + timedelta(minutes=effective_frequency_minutes)
                await user_scheduler_runtime_repo.update_by_user_id(user.id, {"nextScheduledIngestionPipelineStartingAt": next_start})
                logger.info("Next scheduled ingestion pipeline starting at (user: %s): %s", user.id, next_start.isoformat(), extra={"job": "ingestion"})
            
            except Exception as e:
                logger.error("Ingestion pipeline failed (user: %s): %s", user.id, str(e), extra={"error": str(e), "job": "ingestion"})
    
        # Refresh app config from repository and reschedule job if frequency changed
        new_app_config = await app_config_repo.get_config()
        new_ingestion_freq = new_app_config.scheduler_config.ingestion_pipeline_frequency_minutes
        if float(new_ingestion_freq) != float(ingestion_pipeline_frequency_minutes):
            try:
                scheduler.reschedule_job("ingestion_job", trigger="interval", minutes=new_ingestion_freq)
                ingestion_pipeline_frequency_minutes = new_ingestion_freq  # update local var for this run
                logger.info("Rescheduled app ingestion_job frequency to %s minutes", new_ingestion_freq, extra={"job": "ingestion"})
            except Exception as ex:
                logger.warning("Failed to reschedule app ingestion_job frequency: %s", str(ex), extra={"job": "ingestion"})



    # Inline async function for PUBLISHING
    async def publishing_job():
        # 1. Get pipeline execution frequency at app config level
        app_config = await app_config_repo.get_config()
        # app_frequency_minutes = float(app_config.scheduler_config.publishing_pipeline_frequency_minutes)
        default_user_frequency_minutes = 1440

        users = await user_repo.find_all()
        now = datetime.utcnow()

        for user in users:
            try:
                # 2. Check if pipeline is enabled (user config takes priority, then app config)
                user_scheduler_config = getattr(user, "scheduler_config", None)
                if user_scheduler_config and hasattr(user_scheduler_config, "is_publishing_pipeline_enabled") and user_scheduler_config.is_publishing_pipeline_enabled is False:
                    logger.info("Skipping publishing pipeline (user: %s disabled by user config)", user.id, extra={"job": "publishing"})
                    continue

                app_scheduler_config = app_config.scheduler_config
                if not app_scheduler_config or not hasattr(app_scheduler_config, "is_publishing_pipeline_enabled") or app_scheduler_config.is_publishing_pipeline_enabled is False:
                    logger.info("Skipping publishing pipeline (user: %s disabled by app_config or app_config missing)", user.id, extra={"job": "publishing"})
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
                # protection condition: pipeline stuck (elapsed > 2x frequency)
                stuck_protection = elapsed_minutes is not None and elapsed_minutes > (effective_frequency_minutes * 2)
                # first run condition: no previous execution recorded 
                first_run = elapsed_minutes is None

                should_run = first_run or enough_time_passed or stuck_protection
                logger.info("Publishing pipeline scheduling check (user %s): Configured frequency is %s mins, Last run started %s mins ago.", user.id, effective_frequency_minutes, f"{elapsed_minutes:.2f}", extra={"job": "ingestion"})

                if not should_run:
                    logger.info("Skipping ingestion pipeline (user: %s already running or within frequency window)", user.id, extra={"job": "ingestion"})
                    continue

                # 6. Run pipeline
                logger.info("Publishing pipeline starting (user: %s)", user.id, extra={"job": "publishing"})
                await publishing_pipeline_service_instance.run_for_user(user_id=user.id)
                logger.info("Publishing pipeline finished (user: %s)", user.id, extra={"job": "publishing"})

                # 7. Update the time for next pipeline initiation using the effective frequency (user or app)
                finish_time = datetime.utcnow()
                next_start = finish_time + timedelta(minutes=effective_frequency_minutes)
                await user_scheduler_runtime_repo.update_by_user_id(user.id, {"nextScheduledPublishingPipelineStartingAt": next_start})
                logger.info("Next scheduled publishing pipeline starting at (user: %s): %s", user.id, next_start.isoformat(), extra={"job": "publishing"})

            except Exception as e:
                logger.error("Publishing pipeline failed (user: %s): %s", user.id, str(e), extra={"error": str(e), "job": "publishing"})

        # Refresh app config from repository and reschedule job if frequency changed
        new_app_config = await app_config_repo.get_config()
        new_publishing_freq = new_app_config.scheduler_config.publishing_pipeline_frequency_minutes
        if float(new_publishing_freq) != float(publishing_pipeline_frequency_minutes):
            try:
                scheduler.reschedule_job("publishing_job", trigger="interval", minutes=new_publishing_freq)
                publishing_pipeline_frequency_minutes = new_publishing_freq  # update local var for this run
                logger.info("Rescheduled app publishing_job frequency to %s minutes", new_publishing_freq, extra={"job": "publishing"})
            except Exception as ex:
                logger.warning("Failed to reschedule app publishing_job frequency: %s", str(ex), extra={"job": "publishing"})


    # load appConfig from repo
    app_config = await app_config_repo.get_config()
    ingestion_pipeline_frequency_minutes = app_config.scheduler_config.ingestion_pipeline_frequency_minutes
    publishing_pipeline_frequency_minutes = app_config.scheduler_config.publishing_pipeline_frequency_minutes
    logger.info("Loaded application config from DB: ingestion_freq=%s min, publishing_freq=%s min", ingestion_pipeline_frequency_minutes, publishing_pipeline_frequency_minutes)
    
    # setup job execution frequency
    scheduler.add_job(ingestion_job, "interval", minutes=ingestion_pipeline_frequency_minutes, id="ingestion_job")
    scheduler.add_job(publishing_job, "interval", minutes=publishing_pipeline_frequency_minutes, id="publishing_job")
    
    # start scheduler.
    scheduler.start()
    logger.info("APScheduler started")

    yield  # Application runs here

    # shutdown scheduler
    scheduler.shutdown()
    logger.info("APScheduler stopped")


# Start FastAPI application
app = FastAPI(
    title       = "Ingestion and Publication Pipelines",
    version     = "1.0.0",
    description = "",
    lifespan    = lifespan   # start the scheduler
)

# Register routes
app.include_router(pipeline_controller.router)


if __name__ == "__main__":
    # wrap ASGI server start-up under if __name__ == "__main__":, so the run doesnt double-execute
    uvicorn.run("main:app", host="0.0.0.0", port=8000)       # En PRO --> reload=False