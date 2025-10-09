# src/domain/ports/transcription_port.py

from abc import ABC, abstractmethod
from typing import Optional

class TranscriptionPort(ABC):
    """
    Puerto que define la abstracción para obtener transcripciones de video. Acepta un único código de idioma.
    """

    @abstractmethod
    async def transcribe(self, video_id: str, language: Optional[str] = None) -> Optional[str]:
        pass
