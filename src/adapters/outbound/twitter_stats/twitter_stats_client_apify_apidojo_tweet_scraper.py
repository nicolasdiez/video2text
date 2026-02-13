# src/adapters/outbound/twitter_stats/twitter_stats_client_apify_apidojo_tweet_scraper.py

import aiohttp
import logging
import inspect
from typing import Optional

from domain.ports.outbound.twitter_stats.twitter_stats_port import TwitterStatsPort
from domain.entities.tweet import TwitterStats, MetricValue

logger = logging.getLogger(__name__)


class TwitterStatsClientApifyApidojoTweetScraper(TwitterStatsPort):
    """
    Adapter that retrieves tweet performance metrics using the Apify Actor:
    https://console.apify.com/actors/apidojo~tweet-scraper

    This adapter uses the Apify run-sync API to execute the actor and return
    the scraped tweet statistics in a normalized TwitterStats object.
    """

    def __init__(self, apify_token: str):
        self.apify_token = apify_token
        self.actor_name = "apidojo~tweet-scraper"

        logger.info("Initialized", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})


    async def fetch_tweet_stats(self, tweet_id: str) -> Optional[TwitterStats]:
        logger.info("Fetching tweet stats...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

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
                        logger.warning("Apify returned non-200 status: %s", response.status, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                        return None

                    data = await response.json()

        except Exception as e:
            logger.error("Apify request failed: %s", str(e), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None

        # Expecting a list with exactly one tweet result
        if not isinstance(data, list) or len(data) == 0:
            logger.warning("Unexpected Apify response format", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None

        raw = data[0]

        # Convert raw values into MetricValue objects
        def mv(value):
            return MetricValue(value=value, provider="apify_apidojo_tweet_scraper") if value is not None else None

        stats = TwitterStats(
            likes=mv(raw.get("likes")),
            retweets=mv(raw.get("retweets")),
            replies=mv(raw.get("replies")),
            quotes=mv(raw.get("quotes")),
            impressions=mv(raw.get("viewsCount")),
            bookmarks=mv(raw.get("bookmarks")),

            profile_visits=None,
            detail_expands=None,
            link_clicks=None,
            user_follows=None,
            engagement_rate=None,
            video_views=None,
            media_views=None,
            media_engagements=None,

            raw=raw
        )

        logger.info("Tweet stats fetched successfully", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return stats
