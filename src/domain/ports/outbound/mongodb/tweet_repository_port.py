# domain/ports/outbound/mongodb/tweet_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.tweet import Tweet
from domain.entities.user import TweetFetchSortOrder


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
    async def find_unpublished_by_user(self, user_id: str, limit: Optional[int] = 50, order: TweetFetchSortOrder = TweetFetchSortOrder.oldest_first) -> List[Tweet]:
        """
        Fetch unpublished tweets for a given user, up to `limit`, 
        ordered by createdAt. `order` can be "oldest_first" or "newest_first".
        """
        ...

    @abstractmethod
    async def find_published_by_user(self, user_id: str, limit: Optional[int] = None, order: TweetFetchSortOrder = TweetFetchSortOrder.newest_first, max_days_back: Optional[int] = None) -> List[Tweet]:
        """
        Fetch published tweets for a given user.
        Supports:
        - optional `limit` on number of tweets returned
        - configurable sort order: "oldest_first", "newest_first", or "random"
        - optional `max_days_back` to restrict results to tweets published within the last X days
        """
        ...

    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        max_days_back: Optional[int] = None
    ) -> List[Tweet]:
        """
        Fetch all tweets belonging to a given user.
        Supports optional `max_days_back` to restrict results to tweets created within the last X days.
        """
        ...

    @abstractmethod
    async def update(self, tweet: Tweet) -> None:
        """
        Updates an existing tweet.
        """
        ...
