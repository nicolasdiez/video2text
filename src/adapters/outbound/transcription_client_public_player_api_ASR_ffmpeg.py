# src/adapters/outbound/transcription_client_public_player_api_ASR_ffmpeg.py (with ffmpeg - more complex)

"""
ASR-based transcription adapter for YouTube videos. (ASR = Automatic Speech Recognition)

Behavior (simple, in-memory):
- Resolve an audio URL for the given YouTube video with yt-dlp.
- Stream/pipe the remote audio through ffmpeg to produce a WAV bytes buffer.
- Decode WAV into numpy and run a local Whisper model to transcribe.
- All temporary data lives in memory; no permanent files written.
- Logging follows the project's pattern: include class and method via inspect and "extra".

Requirements:
- yt-dlp
- ffmpeg binary on PATH
- openai/whisper (or compatible whisper package)
- soundfile (pysoundfile) and numpy
"""

import inspect
import io
import logging
import shlex
import subprocess
import asyncio
from typing import Optional, Any, Tuple

import numpy as np
import yt_dlp
import soundfile as sf
import whisper

from domain.ports.outbound.transcription_port import TranscriptionPort

logger = logging.getLogger(__name__)


class YouTubeTranscriptionClientOfficialPublicPlayerAPI_ASR_ffmpeg(TranscriptionPort):
    """
    ASR transcription adapter that downloads YouTube audio streams and runs a local Whisper model.

    Constructor:
      - model_name: Whisper model id (e.g., "tiny", "base", "small").
      - device: "cpu" or "cuda".
    """

    def __init__(self, model_name: str = "small", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model: Optional[Any] = None

        logger.info("ASR adapter initialized (model=%s device=%s)", self.model_name, self.device, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

    def _ensure_model_loaded(self) -> None:
        if self._model is None:
            logger.info("Loading Whisper model", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            self._model = whisper.load_model(self.model_name, device=self.device)
            logger.info("Whisper model loaded", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

    async def transcribe(self, video_id: str, language: Optional[str] = None) -> Optional[str]:
        """
        Async entry point: runs blocking work in a threadpool.
        Returns transcript text or None on failure.
        """
        logger.info("Starting ASR transcription (video_id=%s)", video_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        return await asyncio.to_thread(self._transcribe_sync, video_id, language)

    def _transcribe_sync(self, video_id: str, language: Optional[str]) -> Optional[str]:
        method_name = inspect.currentframe().f_code.co_name
        try:
            audio_bytes = self._download_audio_stream(video_id)
            if not audio_bytes:
                logger.warning("No audio obtained for video %s", video_id, extra={"class": self.__class__.__name__, "method": method_name})
                return None

            audio_np, sr = self._load_audio_from_bytes(audio_bytes)
            if audio_np is None:
                logger.warning("Failed to decode audio for video %s", video_id, extra={"class": self.__class__.__name__, "method": method_name})
                return None

            self._ensure_model_loaded()

            # Whisper accepts numpy audio arrays when using the OpenAI whisper repo;
            # pass the numpy array and sample rate when supported.
            logger.info("Running Whisper transcription (video_id=%s, sample_rate=%s)", video_id, sr, extra={"class": self.__class__.__name__, "method": method_name})

            try:
                lang_param = language[0] if isinstance(language, (list, tuple)) and language else language
                result = self._model.transcribe(audio_np, language=lang_param)  # returns dict with 'text'
            except TypeError:
                # fallback: whisper may accept a filename only; avoid writing to disk in this simple implementation
                logger.exception("Model transcribe call failed due to incompatible interface", extra={"class": self.__class__.__name__, "method": method_name})
                return None

            text = None
            if isinstance(result, dict):
                text = result.get("text")
            elif hasattr(result, "text"):
                text = getattr(result, "text")
            else:
                text = str(result)

            if text:
                logger.info("ASR transcription finished (video_id=%s, chars=%d)", video_id, len(text), extra={"class": self.__class__.__name__, "method": method_name})
                return text

            logger.warning("ASR transcription returned empty result for video %s", video_id, extra={"class": self.__class__.__name__, "method": method_name})
            return None

        except Exception as exc:
            logger.exception("Unexpected error in ASR transcription for video %s: %s", video_id, str(exc), extra={"class": self.__class__.__name__, "method": method_name})
            return None

    def _download_audio_stream(self, video_id: str) -> Optional[bytes]:
        """
        Resolve and stream the best audio format via yt-dlp and ffmpeg.
        Returns WAV bytes (PCM16 LE, 1 channel, 16000 Hz) or None on failure.
        """
        method_name = inspect.currentframe().f_code.co_name
        url = f"https://www.youtube.com/watch?v={video_id}"
        ytdl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            logger.info("yt-dlp extracted info for video %s", video_id, extra={"class": self.__class__.__name__, "method": method_name})
        except Exception as exc:
            logger.exception("yt-dlp failed to extract info for video %s: %s", video_id, str(exc), extra={"class": self.__class__.__name__, "method": method_name})
            return None

        formats = info.get("formats", []) if isinstance(info, dict) else []
        audio_url = None
        for fmt in reversed(formats):
            if fmt.get("acodec") and fmt.get("acodec") != "none" and fmt.get("url"):
                audio_url = fmt["url"]
                break
        if not audio_url:
            audio_url = info.get("url") if isinstance(info, dict) else None

        if not audio_url:
            logger.warning("No audio URL found for video %s", video_id, extra={"class": self.__class__.__name__, "method": method_name})
            return None

        logger.info("Selected audio format for video %s", video_id, extra={"class": self.__class__.__name__, "method": method_name})

        ffmpeg_cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            audio_url,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            "pipe:1",
        ]

        try:
            proc = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10_485_760,
            )
        except Exception as exc:
            logger.exception("Failed to start ffmpeg for video %s: %s", video_id, str(exc), extra={"class": self.__class__.__name__, "method": method_name})
            return None

        try:
            stdout_data, stderr_data = proc.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_data, stderr_data = proc.communicate()
            logger.warning("ffmpeg timed out for video %s", video_id, extra={"class": self.__class__.__name__, "method": method_name})
        except Exception as exc:
            proc.kill()
            logger.exception("Error while running ffmpeg for video %s: %s", video_id, str(exc), extra={"class": self.__class__.__name__, "method": method_name})
            return None

        if proc.returncode != 0:
            logger.warning("ffmpeg exited with code %s for video %s; stderr=%s", proc.returncode, video_id, (stderr_data.decode("utf-8", errors="replace")[:400] if stderr_data else ""), extra={"class": self.__class__.__name__, "method": method_name})
            return None

        logger.info("ffmpeg produced %d bytes of WAV for video %s", len(stdout_data) if stdout_data else 0, video_id, extra={"class": self.__class__.__name__, "method": method_name})
        return stdout_data

    def _load_audio_from_bytes(self, wav_bytes: bytes) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Decode WAV bytes into a mono float32 numpy array and return (array, sample_rate).
        """
        method_name = inspect.currentframe().f_code.co_name
        try:
            bio = io.BytesIO(wav_bytes)
            data, sr = sf.read(bio, dtype="float32")
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            logger.info("Decoded WAV into numpy array (samples=%d, sr=%d)", data.shape[0], sr, extra={"class": self.__class__.__name__, "method": method_name})
            return data, sr
        except Exception as exc:
            logger.exception("Failed to decode WAV bytes: %s", str(exc), extra={"class": self.__class__.__name__, "method": method_name})
            return None, None
