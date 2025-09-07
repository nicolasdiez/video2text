# src/domain/ports/inbound/publishing_pipeline_port.py

from abc import ABC, abstractmethod

class PublishingPipelinePort(ABC):
    """
    Inbound port for the publishing pipeline.
    Defines the contract to:
      1) validate the user exists
      2) fetch unpublished tweets up to max_tweets_to_fetch
      3) publish up to max_tweets_to_publish
      4) update the published tweets’ metadata in the database
    """

    @abstractmethod
    async def run_for_user(self, user_id: str, max_tweets_to_fetch: int = 10, max_tweets_to_publish: int = 5) -> None:
        """
        Execute the publishing pipeline for the given user_id:
          1) check user exists
          2) retrieve unpublished tweets (limit = max_tweets_to_fetch)
          3) publish tweets to Twitter (limit = max_tweets_to_publish)
          4) mark published tweets in the repository
        """
        ...
