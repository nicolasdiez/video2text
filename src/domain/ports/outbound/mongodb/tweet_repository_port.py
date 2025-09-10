# domain/ports/outbound/mongodb/tweet_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.tweet import Tweet
from enum import Enum

class SortOrder(str, Enum):
    oldest_first = "oldest_first"
    newest_first = "newest_first"
    random = "random"

class TweetRepositoryPort(ABC):
    @abstractmethod
    async def save(self, tweet: Tweet) -> str:
        """
        Insert a new tweet document and return by its id.
        """
        ...

    @abstractmethod
    async def save_all(self, tweets: List[Tweet]) -> List[str]:
        """
        Batch insert multiple Tweet entities and return their IDs as strings.
        """
        ...

    @abstractmethod
    async def find_by_id(self, tweet_id: str) -> Optional[Tweet]:
        """
        Fetch one tweet by its id.
        """
        ...

    @abstractmethod
    async def find_by_generation_id(self, generation_id: str) -> List[Tweet]:
        """
        Fetch all tweets associated to a given tweet generation.
        """
        ...

    @abstractmethod
    async def find_unpublished_by_user(self, user_id: str, limit: int = 50, order: SortOrder = SortOrder.oldest_first) -> List[Tweet]:
        """
        Fetch unpublished tweets for a given user, up to `limit`, 
        ordered by createdAt. `order` can be "oldest_first" or "newest_first".
        """

    @abstractmethod
    async def update(self, tweet: Tweet) -> None:
        """
        Updates an existing tweet.
        """
        ...
