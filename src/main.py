# /src/main.py

# TODO:
# - endpoints de consumo desde front para CRUD entities: users, channels, prompts
# - change transcription_client.py to switch from using deprecated get_transcript() to use fetch()
# - implement 2nd fallback mechanism in ingestion_pipeline_service for the transcription retrieval
# - tidy up prompt generation with user_message and system_message (prompt_composer_service.py and openai_client.py)
# - extend collection {users} to have flags: isIngestionPipelineExecuting and isPublishingPipelineExecuting (to prevent more than 1 instance to run pipeline twice or more at the sime time)
# - extend collection {users} to have variable: lastIngestionPipelineExecutionStartedAt, lastIngestionPipelineExecutionFinisheddAt
# - extend collection {users} to have variable: lastPublishingPipelineExecutionStartedAt, lastPublishingPipelineExecutionFinisheddAt
# - modify main to loop thru all {users}, but only if Pipeline is NOT already executing (flag) AND last execution > X mins (variables)
# - create a collection {prompts_master} to hold master prompts of the application, not dependent on userId, nor channelId.


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
from adapters.outbound.transcription_client import YouTubeTranscriptionClient
from adapters.outbound.transcription_client_official import YouTubeTranscriptionClientOfficial
from adapters.outbound.transcription_client_ASR import YouTubeTranscriptionClientASR
from adapters.outbound.mongodb.prompt_repository import MongoPromptRepository
from adapters.outbound.openai_client import OpenAIClient
from adapters.outbound.mongodb.tweet_generation_repository import MongoTweetGenerationRepository
from adapters.outbound.mongodb.tweet_repository import MongoTweetRepository

# Publishing pipeline
from application.services.publishing_pipeline_service import PublishingPipelineService
from adapters.outbound.twitter_client import TwitterClient

# appConfig adapter
from adapters.outbound.mongodb.app_config_repository import MongoAppConfigRepository

# factory to get a youtube_client resource for consuming Youtube Data API to retrieve video transcriptions 
from infrastructure.auth.youtube_credentials import get_youtube_client

# specific logger for this module
logger = logging.getLogger(__name__)


# create a youtube_client resource to inject as dependency into YouTubeTranscriptionClientOfficial
try:
    youtube_client = get_youtube_client(client_id=config.YOUTUBE_OAUTH_CLIENT_ID, client_secret=config.YOUTUBE_OAUTH_CLIENT_SECRET, refresh_token=config.YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN)
except RuntimeError as exc:
    logger.error("YouTube client could not be constructed: %s", str(exc), extra={"mod": __name__})
    # if instanciation fails, then rely on the transcription fallback service
    youtube_client = None

# --- Ingestion adapters & service instantiation ---
user_repo                       = MongoUserRepository(database=db)
prompt_loader                   = FilePromptLoader(prompts_dir="prompts")
channel_repo                    = MongoChannelRepository(database=db)
video_source                    = YouTubeVideoClient(api_key=config.YOUTUBE_API_KEY)
video_repo                      = MongoVideoRepository(database=db)
#transcription_client           = YouTubeTranscriptionClient(default_language="es")
transcription_client_fallback   = YouTubeTranscriptionClientASR(model_name="tiny", device="cpu")
transcription_client            = YouTubeTranscriptionClientOfficial(youtube_client=youtube_client) if youtube_client else None
prompt_repo                     = MongoPromptRepository(database=db)
openai_client                   = OpenAIClient(api_key=config.OPENAI_API_KEY)
tweet_generation_repo           = MongoTweetGenerationRepository(db=db)
tweet_repo                      = MongoTweetRepository(database=db)

# if no official Youtube API transcription client, warn in log
if transcription_client is None:
    logger.warning("YouTube official transcription client not configured; using ASR fallback only", extra={"mod": __name__})

# Create an instance of PipelineService with the concrete implementations of the ports (i.e., inject Adapters into the Ports of IngestionPipelineService)
ingestion_pipeline_service_instance = IngestionPipelineService(
    user_repo                       = user_repo,
    prompt_loader                   = prompt_loader,
    channel_repo                    = channel_repo,
    video_source                    = video_source,
    video_repo                      = video_repo,
    transcription_client            = transcription_client,
    transcription_client_fallback   = transcription_client_fallback,
    prompt_repo                     = prompt_repo,
    openai_client                   = openai_client,
    tweet_generation_repo           = tweet_generation_repo,
    tweet_repo                      = tweet_repo,
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
    user_repo               = user_repo,
    tweet_repo              = tweet_repo,
    twitter_client          = twitter_client
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

    # ===== TEMPORARY BLOCK =====
    # Escribir en el document del USER_ID las credentials de usuario que temporalmente están en .env
    # TODO: remove this block when frontend/endpoints for user credential management is ready
    USER_ID = "64e8b0f3a1b2c3d4e5f67891" # Nico
    bootstrap_user_id = USER_ID
    # Retrieve USER X credentials from env (either .env file or Github Environment secrets) and save them encrypted to mongoDB user collection
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
    logger.info("Temporary - Twitter user credentials written in MongoDB for bootstrap user: %s", bootstrap_user_id)
    # ===== END TEMPORARY BLOCK =====


    # Inline async function for Ingestion
    async def ingestion_job():
        users = await user_repo.find_all()
        for user in users:
            try:
                logger.info("Ingestion pipeline starting (user: %s)", user.id, extra={"user_id": user.id, "job": "ingestion"})
                await ingestion_pipeline_service_instance.run_for_user(user_id=user.id)
                logger.info("Ingestion pipeline finished (user: %s)", user.id, extra={"user_id": user.id, "job": "ingestion"})
            except Exception as e:
                logger.error("Ingestion pipeline failed (user: %s): %s", user.id, str(e), extra={"user_id": user.id, "error": str(e)})

    # Inline async function for Publishing
    async def publishing_job():
        users = await user_repo.find_all()
        for user in users:
            try:
                logger.info("Publishing pipeline starting (user: %s)", user.id, extra={"user_id": user.id, "job": "publishing"})
                await publishing_pipeline_service_instance.run_for_user(user_id=user.id)
                logger.info("Publishing pipeline finished (user: %s)", user.id, extra={"user_id": user.id, "job": "publishing"})
            except Exception as e:
                logger.error("Publishing pipeline failed (user: %s): %s", user.id, extra={"user_id": user.id, "error": str(e)})

    # load appConfig from DB
    app_config = await app_config_repo.get_config()
    ingestion_minutes = app_config.scheduler.ingestion_minutes
    publishing_minutes = app_config.scheduler.publishing_minutes
    logger.info("Loaded application config from DB: ingestion_freq=%s min, publishing_freq=%s min", ingestion_minutes, publishing_minutes)
    
    # setup job execution frequency dynamically
    scheduler.add_job(ingestion_job, "interval", minutes=ingestion_minutes)
    scheduler.add_job(publishing_job, "interval", minutes=publishing_minutes)
    
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