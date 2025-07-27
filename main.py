# main.py

import os
import asyncio

import uvicorn      # servidor de aplicaciones ligero y de alto rendimiento

from fastapi import FastAPI

# importo pipeline_controller para inyectarle más adelante la instancia de PipelineService con todos los adaptadores creados
import adapters.inbound.http.pipeline_controller as pipeline_controller 

from adapters.outbound.youtube_video_client import YouTubeVideoClient
from adapters.outbound.transcription_client import YouTubeTranscriptionClient
from adapters.outbound.file_prompt_loader import FilePromptLoader
from adapters.outbound.openai_client import OpenAIClient
from adapters.outbound.twitter_client import TwitterClient

from application.services.pipeline_service import PipelineService 


# Cargar credenciales del entorno
YOUTUBE_API_KEY             = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY              = os.getenv("OPENAI_API_KEY")
TWITTER_API_KEY             = os.getenv("X_API_KEY")
TWITTER_API_SECRET          = os.getenv("X_API_SECRET")
TWITTER_ACCESS_TOKEN        = os.getenv("X_API_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("X_API_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN        = os.getenv("X_API_BEARER_TOKEN")


# Instanciar los adaptadores concretos
video_source   = YouTubeVideoClient(api_key=YOUTUBE_API_KEY)
transcriber    = YouTubeTranscriptionClient(default_language="es")
prompt_loader  = FilePromptLoader(prompts_dir="prompts")
openai_client  = OpenAIClient(api_key=OPENAI_API_KEY)
twitter_client = TwitterClient(
    api_key            = TWITTER_API_KEY,
    api_secret         = TWITTER_API_SECRET,
    access_token       = TWITTER_ACCESS_TOKEN,
    access_token_secret= TWITTER_ACCESS_TOKEN_SECRET,
    bearer_token       = TWITTER_BEARER_TOKEN
)

# Crear la instancia del PipelineService con las implementaciones concretas de los adaptadores (inyectar Adapters en los Ports de PipelineService)
pipeline_service_instance = PipelineService(
    video_source   = video_source,
    transcriber    = transcriber,
    prompt_loader  = prompt_loader,
    openai_client  = openai_client,
    twitter_client = twitter_client,
)

# Inyectar la instancia de PipelineService (ya con todos los Adapters) en la variable pipeline_service (PipelineService) del pipeline controller 
pipeline_controller.pipeline_service = pipeline_service_instance

# Montar FastAPI y registrar el router de pipeline
app = FastAPI(
    title       = "YouTube→Tweet Pipeline",
    version     = "1.0.0",
    description = "Recupera videos de YouTube, genera tweets con OpenAI y los publica en Twitter."
)

app.include_router(pipeline_controller.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)       # En PRO --> reload=False