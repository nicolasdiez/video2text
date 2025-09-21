# src/application/services/publishing_pipeline_service.py

import asyncio
from datetime import datetime
from typing import List

# logging
import inspect
import logging


from domain.ports.inbound.publishing_pipeline_port import PublishingPipelinePort
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort
from domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort
from domain.ports.outbound.twitter_port import TwitterPort
from domain.entities.user import TweetFetchSortOrder
from domain.entities.tweet import Tweet

# Specific logger for this module
logger = logging.getLogger(__name__)

class PublishingPipelineService(PublishingPipelinePort):
    """
    Orchestrates the publishing pipeline:
      1. Validate user exists
      2. Fetch unpublished tweets (up to max_tweets_to_fetch_from_db)
      3. Publish unpublished tweets (up to max_tweets_to_publish)
      4. Update metadata only for those actually published
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        tweet_repo: TweetRepositoryPort,
        twitter_client: TwitterPort,
    ):
        self.user_repo = user_repo
        self.tweet_repo = tweet_repo
        self.twitter_client = twitter_client

    async def run_for_user(self, user_id: str) -> None:
        
        # 1. Validate that user actually exists on the repo
        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            raise LookupError(f"User '{user_id}' not found")
        logger.info("User found (username: %s)", user.username, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        # 2. Fetch unpublished tweets of the user
        max_tweets_to_fetch_from_db = user.max_tweets_to_fetch_from_db
        tweets: List[Tweet] = await self.tweet_repo.find_unpublished_by_user(
            user_id=user.id,
            limit=max_tweets_to_fetch_from_db,
            order=user.tweet_fetch_sort_order
        )
        # print(f"[PublishingPipelineService] Fetched {len(tweets)} unpublished tweets (out of max {max_tweets_to_fetch_from_db})")
        logger.info("Fetched %s unpublished tweets (out of max %s)", len(tweets), max_tweets_to_fetch_from_db, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        # 3. Determine how many tweets to publish
        max_tweets_to_publish = user.max_tweets_to_publish
        tweets_to_publish = tweets[:max_tweets_to_publish]
        # print(f"[PublishingPipelineService] Starting to publish {len(tweets_to_publish)} tweets (out of max {max_tweets_to_publish})")
        logger.info("Starting to publish %s tweets (out of max %s)", len(tweets_to_publish), max_tweets_to_publish, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        # 4. Publish and update only those tweets
        for index, tweet in enumerate(tweets_to_publish, start=1):
            tweet_id = await self.twitter_client.publish(tweet.text)
            # print(f"[PublishingPipelineService] Tweet {index}/{len(tweets_to_publish)} published successfully with tweet_id {tweet_id}")
            logger.info("Tweet %s/%s published successfully with tweet_id %s", index, len(tweets_to_publish), tweet_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            now = datetime.utcnow()

            tweet.published = True
            tweet.published_at = now
            tweet.twitter_id = tweet_id
            tweet.updated_at = now

            await self.tweet_repo.update(tweet)
            # print(f"[PublishingPipelineService] Tweet_id {tweet_id} updated in collection 'tweets'")
            logger.info("Tweet_id %s updated in collection 'tweets'", tweet_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})