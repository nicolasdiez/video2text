# src/domain/ports/inbound/generation_pipeline_port.py

from abc import ABC, abstractmethod

class GenerationPipelinePort(ABC):
    """
    Inbound port for the generation pipeline.
    Defines the contract to fetch channels for a user, process new videos, generate tweets, and persist them.
    """

    @abstractmethod
    async def run_for_user(self, user_id: str) -> None:
        """
        Execute the generation pipeline for the given user_id:
          1) retrieve channels linked to user_id
          2) fetch and transcribe new videos
          3) generate tweets via OpenAI
          4) save generated tweets to the database
        """
        raise NotImplementedError
