# main.py

import asyncio

from adapters.outbound.twitter_client import TwitterClient
from adapters.outbound.youtube_video_client import YouTubeVideo, YouTubeVideoClient     
from adapters.outbound.transcription_client import YouTubeTranscriptionClient
from application.services.pipeline_service import PipelineService

async def main():
    # Crear los adaptadores concretos
    twitter = TwitterClient()
    video   = YouTubeVideoClient()
    transcr = YouTubeTranscriptionClient()
    
    # Componer el servicio de pipeline inyectando adaptadores
    pipeline = PipelineService(video, transcr, twitter)
    
    # Ejecutar la lógica principal del pipeline
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())