# src/adapters/outbound/twitter_stats/twitter_stats_client_apify_apidojo_tweet_scraper.py

import aiohttp  # async http client lib
import logging
import inspect
from typing import Optional, Dict

from domain.ports.outbound.twitter_stats_port import TwitterStatsPort

logger = logging.getLogger(__name__)


class TwitterStatsClientApifyApidojoTweetScraper(TwitterStatsPort):
    """
    Adapter that retrieves tweet performance metrics using the Apify Actor:
    https://console.apify.com/actors/apidojo~tweet-scraper

    This adapter uses the Apify run-sync API to execute the actor and return
    the scraped tweet statistics in a normalized dictionary format.
    """

    def __init__(self, apify_token: str):
        self.apify_token = apify_token
        self.actor_name = "apidojo~tweet-scraper"  # readable and stable

        logger.info(
            "Initialized",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
        )

    async def fetch_tweet_stats(self, tweet_id: str) -> Optional[Dict]:
        logger.info(
            "Fetching tweet stats...",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
        )

        # Build tweet URL from ID
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

        # Apify run-sync endpoint using actor NAME (not ID)
        url = (
            f"https://api.apify.com/v2/acts/{self.actor_name}/run-sync"
            f"?token={self.apify_token}"
        )

        payload = {
            "tweetUrls": [tweet_url],
            "includeRetweeters": False,
            "includeLikers": False,
            "includeQuotedTweets": False,
            "includeReplies": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=60) as response:
                    if response.status != 200:
                        logger.warning(
                            f"Apify returned non-200 status: {response.status}",
                            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
                        )
                        return None

                    data = await response.json()

        except Exception as e:
            logger.error(
                f"Apify request failed: {str(e)}",
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
            )
            return None

        # The actor returns a list of tweets; we expect exactly one
        if not isinstance(data, list) or len(data) == 0:
            logger.warning(
                "Unexpected Apify response format",
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
            )
            return None

        raw = data[0]

        # Normalize fields (Apify actor uses these names)
        normalized = {
            "likes": raw.get("likes"),
            "retweets": raw.get("retweets"),
            "replies": raw.get("replies"),
            "quotes": raw.get("quotes"),
            "impressions": raw.get("viewsCount"),
            "bookmarks": raw.get("bookmarks"),
            "provider": "apify_apidojo_tweet_scraper",
            "tweet_id": tweet_id
        }

        logger.info(
            "Tweet stats fetched successfully",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
        )

        return normalized
