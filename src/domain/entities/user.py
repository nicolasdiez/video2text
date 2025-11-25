# src/domain/entities/user.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

from domain.value_objects.scheduler_config import SchedulerConfig


class TweetFetchSortOrder(str, Enum):
    oldest_first = "oldest_first"
    newest_first = "newest_first"
    random = "random"


@dataclass
class UserTwitterCredentials:
    """
    Credentials related to the user's Twitter account.
    """
    oauth1_access_token: str
    oauth1_access_token_secret: str
    oauth2_access_token: str                                    # For future OAuth2.0
    oauth2_access_token_expires_at: Optional[datetime] = None   # For future OAuth2.0
    oauth2_refresh_token: Optional[str] = None                  # For future OAuth2.0
    oauth2_refresh_token_expires_at: Optional[datetime] = None  # For future OAuth2.0
    screen_name: Optional[str] = None                           # Visible name on Twitter


@dataclass(kw_only=True)
class User:
    """
    Domain entity representing an application user.
scheduler_config is optional; when absent, the application-level config should be used.
    """
    id: Optional[str] = None
    username: str                                               # Email or username
    openai_api_key: Optional[str] = None

    twitter_credentials: Optional[UserTwitterCredentials] = None
    scheduler_config: Optional[SchedulerConfig] = None          # Per-user scheduler configuration (overrides app defaults)

    max_tweets_to_fetch_from_db: int = 10
    max_tweets_to_publish: int = 5
    tweet_fetch_sort_order: Optional[TweetFetchSortOrder] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
