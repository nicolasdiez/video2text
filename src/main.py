# src/main.py

import os
import asyncio

import config

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
from adapters.outbound.mongodb.prompt_repository import MongoPromptRepository
from adapters.outbound.openai_client import OpenAIClient
from adapters.outbound.mongodb.tweet_generation_repository import MongoTweetGenerationRepository
from adapters.outbound.mongodb.tweet_repository import MongoTweetRepository

# Specific logger for this module
logger = logging.getLogger(__name__)

# Publishing pipeline
from application.services.publishing_pipeline_service import PublishingPipelineService
from adapters.outbound.twitter_client import TwitterClient

# --- Ingestion adapters & service instantiation ---
user_repo               = MongoUserRepository(database=db)
prompt_loader           = FilePromptLoader(prompts_dir="prompts")
channel_repo            = MongoChannelRepository(database=db)
video_source            = YouTubeVideoClient(api_key=config.YOUTUBE_API_KEY)
video_repo              = MongoVideoRepository(database=db)
transcription_client    = YouTubeTranscriptionClient(default_language="es")
prompt_repo             = MongoPromptRepository(database=db)
openai_client           = OpenAIClient(api_key=config.OPENAI_API_KEY)
tweet_generation_repo   = MongoTweetGenerationRepository(db=db)
tweet_repo              = MongoTweetRepository(database=db)

# Create an instance of PipelineService with the concrete implementations of the ports (i.e., inject Adapters into the Ports of IngestionPipelineService)
ingestion_pipeline_service_instance = IngestionPipelineService(
    user_repo               = user_repo,
    prompt_loader           = prompt_loader,
    channel_repo            = channel_repo,
    video_source            = video_source,
    video_repo              = video_repo,
    transcription_client    = transcription_client,
    prompt_repo             = prompt_repo,
    openai_client           = openai_client,
    tweet_generation_repo   = tweet_generation_repo,
    tweet_repo              = tweet_repo,
)

# Inject the instance of IngestionPipelineService (with all the Adapters) into the pipeline controller 
pipeline_controller.ingestion_pipeline_service = ingestion_pipeline_service_instance


# --- Publishing adapters & service instantiation ---
twitter_client = TwitterClient(
    api_key            = config.TWITTER_API_KEY,
    api_secret         = config.TWITTER_API_SECRET,
    access_token       = config.TWITTER_ACCESS_TOKEN,
    access_token_secret= config.TWITTER_ACCESS_TOKEN_SECRET,
    bearer_token       = config.TWITTER_BEARER_TOKEN
)

# Create an instance of PublishingPipelineService with the concrete implementations of the ports (i.e., inject Adapters into the Ports of PublishingPipelineService)
publishing_pipeline_service_instance = PublishingPipelineService(
    user_repo               = user_repo,
    tweet_repo              = tweet_repo,
    twitter_client          = twitter_client
)

# Inject the instance of PublishingPipelineService (with all the Adapters) into the pipeline controller 
pipeline_controller.publishing_pipeline_service = publishing_pipeline_service_instance

# APScheduler instance
scheduler = AsyncIOScheduler()

USER_ID = "64e8b0f3a1b2c3d4e5f67891"

# Lifespan context manager (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Inline async function for Ingestion
    async def ingestion_job():
        user = await user_repo.find_by_id(USER_ID)
        if not user:
            # print(f"[Main] User {USER_ID} not found")
            logger.info("User %s not found", USER_ID, extra={"module": __name__, "function": inspect.currentframe().f_code.co_name})
            return
        await ingestion_pipeline_service_instance.run_for_user(user_id=USER_ID)

    # Inline async function for Publishing
    async def publishing_job():
        user = await user_repo.find_by_id(USER_ID)
        if not user:
            # print(f"[Main] User {USER_ID} not found")
            logger.info("User %s not found", USER_ID, extra={"module": __name__, "function": inspect.currentframe().f_code.co_name})
            return
        await publishing_pipeline_service_instance.run_for_user(user_id=USER_ID)


    scheduler.add_job(ingestion_job, "interval", minutes=0)
    scheduler.add_job(publishing_job, "interval", minutes=2)
    scheduler.start()
    # print("[Main] APScheduler started")
    logger.info("APScheduler started")

    yield  # Application runs here

    # --- Shutdown ---
    scheduler.shutdown()
    # print("[Main] APScheduler stopped")
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