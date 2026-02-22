# src/adapters/outbound/transcription_client_captions_api.py

# IMPORTANT --> Este es básicamente el unico metodo oficial, estable y fiable para recuperar transcripts de videos YT a nivel productivo.

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


class YouTubeTranscriptionClientOfficialCaptionsAPI(TranscriptionPort):
    """
    Implementación del puerto TranscriptionPort que usa YouTubeTranscriptApi para obtener la transcripción. Maneja un único idioma.
    Important: this implementation of the TranscriptionPort does NOT use the official Youtube Data API library, so it might be blocked by youtube. <---- ¿?¿?
    """

    def __init__(self, default_language: str = "es"):
        self.default_language = default_language

        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})


    async def transcribe(self, video_id: str, language: Optional[str] = None) -> Optional[str]:
        logger.info("Starting...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        lang = language or self.default_language

        try:
            transcript_list = await asyncio.to_thread(
                YouTubeTranscriptApi.get_transcript,
                video_id,
                lang
            )
        except Exception as e:
            logger.warning("Transcript API failed: %s", str(e),
                        extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None

        if not transcript_list:
            # VERY IMPORTANT: return None so fallbacks trigger in the consumer (i.e. ingestion pipeline)
            return None

        full_text = " ".join(segment["text"] for segment in transcript_list).strip()

        if not full_text:
            # Also important: empty string should not block fallbacks in the consumer (i.e. ingestion pipeline)
            return None

        logger.info("Video transcription created successfully (youtube_video_id: %s)", video_id,
                    extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return full_text

