# src/application/services/embeddings_pipeline_service.py

import inspect
import logging
from datetime import datetime
from typing import List, Optional

from domain.ports.inbound.embeddings_pipeline_port import EmbeddingsPipelinePort
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort
from domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort
from domain.ports.outbound.mongodb.video_repository_port import VideoRepositoryPort
from domain.ports.outbound.mongodb.embedding_vector_repository_port import EmbeddingVectorRepositoryPort
from domain.ports.outbound.embedding_vector_port import EmbeddingVectorPort
from domain.ports.outbound.mongodb.user_scheduler_runtime_status_repository_port import UserSchedulerRuntimeStatusRepositoryPort

from domain.value_objects.embedding_vector import EmbeddingVector
from domain.value_objects.embedding_type import EmbeddingType
from domain.entities.tweet import Tweet

logger = logging.getLogger(__name__)


class EmbeddingsPipelineService(EmbeddingsPipelinePort):
    """
    Orchestrates the embeddings pipeline:
      - Validate user exists
      - Fetch tweets of the user (optionally filtered by max_days_back)
      - Generate embeddings for tweet text and video transcript
      - Persist embeddings in the vector database
      - Update Tweet.embedding_refs accordingly
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        tweet_repo: TweetRepositoryPort,
        video_repo: VideoRepositoryPort,
        embedding_repo: EmbeddingVectorRepositoryPort,
        embedding_client: EmbeddingVectorPort,
        user_scheduler_runtime_repo: UserSchedulerRuntimeStatusRepositoryPort,
        embedding_model: str,
        tweet_max_days_back_calculate_embeddings: Optional[int] = None,
    ):
        self.user_repo = user_repo
        self.tweet_repo = tweet_repo
        self.video_repo = video_repo
        self.embedding_repo = embedding_repo
        self.embedding_client = embedding_client
        self.user_scheduler_runtime_repo = user_scheduler_runtime_repo
        self.embedding_model = embedding_model
        self.tweet_max_days_back_calculate_embeddings = tweet_max_days_back_calculate_embeddings

    async def run_for_user(self, user_id: str) -> None:
        try:
            # 0. Starting pipeline
            try:
                await self.user_scheduler_runtime_repo.mark_embeddings_started(user_id, datetime.utcnow())
                logger.info("Starting...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            except Exception:
                logger.exception("Failed to mark embeddings pipeline started", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                raise

            # 1. Validate user exists
            user = await self.user_repo.find_by_id(user_id)
            if user is None:
                raise LookupError(f"User '{user_id}' not found")
            logger.info("User found (username: %s)", user.username, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 2. Fetch tweets of the user
            tweets: List[Tweet] = await self.tweet_repo.find_by_user(
                user_id=user.id,
                max_days_back=self.tweet_max_days_back_calculate_embeddings
            )
            logger.info("Fetched %s tweets for embeddings", len(tweets), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 3. Process each tweet
            for index, tweet in enumerate(tweets, start=1):
                logger.info("Processing tweet %s/%s (_id: %s)", index, len(tweets), tweet.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                # Ensure embedding_refs exists
                if tweet.embedding_refs is None:
                    tweet.embedding_refs = tweet.embedding_refs.__class__()  # TweetEmbeddingRefs()

                # 3.a. Embedding for tweet text
                if tweet.text and not tweet.embedding_refs.tweet_text_id:
                    try:
                        logger.info("Generating embedding for tweet text...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                        vector = await self.embedding_client.get_embedding(tweet.text, self.embedding_model)

                        embedding = EmbeddingVector(
                            id=None,
                            tweet_id=tweet.id,
                            type=EmbeddingType.TWEET_TEXT,
                            vector=vector,
                            created_at=datetime.utcnow(),
                        )
                        embedding_id = await self.embedding_repo.save(embedding)
                        tweet.embedding_refs.tweet_text_id = embedding_id

                    except Exception:
                        logger.exception("Failed generating embedding for tweet text (_id: %s)", tweet.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                # 3.b. Embedding for video transcript
                if tweet.video_id and not tweet.embedding_refs.video_transcript_id:
                    try:
                        video = await self.video_repo.find_by_id(tweet.video_id)
                        if video and video.transcript:
                            logger.info("Generating embedding for video transcript...", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                            vector = await self.embedding_client.get_embedding(video.transcript, self.embedding_model)

                            embedding = EmbeddingVector(
                                id=None,
                                tweet_id=tweet.id,
                                type=EmbeddingType.VIDEO_TRANSCRIPT,
                                vector=vector,
                                created_at=datetime.utcnow(),
                            )
                            embedding_id = await self.embedding_repo.save(embedding)
                            tweet.embedding_refs.video_transcript_id = embedding_id
                        else:
                            logger.info("No transcript found for video_id %s, skipping transcript embedding", tweet.video_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                    except Exception:
                        logger.exception("Failed generating embedding for video transcript (_id: %s)", tweet.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

                # 3.c. Persist updated tweet
                try:
                    await self.tweet_repo.update(tweet)
                    logger.info("Updated tweet embedding refs (_id: %s)", tweet.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                except Exception:
                    logger.exception("Failed updating tweet after embeddings (_id: %s)", tweet.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            # 4-a. Finishing pipeline OK
            await self.user_scheduler_runtime_repo.mark_embeddings_finished(user_id, datetime.utcnow(), success=True)
            await self.user_scheduler_runtime_repo.reset_embeddings_failures(user_id)
            logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        # 4-b. Finishing pipeline KO
        except Exception:
            try:
                await self.user_scheduler_runtime_repo.increment_embeddings_failures(user_id, by=1)
                await self.user_scheduler_runtime_repo.mark_embeddings_finished(user_id, datetime.utcnow(), success=False)
            except Exception:
                logger.exception("Failed updating user runtime status after embeddings pipeline error", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

            logger.exception("Embeddings pipeline failed", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            raise
