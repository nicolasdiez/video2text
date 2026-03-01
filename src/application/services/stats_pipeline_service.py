# src/application/services/stats_pipeline_service.py

import inspect
import logging
from datetime import datetime
from typing import List, Optional

from domain.ports.inbound.stats_pipeline_port import StatsPipelinePort
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort
from domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort
from domain.ports.outbound.twitter_stats.twitter_stats_port import TwitterStatsPort
from domain.ports.inbound.growth_score_calculator_port import GrowthScoreCalculatorPort
from domain.ports.outbound.mongodb.user_scheduler_runtime_status_repository_port import UserSchedulerRuntimeStatusRepositoryPort
from domain.entities.tweet import Tweet, TwitterStats, MetricValue
from domain.entities.user import TweetFetchSortOrder

from config import STATS_MIN_TWEET_AGE_MINUTES, STATS_MIN_STATS_FRESHNESS_MINUTES

logger = logging.getLogger(__name__)

class StatsPipelineService(StatsPipelinePort):
    """
    Orchestrates the statistics pipeline:
      - Validate user exists
      - Fetch published tweets
      - Retrieve updated performance metrics
      - Compute growth score
      - Persist updated tweet entities
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        tweet_repo: TweetRepositoryPort,
        stats_provider: TwitterStatsPort,
        growth_score_calculator: GrowthScoreCalculatorPort,
        user_scheduler_runtime_repo: UserSchedulerRuntimeStatusRepositoryPort,
    ):
        self.user_repo = user_repo
        self.tweet_repo = tweet_repo
        self.stats_provider = stats_provider
        self.growth_score_calculator = growth_score_calculator
        self.user_scheduler_runtime_repo = user_scheduler_runtime_repo

    def _get_latest_fetched_at(self, stats: TwitterStats) -> Optional[datetime]:
        """ 
        Extract the most recent fetched_at across all metrics in TwitterStats. 
        Helps decide whether stats are recent enough to avoid fetching again. 
        """
        if not stats:
            return None

        timestamps = []

        for field_name in stats.__dataclass_fields__:
            value = getattr(stats, field_name)
            if isinstance(value, MetricValue) and value.fetched_at:
                timestamps.append(value.fetched_at)

        return max(timestamps) if timestamps else None


    async def run_for_user(self, user_id: str) -> None:
        try:
            # 0. Starting pipeline
            try:
                await self.user_scheduler_runtime_repo.mark_stats_started(user_id, datetime.utcnow())
                logger.info("Starting...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            except Exception:
                logger.exception("Failed to mark stats pipeline started", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                raise

            # 1. Validate user exists
            user = await self.user_repo.find_by_id(user_id)
            if user is None:
                raise LookupError(f"User '{user_id}' not found")
            logger.info("User found (username: %s)", user.username, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 2. Fetch published tweets of the user
            max_days_back = 6
            tweets: List[Tweet] = await self.tweet_repo.find_published_by_user(user_id=user.id, order=user.tweet_fetch_sort_order or TweetFetchSortOrder.newest_first, max_days_back=max_days_back)
            logger.info("Fetched %s published tweets (max days back: %s)", len(tweets), max_days_back, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 3. Process each tweet
            for index, tweet in enumerate(tweets, start=1):

                logger.info("Stats tweet %s/%s - Processing... (tweet_id=%s)", index, len(tweets), tweet.twitter_id)

                if not tweet.twitter_id:
                    logger.warning("Tweet %s/%s has no twitter_id, skipping", index, len(tweets))
                    continue

                # Skip if tweet is too young (minimum tweet age)
                tweet_age_minutes = (datetime.utcnow() - tweet.created_at).total_seconds() / 60
                if tweet_age_minutes < STATS_MIN_TWEET_AGE_MINUTES:
                    logger.info(
                        "Skipping tweet %s/%s (tweet age %.1f < %s mins)",
                        index, len(tweets), tweet_age_minutes, STATS_MIN_TWEET_AGE_MINUTES
                    )
                    continue

                # Skip if stats are too fresh (minimum stats freshness)
                if tweet.twitter_stats:
                    latest_ts = self._get_latest_fetched_at(tweet.twitter_stats)
                    if latest_ts:
                        age_minutes = (datetime.utcnow() - latest_ts).total_seconds() / 60
                        if age_minutes < STATS_MIN_STATS_FRESHNESS_MINUTES:
                            logger.info(
                                "Skipping tweet %s/%s (stats freshness %.1f < %s mins)",
                                index, len(tweets), age_minutes, STATS_MIN_STATS_FRESHNESS_MINUTES
                            )
                            continue

                # Fetch stats from provider
                try:
                    tweet.twitter_id = "2023075568980488581"  # debug twitter id (real)
                    stats = await self.stats_provider.fetch_tweet_stats(tweet.twitter_id)
                    logger.info("Fetched stats for tweet %s/%s (twitter_id: %s)", index, len(tweets), tweet.twitter_id)
                except Exception:
                    logger.exception("Failed to fetch stats for tweet_id %s", tweet.twitter_id)
                    continue

                # Skip if stats is None
                if stats is None:
                    logger.warning("Stats is None for tweet_id %s, skipping update and growth score", tweet.twitter_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                    continue

                # Update tweet stats
                now = datetime.utcnow()
                tweet.twitter_stats = stats
                tweet.updated_at = now
                logger.info("Updated tweet stats in collection 'tweets' (twitter_id: %s)", tweet.twitter_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                # Compute growth score
                try:
                    growth_score = await self.growth_score_calculator.compute_growth_score(tweet)
                    if growth_score:
                        tweet.growth_score = growth_score
                    logger.info("Computed growth score for tweet %s/%s: %s", index, len(tweets), tweet.growth_score, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                except Exception:
                    logger.exception("Failed to compute growth score for tweet_id %s", tweet.twitter_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                # Persist updated tweet
                try:
                    await self.tweet_repo.update(tweet)
                    logger.info("Updated tweet stats in DB (tweet_id: %s, _id: %s)", tweet.twitter_id, tweet.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                except Exception:
                    logger.exception("Failed to update tweet in DB (tweet_id: %s)", tweet.twitter_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                logger.info("Stats tweet %s/%s - Process finished", index, len(tweets), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 4-a. Finishing pipeline OK
            await self.user_scheduler_runtime_repo.mark_stats_finished(user_id, datetime.utcnow(), success=True)
            await self.user_scheduler_runtime_repo.reset_stats_failures(user_id)
            logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        # 4-b. Finishing pipeline KO
        except Exception:
            try:
                await self.user_scheduler_runtime_repo.increment_stats_failures(user_id, by=1)
                await self.user_scheduler_runtime_repo.mark_stats_finished(user_id, datetime.utcnow(), success=False)
            except Exception:
                logger.exception("Failed updating user runtime status after stats pipeline error", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            logger.exception("Stats pipeline failed", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise
