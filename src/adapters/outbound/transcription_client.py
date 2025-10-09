# adapters/outbound/transcription_client.py

import os
import asyncio

# logging
import inspect
import logging 

from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi

from domain.ports.outbound.transcription_port import TranscriptionPort

# Specific logger for this module
logger = logging.getLogger(__name__)


class YouTubeTranscriptionClient(TranscriptionPort):
    """
    Implementación del puerto TranscriptionPort que usa YouTubeTranscriptApi para obtener la transcripción. Maneja un único idioma.
    """

    def __init__(self, default_language: str = "es"):
        self.default_language = default_language

        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})


    async def transcribe(self, video_id: str, language: Optional[str] = None) -> Optional[str]:
        """
        Descarga y concatena la transcripción de un video.
        """
        logger.info("Starting...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        lang = language or self.default_language

        # youtube_transcript_api es síncrono, lo ejecutamos en un hilo aparte
        transcript_list = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript,
            video_id,
            lang
        )

        # Unir todos los segmentos en un solo string
        full_text = " ".join(segment["text"] for segment in transcript_list)

        logger.info("Video transcription created successfully (youtube_video_id: %s)", video_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        
        return full_text
