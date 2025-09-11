# domain/entities/user.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class TweetFetchSortOrder(str, Enum):
    oldest_first = "oldest_first"
    newest_first = "newest_first"
    random = "random"


@dataclass
class TwitterCredentials:
    access_token: str
    access_token_secret: str
    screen_name: str  # Visible name on Twitter


@dataclass(kw_only=True)
class User:
    id: Optional[str] = None
    username: str                                               # Email or username
    openai_api_key: Optional[str] = None
    twitter_credentials: Optional[TwitterCredentials] = None

    ingestion_polling_interval: Optional[int] = None            # in minutes
    publishing_polling_interval: Optional[int] = None           # in minutes
    max_tweets_to_fetch: int = 10
    max_tweets_to_publish: int = 5
    tweet_fetch_sort_order: Optional[TweetFetchSortOrder] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

