# src/adapters/outbound/transcription_client_android_player_api_ASR.py

"""
YouTube ASR transcription client using yt-dlp with the Android player client.

This adapter implements a production-grade fallback method:
  - Forces yt-dlp to use the "android" YouTube player client.
  - Avoids signed URLs that expire quickly.
  - Avoids 403 Forbidden errors from googlevideo.com.
  - Does NOT require cookies or login.
  - Downloads audio directly into memory.
  - Runs Whisper ASR on the decoded audio.

This module preserves the TranscriptionPort interface and is fully compatible
with the rest of the application.
"""

import inspect
import io
import logging
import asyncio
from typing import Optional, Any, Tuple

import numpy as np
import yt_dlp
import soundfile as sf
import whisper

from domain.ports.outbound.transcription_port import TranscriptionPort

logger = logging.getLogger(__name__)


class YouTubeTranscriptionClientAndroidPlayerAPI_ASR(TranscriptionPort):
    """
    Fallback ASR transcription adapter using yt-dlp with the Android player client.
    """

    def __init__(self, model_name: str = "small", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model: Optional[Any] = None

        logger.info(
            "Android Player API ASR adapter initialized (model=%s device=%s)",
            self.model_name,
            self.device,
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

    # -------------------------------------------------------------------------
    # Whisper model loading
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Public async entry point
    # -------------------------------------------------------------------------
    async def transcribe(self, video_id: str, language: Optional[str] = None) -> Optional[str]:
        logger.info(
            "Starting Android Player API ASR transcription (video_id=%s)",
            video_id,
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )
        return await asyncio.to_thread(self._transcribe_sync, video_id, language)

    # -------------------------------------------------------------------------
    # Sync transcription pipeline
    # -------------------------------------------------------------------------
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

            lang_param = language[0] if isinstance(language, (list, tuple)) and language else language
            result = self._model.transcribe(audio_np, language=lang_param)

            text = result.get("text") if isinstance(result, dict) else getattr(result, "text", str(result))

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
                "Unexpected error in Android Player API ASR transcription for video %s: %s",
                video_id,
                str(exc),
                extra={"class": self.__class__.__name__, "method": method_name},
            )
            return None

    # -------------------------------------------------------------------------
    # Audio download using yt-dlp with Android player client
    # -------------------------------------------------------------------------
    def _download_audio_stream(self, video_id: str) -> Optional[bytes]:
        """
        Download audio using yt-dlp with the Android player client.
        This avoids 403 errors and does not require cookies.
        """
        method_name = inspect.currentframe().f_code.co_name
        url = f"https://www.youtube.com/watch?v={video_id}"

        logger.info(
            "Preparing yt-dlp Android client download (video_id=%s)",
            video_id,
            extra={"class": self.__class__.__name__, "method": method_name},
        )

        ytdl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "outtmpl": "-",
            "extractor_args": {
                "youtube": {
                    # Force Android client → avoids 403
                    "player_client": ["android"]
                }
            },
            "http_headers": {
                # Browser-like headers (helps with some edge cases)
                "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 13)",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        try:
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                logger.info(
                    "Downloading audio via Android client (video_id=%s)",
                    video_id,
                    extra={"class": self.__class__.__name__, "method": method_name},
                )
                info = ydl.extract_info(url, download=True)
                audio_bytes = info.get("__data")
        except Exception as exc:
            logger.exception(
                "yt-dlp Android client failed for video %s: %s",
                video_id,
                str(exc),
                extra={"class": self.__class__.__name__, "method": method_name},
            )
            return None

        if not audio_bytes:
            logger.warning(
                "yt-dlp Android client returned empty audio for video %s",
                video_id,
                extra={"class": self.__class__.__name__, "method": method_name},
            )
            return None

        logger.info(
            "yt-dlp Android client downloaded %d bytes of audio for video %s",
            len(audio_bytes),
            video_id,
            extra={"class": self.__class__.__name__, "method": method_name},
        )

        return audio_bytes

    # -------------------------------------------------------------------------
    # Audio decoding
    # -------------------------------------------------------------------------
    def _load_audio_from_bytes(self, audio_bytes: bytes) -> Tuple[Optional[np.ndarray], Optional[int]]:
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
