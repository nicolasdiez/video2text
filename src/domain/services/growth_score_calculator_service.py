# src/domain/services/growth_score_calculator_service.py

# === Application Service === 
# Hace orquestación. 
# Coordina repositorios, pipelines, consume servicios externos, actualiza estado, orquesta pasos.
# Aplica reglas de aplicación (no de dominio).
# Tiene efectos secundarios (persistencia, llamadas a APIs).
# Ej: IngestionPipelineService (llama a repositorios, llama al LLM, guarda tweets...)
# Regla rápida: si el código necesita un repo/client → application; si es cálculo/decisión puro sobre entidades → domain.

# === Domain Service === 
# NO es orquestación. Es lógica de dominio pura.
# No toca repositorios.
# No toca infraestructura (APIs...).
# No tiene efectos secundarios.
# Solo contiene reglas del dominio que no pertenecen a una entidad concreta.
# Los domain services no persisten ni llaman a externos. Su responsabilidad es calcular/decidir.
# Ej: Fórmula que combina likes/retweets/engagement/decay para producir un score, 
# esa fórmula no pertenece a Tweet (no es un método de entidad TODO:¿xq no?), y tampoco pertenece a un pipeline.
# Ej: "si el canal es de finanzas, aplica este ajuste", "Combinación de objetos del dominio para producir un resultado del dominio"

# Servicios sin constructor y solo métodos utilitarios (¿application o domain?)
# Si no usan repos/clients y solo realizan validaciones o cálculos deterministas (por ejemplo is_length_valid()), son domain services o incluso módulos de funciones puras / value helpers dentro del dominio.
# Si esos métodos se limitan a validaciones de reglas de negocio (p. ej. guardrails de salida del tweet), colócalos en src/domain/services/ o en src/domain/utils/ como funciones puras.


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
        # Scale to 0–1 range using a realistic engagement curve (relative to the number of followers of the account).
        #
        # engagement_rate = raw_engagement / followers
        #
        # Examples:
        #   0% engagement   → 0.00 → score = 0.0            --> poor tweet
        #   0.1% engagement → 0.001 → score = 0.01          --> poor tweet
        #   2% engagement → 0.02 → score = 0.02             --> normal tweet
        #   8% engagement   → 0.08  → score = 0.80          --> very good tweet
        #   10% engagement  → 0.10  → score = 1.00 (capped) --> amazing tweet
        #   20% engagement  → 0.20  → score = 2.00 (capped) --> amazing tweet
        #
        # This curve avoids saturating too early and differentiates between normal, good, and exceptional tweets.
        # ---------------------------------------------------------
        engagement_score = min(engagement_rate * 10, 1.0)

        return engagement_score


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
