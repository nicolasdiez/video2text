# src/domain/entities/video.py

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class TranscriptSegment:
    start: float
    duration: float
    text: str

@dataclass(kw_only=True)
class Video:
    id: Optional[str] = None
    user_id: Optional[str] = None       # Redundante, pero útil para consultas
    channel_id: str                     # FK → channels._id
    youtube_video_id: str
    title: str
    url: str

    transcript: str = ''                                                            # Texto plano unificado
    transcript_segments: List[TranscriptSegment] = field(default_factory=list)      # (opcional) para guardar por fragmentos

    transcript_fetched_at: Optional[datetime] = None                                
    tweets_generated: bool = False                                                  # Flag para control rápido de si ya se generaron tweets a partir de este video

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
