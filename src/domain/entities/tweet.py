# src/domain/entities/tweet.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Union


@dataclass(kw_only=True)
class MetricValue:
    """
    Represents a single metric value coming from a specific provider.
    Each metric stores:
    - value: the numeric value of the metric
    - provider: the provider that supplied this metric (e.g., "apify", "brightdata")
    - fetched_at: timestamp when this metric was retrieved
    """
    value: Optional[Union[int, float]] = None
    provider: Optional[str] = None
    fetched_at: Optional[datetime] = None


@dataclass(kw_only=True)
class TwitterStats:
    """
    Represents performance metrics for a published tweet.
    Supports both basic metrics (Apify) and advanced metrics (Bright Data or future providers).
    Each metric is a MetricValue, allowing multiple providers to contribute independently.
    """

    # Basic metrics (Apify)
    likes: Optional[MetricValue] = None
    retweets: Optional[MetricValue] = None
    replies: Optional[MetricValue] = None
    quotes: Optional[MetricValue] = None
    impressions: Optional[MetricValue] = None
    bookmarks: Optional[MetricValue] = None

    # Advanced metrics (Bright Data or future providers)
    profile_visits: Optional[MetricValue] = None
    detail_expands: Optional[MetricValue] = None
    link_clicks: Optional[MetricValue] = None
    user_follows: Optional[MetricValue] = None
    engagement_rate: Optional[MetricValue] = None
    video_views: Optional[MetricValue] = None
    media_views: Optional[MetricValue] = None
    media_engagements: Optional[MetricValue] = None

    # Raw payloads grouped by provider (optional but useful for debugging)
    raw: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass(kw_only=True)
class Tweet:
    """
    Domain entity representing a generated or published tweet.
    """

    id: Optional[str] = None
    user_id: str
    video_id: str
    generation_id: str                          # FK → tweet_generations._id
    text: str                                   # The tweet itself
    index_in_generation: Optional[int] = None   # Position inside the generation
    published: bool = False                     # True if already published in X
    published_at: Optional[datetime] = None     # Publication timestamp in X
    twitter_id: Optional[str] = None            # ID of the tweet in X

    # Performance metrics (optional, filled after scraping)
    twitter_stats: Optional[TwitterStats] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[str] = None
