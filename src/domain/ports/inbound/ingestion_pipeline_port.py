# src/domain/ports/inbound/ingestion_pipeline_port.py

from abc import ABC, abstractmethod

class IngestionPipelinePort(ABC):
    """
    Inbound port for the ingestion pipeline.
    Defines the contract to fetch channels for a user, process new videos, generate tweets, and persist them.
    """

    @abstractmethod
    async def run_for_user(self, user_id: str, prompt_file: str, max_videos_to_fetch_per_channel: int = 2, max_tweets_to_generate_per_video: int = 3) -> None:
        """
        Execute the ingestion pipeline for the given user_id:
          1) retrieve channels linked to user_id
          2) fetch and transcribe new videos
          3) generate tweets via OpenAI
          4) save generated tweets to the database
        """
        ...
