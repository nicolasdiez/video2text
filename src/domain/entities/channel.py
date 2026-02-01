# src/domain/entities/channel.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass(kw_only=True)
class Channel:
    """
    Domain entity representing a YouTube channel subscription.
    """
    id: Optional[str] = None
    user_id: str                                                # FK → users._id
    youtube_channel_id: str
    selected_prompt_id: Optional[str] = None                    # FK → prompts._id
    selected_master_prompt_id: Optional[str] = None             # FK → master_prompts._id
    title: str
    polling_interval: Optional[int] = None                      # in minutes
    max_videos_to_fetch_from_channel: Optional[int] = None      # max number of videos to retrieve from the channel
    tweets_to_generate_per_video: int                       # max number of tweets to generate for each video of the channel
    last_polled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
