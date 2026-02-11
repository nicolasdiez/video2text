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
from domain.ports.outbound.twitter_port import TwitterPublicationPort
from domain.entities.tweet import Tweet
from domain.ports.outbound.mongodb.user_scheduler_runtime_status_repository_port import UserSchedulerRuntimeStatusRepositoryPort

# Specific logger for this module
logger = logging.getLogger(__name__)


class PublishingPipelineService(PublishingPipelinePort):
    """
    Orchestrates the publishing pipeline:
      - Validate user exists
      - Fetch unpublished tweets (up to max_tweets_to_fetch_from_db)
      - Publish unpublished tweets (up to max_tweets_to_publish)
      - Update metadata only for those tweets actually published
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        tweet_repo: TweetRepositoryPort,
        twitter_publication_client: TwitterPublicationPort,
        user_scheduler_runtime_repo: UserSchedulerRuntimeStatusRepositoryPort,
    ):
        self.user_repo = user_repo
        self.tweet_repo = tweet_repo
        self.twitter_publication_client = twitter_publication_client
        self.user_scheduler_runtime_repo = user_scheduler_runtime_repo

    async def run_for_user(self, user_id: str) -> None:
        try:
            # 0. Starting pipeline
            try:
                await self.user_scheduler_runtime_repo.mark_publishing_started(user_id, datetime.utcnow())
                logger.info("Starting...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            except Exception:
                logger.exception("Failed to mark publishing pipeline started", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                raise

            # 1. Validate that user actually exists on the repo
            user = await self.user_repo.find_by_id(user_id)
            if user is None:
                raise LookupError(f"User '{user_id}' not found")
            logger.info("User found (username: %s)", user.username, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 2. Fetch unpublished tweets of the user
            tweets: List[Tweet] = await self.tweet_repo.find_unpublished_by_user(
                user_id=user.id,
                limit=user.max_tweets_to_fetch_from_db,
                order=user.tweet_fetch_sort_order
            )
            logger.info("Fetched %s unpublished tweets (out of max %s)", len(tweets), user.max_tweets_to_fetch_from_db, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 3. Determine how many tweets to publish
            max_tweets_to_publish = user.max_tweets_to_publish
            tweets_to_publish = tweets[:max_tweets_to_publish]

            # 4. Publish and update only those tweets
            logger.info("Starting to publish %s tweets (out of max %s)", len(tweets_to_publish), max_tweets_to_publish, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            for index, tweet in enumerate(tweets_to_publish, start=1):

                # Retrieve X user credentials
                creds = user.twitter_credentials
                if not creds or not creds.oauth1_access_token or not creds.oauth1_access_token_secret:
                    logger.error("User %s has no valid OAuth1 credentials, skipping tweet publication", user.username, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name,},)
                    continue
                
                # Publish tweet with user credentials
                tweet_id = await self.twitter_publication_client.publish(tweet.text, oauth1_access_token=creds.oauth1_access_token, oauth1_access_token_secret=creds.oauth1_access_token_secret,)
                logger.info("Tweet %s/%s published successfully with tweet_id %s", index, len(tweets_to_publish), tweet_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name,},)

                now = datetime.utcnow()
                tweet.published = True
                tweet.published_at = now
                tweet.twitter_id = tweet_id
                tweet.updated_at = now

                await self.tweet_repo.update(tweet)
                logger.info("Tweet_id %s updated in collection 'tweets' (_id: %s)", tweet_id, tweet.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 5-a. Finishing pipeline OK
            await self.user_scheduler_runtime_repo.mark_publishing_finished(user_id, datetime.utcnow(), success=True)
            await self.user_scheduler_runtime_repo.reset_publishing_failures(user_id)
            logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        
        # 5-b. Finishing pipeline KO
        except Exception:
            # increment failure counter and mark as finished with failure
            try:
                await self.user_scheduler_runtime_repo.increment_publishing_failures(user_id, by=1)
                await self.user_scheduler_runtime_repo.mark_publishing_finished(user_id, datetime.utcnow(), success=False)
            except Exception:
                logger.exception("Failed updating user runtime status after publishing pipeline error", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            logger.exception("Publishing pipeline failed", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise
