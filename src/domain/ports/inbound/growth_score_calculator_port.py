# src/domain/ports/inbound/growth_score_calculator_port.py

from abc import ABC, abstractmethod
from typing import Dict, Optional

from domain.entities.tweet import Tweet


class GrowthScoreCalculatorPort(ABC):
    """
    Inbound port for computing growth scores for tweets.
    Defines a flexible and extensible contract that allows:
      - computing a full growth score for a tweet
      - computing individual sub-scores (engagement, style, relevance, etc.)
      - combining sub-scores into a final score
      - supporting multiple scoring formula versions
      - recalculating scores when the scoring model evolves
    """

    @abstractmethod
    async def compute_growth_score(self, tweet: Tweet) -> Optional[Dict[str, float]]:
        """
        Compute the full growth score for a tweet.
        Returns a dictionary of sub-scores plus an 'overall' score.
        Example:
            {
                "engagement": 0.72,
                "style_alignment": 0.88,
                "topic_relevance": 0.81,
                "overall": 0.82
            }
        """
        ...

    @abstractmethod
    async def compute_subscores(self, tweet: Tweet) -> Dict[str, float]:
        """
        Compute individual sub-scores for the tweet.
        Sub-scores may include:
          - engagement score (based on stats)
          - style alignment score (based on embeddings)
          - topic relevance score (based on embeddings)
          - any future metrics
        Returns a dictionary of sub-scores without the final 'overall' score.
        """
        ...

    @abstractmethod
    async def combine_subscores(self, subscores: Dict[str, float]) -> float:
        """
        Combine the sub-scores into a single final 'overall' score.
        Allows different weighting strategies or formula versions.
        """
        ...

    @abstractmethod
    def scoring_version(self) -> str:
        """
        Return the version identifier of the scoring formula.
        Useful for tracking changes in scoring logic over time.
        Example: 'v1', 'v2.1', etc.
        """
        ...

    @abstractmethod
    async def recompute_for_historical_tweets(self, user_id: str) -> None:
        """
        Optional: Recompute growth scores for all tweets of a user.
        Useful when:
          - the scoring formula changes
          - new embeddings become available
          - new stats arrive
        """
        ...
