# src/domain/ports/twitter_stats_port.py

from abc import ABC, abstractmethod
from typing import Optional, Dict

class TwitterStatsPort(ABC):
    """
    Port that abstracts the retrieval of performance metrics for a published tweet.
    This allows the application to plug different scraping providers (Apify, Bright Data, etc.)
    without changing the domain logic.
    """

    @abstractmethod
    async def fetch_tweet_stats(self, tweet_id: str) -> Optional[Dict]:
        """
        Fetches performance metrics for a given tweet ID.

        The returned dictionary should contain the metrics available from the provider,
        such as likes, retweets, replies, impressions, quotes, bookmarks, etc.

        :param tweet_id: ID of the tweet to retrieve metrics for
        :return: A dictionary with tweet metrics, or None if the provider fails
        """
        pass
