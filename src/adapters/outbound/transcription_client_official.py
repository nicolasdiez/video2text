# adapters/outbound/transcription_client_official.py
"""
Adapter that uses the YouTube Data API (googleapiclient) to list and download captions.
The adapter expects an injected `youtube_client` (googleapiclient.discovery.Resource)
constructed elsewhere (e.g., with an app-owned OAuth refresh token).
"""

import inspect
import logging
import asyncio
from typing import Optional, Any

from googleapiclient.errors import HttpError

from domain.ports.outbound.transcription_port import TranscriptionPort

logger = logging.getLogger(__name__)


class YouTubeTranscriptionClientOfficialDataAPI(TranscriptionPort):
    """
    Uses the official YouTube Data API to list caption tracks and download a caption file.
    Returns the transcription as a string or None when no captions are available or on failure.

    Construction:
      - Provide a `youtube_client` built with googleapiclient.discovery.build(..., credentials=...).
      - The adapter does not read environment or config directly; credentials and client
        lifecycle are the caller's responsibility (allows easy testing and DI).
    """

    def __init__(self, youtube_client: Optional[Any] = None):
        """
        Initialize the adapter with an injected youtube_client.
        Raise RuntimeError if youtube_client is not provided.
        """
        if youtube_client is None:
            raise RuntimeError("youtube_client must be provided to YouTubeTranscriptionClientOfficialDataAPI")
        self.youtube = youtube_client

        logger.info(
            "YouTube Data API official client initialized",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

    async def transcribe(self, video_id: str, language: Optional[str] = None) -> Optional[str]:
        """
        Public async entry point. Runs the blocking API calls in a thread to avoid blocking the event loop.
        """
        logger.info(
            "Starting transcription retrieval (video_id=%s)",
            video_id,
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )
        return await asyncio.to_thread(self._get_captions_via_data_api, video_id)

    def _get_captions_via_data_api(self, video_id: str) -> Optional[str]:
        """
        Synchronously list caption tracks for the video and download the preferred track.
        Returns the caption body as UTF-8 string, or None on any error or when no captions exist.
        """
        # 1) List caption tracks
        try:
            resp = self.youtube.captions().list(part="id,snippet", videoId=video_id).execute()
        except HttpError as e:
            logger.warning(
                "captions.list HttpError for video %s: %s",
                video_id,
                e,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None
        except Exception as e:
            logger.exception(
                "Unexpected error listing captions for video %s: %s",
                video_id,
                e,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None

        items = resp.get("items", [])
        if not items:
            logger.info(
                "No captions found for video %s",
                video_id,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None

        # 2) Prefer a manually uploaded track over auto-generated ASR
        caption_id = None
        for it in items:
            kind = it.get("snippet", {}).get("trackKind")
            if kind and kind.upper() != "ASR":
                caption_id = it["id"]
                break
        if caption_id is None:
            caption_id = items[0]["id"]

        # 3) Download the caption track (SRT format)
        try:
            download = self.youtube.captions().download(id=caption_id, tfmt="srt").execute()
        except HttpError as e:
            logger.warning(
                "captions.download HttpError for video %s caption %s: %s",
                video_id,
                caption_id,
                e,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None
        except Exception as e:
            logger.exception(
                "Unexpected error downloading caption %s for video %s: %s",
                caption_id,
                video_id,
                e,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None

        # 4) Normalize and return the response body as string
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
            # Some client responses embed the body in a dict under 'body'
            body = download.get("body")
            if isinstance(body, bytes):
                try:
                    return body.decode("utf-8")
                except Exception:
                    return None
            return body
        try:
            return str(download)
        except Exception:
            return None
