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
    oauth2_access_token: str
    oauth2_access_token_expires_at: Optional[datetime] = None
    oauth2_refresh_token: Optional[str] = None
    oauth2_refresh_token_expires_at: Optional[datetime] = None
    screen_name: Optional[str] = None


@dataclass(kw_only=True)
class User:
    """
    Domain entity representing an application user.
    scheduler_config is optional; when absent, the application-level config should be used.
    """

    # Core identity
    id: Optional[str] = None
    username: str                     # You can keep this if you want, but email is now the real login field
    email: str                        # Required for login
    hashed_password: str              # Stored hashed password (never plaintext)
    is_active: bool = True            # Required for auth flows

    # API keys / credentials
    openai_api_key: Optional[str] = None
    twitter_credentials: Optional[UserTwitterCredentials] = None

    # Scheduler config
    scheduler_config: Optional[SchedulerConfig] = None

    # Tweet generation preferences
    max_tweets_to_fetch_from_db: int = 10
    max_tweets_to_publish: int = 5
    tweet_fetch_sort_order: Optional[TweetFetchSortOrder] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
