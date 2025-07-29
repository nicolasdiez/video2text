from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class TranscriptSegment:
    start: float
    duration: float
    text: str

@dataclass
class Video:
    id: Optional[str] = None
    user_id: Optional[str] = None

    channel_id: str
    youtube_video_id: str
    title: str
    url: str

    transcript: str = ''
    transcript_segments: List[TranscriptSegment] = field(default_factory=list)

    transcript_fetched_at: Optional[datetime] = None
    tweets_generated: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
