# src/main.py

import os
import asyncio

import uvicorn      # ASGI ligero y de alto rendimiento (Asynchronous Server Gateway Interface server)

from fastapi import FastAPI
from infrastructure.mongodb import db

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
from adapters.outbound.openai_client import OpenAIClient
from adapters.outbound.mongodb.tweet_generation_repository import MongoTweetGenerationRepository
from adapters.outbound.mongodb.tweet_repository import MongoTweetRepository

# Publishing pipeline
from application.services.publishing_pipeline_service import PublishingPipelineService
from adapters.outbound.twitter_client import TwitterClient

# Load env variables
YOUTUBE_API_KEY             = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY              = os.getenv("OPENAI_API_KEY")
TWITTER_API_KEY             = os.getenv("X_API_KEY")
TWITTER_API_SECRET          = os.getenv("X_API_SECRET")
TWITTER_ACCESS_TOKEN        = os.getenv("X_API_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("X_API_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN        = os.getenv("X_API_BEARER_TOKEN")

# --- Ingestion adapters & service instantiation ---
user_repo               = MongoUserRepository(database=db)
prompt_loader           = FilePromptLoader(prompts_dir="prompts")
channel_repo            = MongoChannelRepository(database=db)
video_source            = YouTubeVideoClient(api_key=YOUTUBE_API_KEY)
video_repo              = MongoVideoRepository(database=db)
transcription_client    = YouTubeTranscriptionClient(default_language="es")
openai_client           = OpenAIClient(api_key=OPENAI_API_KEY)
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
    openai_client           = openai_client,
    tweet_generation_repo   = tweet_generation_repo,
    tweet_repo              = tweet_repo,
)

# Inject the instance of IngestionPipelineService (with all the Adapters) into the pipeline controller 
pipeline_controller.ingestion_pipeline_service = ingestion_pipeline_service_instance


# --- Publishing adapters & service instantiation ---
twitter_client = TwitterClient(
    api_key            = TWITTER_API_KEY,
    api_secret         = TWITTER_API_SECRET,
    access_token       = TWITTER_ACCESS_TOKEN,
    access_token_secret= TWITTER_ACCESS_TOKEN_SECRET,
    bearer_token       = TWITTER_BEARER_TOKEN
)

# Create an instance of PublishingPipelineService with the concrete implementations of the ports (i.e., inject Adapters into the Ports of PublishingPipelineService)
publishing_pipeline_service_instance = PublishingPipelineService(
    user_repo               = user_repo,
    tweet_repo              = tweet_repo,
    twitter_client          = twitter_client
)

# Inject the instance of PublishingPipelineService (with all the Adapters) into the pipeline controller 
pipeline_controller.publishing_pipeline_service = publishing_pipeline_service_instance


# Start FastAPI and register pipeline route
app = FastAPI(
    title       = "Ingestion and Publication Pipelines",
    version     = "1.0.0",
    description = ""
)

app.include_router(pipeline_controller.router)

if __name__ == "__main__":

    # wrap ASGI server start-up under if __name__ == "__main__":, so the run doesnt double-execute
    uvicorn.run("main:app", host="0.0.0.0", port=8000)       # En PRO --> reload=False