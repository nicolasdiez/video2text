# src/application/services/publishing_pipeline_service.py

import asyncio
from datetime import datetime
from typing import List

from domain.ports.inbound.publishing_pipeline_port import PublishingPipelinePort
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort
from domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort, SortOrder
from domain.ports.outbound.twitter_port import TwitterPort

from domain.entities.tweet import Tweet


class PublishingPipelineService(PublishingPipelinePort):
    """
    Orchestrates the publishing pipeline:
      1. Validate user exists
      2. Fetch unpublished tweets (up to max_tweets_to_fetch)
      3. Publish up to max_tweets_to_publish of them
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

    async def run_for_user(
        self,
        user_id: str,
        max_tweets_to_fetch: int = 10,
        max_tweets_to_publish: int = 5
    ) -> None:
        
        # 1. Validate that user_id actually exists on the repo
        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            raise LookupError(f"User '{user_id}' not found")
        print(f"[PublishingPipelineService] User found: {user_id}")

        # 2. Fetch unpublished tweets
        tweets: List[Tweet] = await self.tweet_repo.find_unpublished_by_user(
            user_id=user_id,
            limit=max_tweets_to_fetch,
            order=SortOrder.oldest_first
        )
        print(f"[PublishingPipelineService] Fetched {len(tweets)} unpublished tweets (out of max {max_tweets_to_fetch})")

        # 3. Determine how many to publish
        tweets_to_publish = tweets[:max_tweets_to_publish]
        print(f"[PublishingPipelineService] Starting to publish {len(tweets_to_publish)} tweets (out of max {max_tweets_to_publish})")

        # 4. Publish and update only those tweets
        for index, tweet in enumerate(tweets_to_publish, start=1):
            tweet_id = await self.twitter_client.publish(tweet.text)
            print(f"[PublishingPipelineService] Tweet {index}/{len(tweets_to_publish)} published successfully with tweet_id {tweet_id}")
            now = datetime.utcnow()

            tweet.published = True
            tweet.published_at = now
            tweet.twitter_id = tweet_id
            tweet.updated_at = now

            await self.tweet_repo.update(tweet)
            print(f"[PublishingPipelineService] Tweet_id {tweet_id} updated in collection 'tweets'")

