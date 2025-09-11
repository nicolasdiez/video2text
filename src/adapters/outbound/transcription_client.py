# adapters/outbound/transcription_client.py

import os
import asyncio
import inspect  # para trazas logging con print

from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi

from domain.ports.outbound.transcription_port import TranscriptionPort

class YouTubeTranscriptionClient(TranscriptionPort):
    """
    Implementación del puerto TranscriptionPort que usa YouTubeTranscriptApi para obtener la transcripción. Maneja un único idioma.
    """

    def __init__(self, default_language: str = "es"):
        self.default_language = default_language

        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")


    async def transcribe(self, video_id: str, language: Optional[str] = None) -> str:
        """
        Descarga y concatena la transcripción de un video.
        """
        lang = language or self.default_language

        # youtube_transcript_api es síncrono, lo ejecutamos en un hilo aparte
        transcript_list = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript,
            video_id,
            lang
        )

        # Unir todos los segmentos en un solo string
        full_text = " ".join(segment["text"] for segment in transcript_list)

        print(f"[YouTubeTranscriptionClient] Video transcription created successfully (youtube_video_id: {video_id})")
        
        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")
        
        return full_text
