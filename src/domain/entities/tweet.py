# src/domain/entities/tweet.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass(kw_only=True)
class Tweet:
    id: Optional[str] = None
    user_id: str
    video_id: str
    generation_id: str                          # FK → tweet_generations._id
    text: str
    index_in_generation: Optional[int] = None   # Posición dentro de la generación
    published: bool = False                     # True if already published in X
    published_at: Optional[datetime] = None     # Publication day in X
    twitter_id: Optional[str] = None            # ID of the tweet in X
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[str] = None
