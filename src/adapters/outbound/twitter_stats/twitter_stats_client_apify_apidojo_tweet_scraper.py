# adapters/outbound/twitter_stats/twitter_stats_client_apify_apidojo_tweet_scraper.py

import logging
import inspect
from typing import Optional
from datetime import datetime

from apify_client import ApifyClient

from domain.ports.outbound.twitter_stats.twitter_stats_port import TwitterStatsPort
from domain.entities.tweet import TwitterStats, MetricValue

logger = logging.getLogger(__name__)


class TwitterStatsClientApifyApidojoTweetScraper(TwitterStatsPort):
    """
    Adapter that retrieves tweet performance metrics using the Apify Actor:
    https://console.apify.com/actors/apidojo/twitter-scraper-lite

    This adapter uses the ApifyClient to execute the actor and return
    the scraped tweet statistics in a normalized TwitterStats object.
    """

    def __init__(self, apify_token: str):
        self.apify_token = apify_token
        self.actor_name = "apidojo/twitter-scraper-lite"
        self.client = ApifyClient(apify_token)

        logger.info("Initialized", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

    async def fetch_tweet_stats(self, tweet_id: str) -> Optional[TwitterStats]:
        logger.info("Fetching tweet stats...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        tweet_url = f"https://x.com/dummyusername/status/{tweet_id}"
    
        # Correct input for twitter-scraper-lite → startUrls must be array of strings
        run_input = {
            "startUrls": [tweet_url],
            # "startUrls": ["https://x.com/elonmusk/status/1728108619189874825"],
            # "startUrls": ["https://x.com/i/web/status/2023075568980488581"],
            "maxItems": 1,
        }

        try:
            # 1. Run the Actor and wait for it to finish
            run = self.client.actor(self.actor_name).call(run_input=run_input)
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                logger.warning("Actor run did not return a datasetId", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return None

            # 2. Fetch dataset items
            items = list(self.client.dataset(dataset_id).iterate_items())

        except Exception as e:
            logger.error("Apify request failed: %s", str(e), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None

        # 3. Validate response
        # logger.warning("DEBUG RAW DATA: %s", items)
        if not items:
            logger.warning("Unexpected Apify response format (empty dataset)", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None
        raw = items[0]

        # 4. Map Apify fields to TwitterStats domain entity
        def mv(value):
            return (
                MetricValue(value=value, provider="apify_apidojo/twitter-scraper-lite", fetched_at=datetime.utcnow())
                if value is not None
                else None
            )

        stats = TwitterStats(
            likes=mv(raw.get("likeCount")),
            retweets=mv(raw.get("retweetCount")),
            replies=mv(raw.get("replyCount")),
            quotes=mv(raw.get("quoteCount")),
            impressions=mv(raw.get("viewCount")),
            bookmarks=mv(raw.get("bookmarkCount")),
            author_followers=mv(raw.get("author", {}).get("followers")),
            profile_visits=None,
            detail_expands=None,
            link_clicks=None,
            user_follows=None,
            engagement_rate=None,
            video_views=None,
            media_views=None,
            media_engagements=None,
            raw=raw,
        )

        logger.info(
            "Tweet stats fetched successfully",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

        return stats