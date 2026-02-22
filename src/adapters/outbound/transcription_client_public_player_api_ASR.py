# src/adapters/outbound/transcription_client_public_player_api_ASR.py 
# (WITHOUT ffmpeg - simpler and more reliable, in theory)

"""
YouTube ASR transcription client using yt-dlp for direct audio download.

This version implements:
  - Solution 1: Browser-like headers (User-Agent, Accept-Language)
  - Solution 2: Optional cookie file support (cookies.txt)

These additions significantly reduce HTTP 403 errors from YouTube CDN by
making yt-dlp requests look more like a real browser session and by providing
consent cookies when available.

Pipeline:
  1. yt-dlp extracts metadata and selects best audio format.
  2. yt-dlp downloads the audio file to an in-memory buffer.
  3. The audio is decoded with soundfile into a numpy array.
  4. Whisper runs ASR on the numpy audio.

All public interfaces remain unchanged.
"""

import inspect
import io
import logging
import asyncio
import os
from typing import Optional, Any, Tuple

import numpy as np
import yt_dlp
import soundfile as sf
import whisper

from domain.ports.outbound.transcription_port import TranscriptionPort

logger = logging.getLogger(__name__)


class YouTubeTranscriptionClientOfficialPublicPlayerAPI_ASR(TranscriptionPort):
    """
    ASR transcription adapter that downloads YouTube audio streams and runs a local Whisper model.
    """

    def __init__(self, model_name: str = "small", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model: Optional[Any] = None

        logger.info(
            "ASR adapter initialized (model=%s device=%s)",
            self.model_name,
            self.device,
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

    def _ensure_model_loaded(self) -> None:
        if self._model is None:
            logger.info(
                "Loading Whisper model",
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            self._model = whisper.load_model(self.model_name, device=self.device)
            logger.info(
                "Whisper model loaded",
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )

    async def transcribe(self, video_id: str, language: Optional[str] = None) -> Optional[str]:
        logger.info(
            "Starting ASR transcription (video_id=%s)",
            video_id,
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )
        return await asyncio.to_thread(self._transcribe_sync, video_id, language)

    def _transcribe_sync(self, video_id: str, language: Optional[str]) -> Optional[str]:
        method_name = inspect.currentframe().f_code.co_name
        try:
            audio_bytes = self._download_audio_stream(video_id)
            if not audio_bytes:
                logger.warning(
                    "No audio obtained for video %s",
                    video_id,
                    extra={"class": self.__class__.__name__, "method": method_name},
                )
                return None

            audio_np, sr = self._load_audio_from_bytes(audio_bytes)
            if audio_np is None:
                logger.warning(
                    "Failed to decode audio for video %s",
                    video_id,
                    extra={"class": self.__class__.__name__, "method": method_name},
                )
                return None

            self._ensure_model_loaded()

            logger.info(
                "Running Whisper transcription (video_id=%s, sample_rate=%s)",
                video_id,
                sr,
                extra={"class": self.__class__.__name__, "method": method_name},
            )

            try:
                lang_param = language[0] if isinstance(language, (list, tuple)) and language else language
                result = self._model.transcribe(audio_np, language=lang_param)
            except TypeError:
                logger.exception(
                    "Model transcribe call failed due to incompatible interface",
                    extra={"class": self.__class__.__name__, "method": method_name},
                )
                return None

            text = None
            if isinstance(result, dict):
                text = result.get("text")
            elif hasattr(result, "text"):
                text = getattr(result, "text")
            else:
                text = str(result)

            if text:
                logger.info(
                    "ASR transcription finished (video_id=%s, chars=%d)",
                    video_id,
                    len(text),
                    extra={"class": self.__class__.__name__, "method": method_name},
                )
                return text

            logger.warning(
                "ASR transcription returned empty result for video %s",
                video_id,
                extra={"class": self.__class__.__name__, "method": method_name},
            )
            return None

        except Exception as exc:
            logger.exception(
                "Unexpected error in ASR transcription for video %s: %s",
                video_id,
                str(exc),
                extra={"class": self.__class__.__name__, "method": method_name},
            )
            return None

    # -------------------------------------------------------------------------
    # UPDATED IMPLEMENTATION: yt-dlp direct audio download with headers + cookies
    # -------------------------------------------------------------------------
    def _download_audio_stream(self, video_id: str) -> Optional[bytes]:
        """
        Download best audio directly using yt-dlp (no ffmpeg).
        Adds:
          - Browser-like headers (Solution 1)
          - Optional cookies.txt support (Solution 2)
        """
        method_name = inspect.currentframe().f_code.co_name
        url = f"https://www.youtube.com/watch?v={video_id}"

        logger.info(
            "Preparing yt-dlp download (video_id=%s)",
            video_id,
            extra={"class": self.__class__.__name__, "method": method_name},
        )

        # Check for cookies.txt
        cookie_file = "/app/cookies.txt"
        use_cookies = os.path.exists(cookie_file)

        if use_cookies:
            logger.info(
                "Using cookies file for yt-dlp: %s",
                cookie_file,
                extra={"class": self.__class__.__name__, "method": method_name},
            )
        else:
            logger.info(
                "No cookies file found; proceeding without cookies",
                extra={"class": self.__class__.__name__, "method": method_name},
            )

        # yt-dlp options
        ytdl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "outtmpl": "-",  # output to memory
            "http_headers": {
                # Browser-like headers to reduce 403 errors
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        if use_cookies:
            ytdl_opts["cookiefile"] = cookie_file

        try:
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                logger.info(
                    "Downloading audio with yt-dlp (video_id=%s)",
                    video_id,
                    extra={"class": self.__class__.__name__, "method": method_name},
                )
                info = ydl.extract_info(url, download=True)
                audio_bytes = info.get("__data")
        except Exception as exc:
            logger.exception(
                "yt-dlp failed to download audio for video %s: %s",
                video_id,
                str(exc),
                extra={"class": self.__class__.__name__, "method": method_name},
            )
            return None

        if not audio_bytes:
            logger.warning(
                "yt-dlp returned empty audio for video %s",
                video_id,
                extra={"class": self.__class__.__name__, "method": method_name},
            )
            return None

        logger.info(
            "yt-dlp downloaded %d bytes of audio for video %s",
            len(audio_bytes),
            video_id,
            extra={"class": self.__class__.__name__, "method": method_name},
        )

        return audio_bytes

    # -------------------------------------------------------------------------

    def _load_audio_from_bytes(self, audio_bytes: bytes) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Decode audio bytes into a mono float32 numpy array and return (array, sample_rate).
        """
        method_name = inspect.currentframe().f_code.co_name
        try:
            bio = io.BytesIO(audio_bytes)
            data, sr = sf.read(bio, dtype="float32")

            if data.ndim > 1:
                data = np.mean(data, axis=1)

            logger.info(
                "Decoded audio into numpy array (samples=%d, sr=%d)",
                data.shape[0],
                sr,
                extra={"class": self.__class__.__name__, "method": method_name},
            )
            return data, sr

        except Exception as exc:
            logger.exception(
                "Failed to decode audio bytes: %s",
                str(exc),
                extra={"class": self.__class__.__name__, "method": method_name},
            )
            return None, None
