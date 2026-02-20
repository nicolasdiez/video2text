from typing import Optional, Dict

from domain.entities.tweet import Tweet, GrowthScore
from domain.ports.inbound.growth_score_calculator_port import GrowthScoreCalculatorPort


class GrowthScoreCalculatorService(GrowthScoreCalculatorPort):
    """
    Default implementation of the GrowthScoreCalculatorPort.
    Computes a growth score for a tweet based on:
      - engagement metrics (likes, retweets, replies, etc.)
      - style alignment (via embeddings)
      - topic relevance (via embeddings)
    The scoring formula is versioned to allow future evolution.
    """

    SCORING_VERSION = "v1"

    async def compute_growth_score(self, tweet: Tweet) -> Optional[GrowthScore]:
        """
        Compute the full growth score (sub-scores + overall).
        Returns a GrowthScore object or None.
        """
        subscores = await self.compute_subscores(tweet)
        if not subscores:
            return None

        overall = await self.combine_subscores(subscores)

        return GrowthScore(
            engagement=subscores.get("engagement"),
            style_alignment=subscores.get("style_alignment"),
            topic_relevance=subscores.get("topic_relevance"),
            overall=overall,
            version=self.SCORING_VERSION,
        )

    async def compute_subscores(self, tweet: Tweet) -> Dict[str, float]:
        """
        Compute individual sub-scores.
        This implementation is intentionally simple and can be expanded later.
        """

        subscores: Dict[str, float] = {}

        # -------------------------
        # 1. Engagement score
        # -------------------------
        engagement_score = self._compute_engagement_score(tweet)
        if engagement_score is not None:
            subscores["engagement"] = engagement_score

        # -------------------------
        # 2. Style alignment score
        # -------------------------
        style_score = await self._compute_style_alignment_score(tweet)
        if style_score is not None:
            subscores["style_alignment"] = style_score

        # -------------------------
        # 3. Topic relevance score
        # -------------------------
        topic_score = await self._compute_topic_relevance_score(tweet)
        if topic_score is not None:
            subscores["topic_relevance"] = topic_score

        return subscores

    async def combine_subscores(self, subscores: Dict[str, float]) -> float:
        """
        Combine sub-scores into a final score.
        Default strategy: simple average.
        """
        if not subscores:
            return 0.0

        return sum(subscores.values()) / len(subscores)

    def scoring_version(self) -> str:
        """
        Return the version of the scoring formula.
        """
        return self.SCORING_VERSION

    async def recompute_for_historical_tweets(self, user_id: str) -> None:
        """
        Optional: Recompute scores for all tweets of a user.
        Implementation left empty intentionally.
        """
        return None

    # ---------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------

    def _compute_engagement_score(self, tweet: Tweet) -> Optional[float]:
        """
        Compute engagement score from twitter_stats.
        Updated heuristic:
        - combine engagement metrics (likes, retweets, replies, quotes, bookmarks)
        - normalize by author followers to get a relative engagement rate
        - scale to 0–1 range using a realistic engagement curve
        """
        stats = tweet.twitter_stats
        if not stats:
            return None

        # Basic engagement metrics
        likes = stats.likes.value if stats.likes else 0
        retweets = stats.retweets.value if stats.retweets else 0
        replies = stats.replies.value if stats.replies else 0
        quotes = stats.quotes.value if stats.quotes else 0
        bookmarks = stats.bookmarks.value if stats.bookmarks else 0

        # Followers of the author (critical for normalization)
        followers = stats.author_followers.value if stats.author_followers else 0
        followers = max(followers, 1)  # avoid division by zero

        # Weighted engagement formula
        raw_engagement = (
            likes +
            (2 * retweets) +
            replies +
            quotes +
            (0.5 * bookmarks)
        )

        # Engagement rate relative to audience size
        engagement_rate = raw_engagement / followers

        # ---------------------------------------------------------
        # Scale to 0–1 range using a realistic engagement curve.
        #
        # engagement_rate = raw_engagement / followers
        #
        # Examples:
        #   0% engagement   → 0.00 → score = 0.0
        #   0.1% engagement → 0.001 → score = 0.01
        #   5% engagement   → 0.05  → score = 0.50
        #   10% engagement  → 0.10  → score = 1.00 (capped)
        #   20% engagement  → 0.20  → score = 2.00 (capped)
        #
        # This curve avoids saturating too early and differentiates between normal, good, and exceptional tweets.
        # ---------------------------------------------------------
        score = min(engagement_rate * 10, 1.0)

        return score


    async def _compute_style_alignment_score(self, tweet: Tweet) -> Optional[float]:
        """
        Placeholder: compute similarity between tweet_text_embedding and creator_style_embedding.
        """
        refs = tweet.embedding_refs
        if not refs:
            return None

        if not refs.tweet_text_id or not refs.creator_style_id:
            return None

        # TODO: call vector store to compute cosine similarity
        return 0.8


    async def _compute_topic_relevance_score(self, tweet: Tweet) -> Optional[float]:
        """
        Placeholder: compute similarity between tweet_text_embedding and video_transcript_embedding.
        """
        refs = tweet.embedding_refs
        if not refs:
            return None

        if not refs.tweet_text_id or not refs.video_transcript_id:
            return None

        # TODO: call vector store to compute cosine similarity
        return 0.85
