# src/domain/ports/inbound/stats_pipeline_port.py

from abc import ABC, abstractmethod

class StatsPipelinePort(ABC):
    """
    Inbound port for the tweet statistics pipeline.
    Defines the contract to:
      1) validate the user exists
      2) fetch all published tweets for that user
      3) retrieve updated performance metrics for each tweet
      4) persist the updated statistics in the repository
    """

    @abstractmethod
    async def run_for_user(self, user_id: str) -> None:
        """
        Execute the statistics pipeline for the given user_id:
          1) check user exists
          2) retrieve all published tweets for the user
          3) fetch updated stats using the configured provider(s)
          4) update each tweet entity with the new metrics
        """
        ...
