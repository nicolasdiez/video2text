# adapters/outbound/transcription_client_official.py

import inspect
import logging
import asyncio
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from domain.ports.outbound.transcription_port import TranscriptionPort

logger = logging.getLogger(__name__)

class YouTubeTranscriptionClientOfficial(TranscriptionPort):
    """
    Simple adapter that uses only the YouTube Data API (googleapiclient) to list and download captions. 
    Returns the transcription as str or None when no captions are available or when download fails.
    """

    def __init__(self, api_key: Optional[str] = None):

        # Use provided API key or read from environment
        self.api_key = api_key or __import__("os").environ.get("YOUTUBE_API_KEY")
        if not self.api_key:
            raise RuntimeError("YOUTUBE_API_KEY not defined")
        
        # Build the official YouTube Data API client
        self.youtube = build("youtube", "v3", developerKey=self.api_key)
        logger.info("YouTube Data API official client initialized", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

    async def transcribe(self, video_id: str, language: Optional[str] = None) -> Optional[str]:
        """
        Attempt to list captions for the video and download the preferred track.
        Returns None if no captions are found or if an authorization/quota error occurs.
        """
        logger.info("Starting transcription (video_id=%s)", video_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        return await asyncio.to_thread(self._get_captions_via_data_api, video_id)

    def _get_captions_via_data_api(self, video_id: str) -> Optional[str]:
        # List caption tracks for the video
        try:
            resp = self.youtube.captions().list(part="id,snippet", videoId=video_id).execute()
        except HttpError as e:
            # Log a warning when the Data API rejects the request (403/401/quota)
            logger.warning("captions.list HttpError for video %s: %s", video_id, e, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None
        except Exception as e:
            # Unexpected errors are logged and result in None
            logger.exception("Unexpected error listing captions for video %s: %s", video_id, e, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None

        items = resp.get("items", [])
        if not items:
            # No caption tracks published for this video
            logger.info("No captions found for video %s", video_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None

        # Prefer a non-auto-generated track if available
        caption_id = None
        for it in items:
            kind = it.get("snippet", {}).get("trackKind")
            if kind and kind.upper() != "ASR":
                caption_id = it["id"]
                break
        if caption_id is None:
            caption_id = items[0]["id"]

        # Download the caption track (may require OAuth for some tracks)
        try:
            download = self.youtube.captions().download(id=caption_id, tfmt="srt").execute()
        except HttpError as e:
            logger.warning("captions.download HttpError for video %s caption %s: %s", video_id, caption_id, e, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None
        except Exception as e:
            logger.exception("Unexpected error downloading caption %s for video %s: %s", caption_id, video_id, e, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None

        # Normalize possible return types from the client
        if isinstance(download, bytes):
            try:
                return download.decode("utf-8")
            except Exception:
                return None
        if hasattr(download, "read"):
            try:
                return download.read().decode("utf-8")
            except Exception:
                return None
        if isinstance(download, dict):
            # Some client responses embed the body in a dict
            return download.get("body")
        return str(download)
