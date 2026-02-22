# src/adapters/outbound/mongodb/tweet_repository.py

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.tweet import (
    Tweet,
    TwitterStats,
    MetricValue,
    TweetEmbeddingRefs,
    GrowthScore,
)
from domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort
from domain.entities.user import TweetFetchSortOrder

from infrastructure.mongodb import db


class MongoTweetRepository(TweetRepositoryPort):

    def __init__(self, database: AsyncIOMotorDatabase = db):
        self._coll = database.get_collection("tweets")

    # ---------------------------------------------------------
    # SAVE OPERATIONS
    # ---------------------------------------------------------

    async def save(self, tweet: Tweet) -> str:
        doc = self._entity_to_doc(tweet)
        result = await self._coll.insert_one(doc)
        return str(result.inserted_id)
    
    async def save_all(self, tweets: List[Tweet]) -> List[str]:
        if not tweets:
            return []

        docs = [self._entity_to_doc(tweet) for tweet in tweets]
        result = await self._coll.insert_many(docs)
        return [str(_id) for _id in result.inserted_ids]

    # ---------------------------------------------------------
    # FIND OPERATIONS
    # ---------------------------------------------------------

    async def find_by_id(self, tweet_id: str) -> Optional[Tweet]:
        doc = await self._coll.find_one({"_id": ObjectId(tweet_id)})
        return self._doc_to_entity(doc) if doc else None

    async def find_by_generation_id(self, generation_id: str) -> List[Tweet]:
        cursor = self._coll.find({"generationId": ObjectId(generation_id)})
        items: List[Tweet] = []
        async for doc in cursor:
            items.append(self._doc_to_entity(doc))
        return items
    
    async def find_unpublished_by_user(
        self,
        user_id: str,
        limit: int = 50,
        order: TweetFetchSortOrder = TweetFetchSortOrder.oldest_first
    ) -> List[Tweet]:

        query = {"userId": ObjectId(user_id), "published": False}

        if order == TweetFetchSortOrder.random:
            pipeline = [
                {"$match": query},
                {"$sample": {"size": limit}}
            ]
            cursor = self._coll.aggregate(pipeline)
            return [self._doc_to_entity(doc) async for doc in cursor]

        sort_dir = 1 if order == TweetFetchSortOrder.oldest_first else -1
        cursor = (
            self._coll
            .find(query)
            .sort("createdAt", sort_dir)
            .limit(limit)
        )
        return [self._doc_to_entity(doc) async for doc in cursor]

    async def find_published_by_user(
        self,
        user_id: str,
        limit: Optional[int] = None,
        order: TweetFetchSortOrder = TweetFetchSortOrder.newest_first,
        max_days_back: Optional[int] = None,
    ) -> List[Tweet]:

        query = {"userId": ObjectId(user_id), "published": True}

        # Optional date filter: only tweets published within the last X days
        if max_days_back is not None:
            cutoff = datetime.utcnow() - timedelta(days=max_days_back)
            query["publishedAt"] = {"$gte": cutoff}

        # RANDOM ORDER
        if order == TweetFetchSortOrder.random:
            pipeline = [{"$match": query}]
            if limit:
                pipeline.append({"$sample": {"size": limit}})

            cursor = self._coll.aggregate(pipeline)
            return [self._doc_to_entity(doc) async for doc in cursor]

        # SORT ORDER
        sort_dir = 1 if order == TweetFetchSortOrder.oldest_first else -1

        cursor = self._coll.find(query).sort("publishedAt", sort_dir)

        if limit:
            cursor = cursor.limit(limit)

        items: List[Tweet] = []
        async for doc in cursor:
            items.append(self._doc_to_entity(doc))

        return items

    async def find_by_user(
        self,
        user_id: str,
        max_days_back: Optional[int] = None
    ) -> List[Tweet]:
        """
        Fetch all tweets belonging to a given user.
        If `max_days_back` is provided, restrict results to tweets created
        within the last X days.
        """

        query = {"user_id": user_id}

        # Apply date filter if needed
        if max_days_back is not None:
            cutoff_date = datetime.utcnow() - timedelta(days=max_days_back)
            query["created_at"] = {"$gte": cutoff_date}

        cursor = self.collection.find(query)

        docs = await cursor.to_list(length=None)

        return [Tweet.from_dict(doc) for doc in docs]

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    async def update(self, tweet: Tweet) -> None:
        doc = self._entity_to_doc(tweet)
        await self._coll.update_one(
            {"_id": ObjectId(tweet.id)},
            {"$set": doc}
        )

    # ---------------------------------------------------------
    # SERIALIZATION HELPERS — METRICS
    # ---------------------------------------------------------

    def _metric_to_doc(self, metric: Optional[MetricValue]) -> Optional[Dict[str, Any]]:
        if metric is None:
            return None

        return {
            "value": metric.value,
            "provider": metric.provider,
            "fetchedAt": metric.fetched_at,
        }

    def _metric_from_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[MetricValue]:
        if not doc:
            return None

        return MetricValue(
            value=doc.get("value"),
            provider=doc.get("provider"),
            fetched_at=doc.get("fetchedAt")
        )

    def _stats_to_doc(self, stats: Optional[TwitterStats]) -> Optional[Dict[str, Any]]:
        if stats is None:
            return None

        return {
            "likes": self._metric_to_doc(stats.likes),
            "retweets": self._metric_to_doc(stats.retweets),
            "replies": self._metric_to_doc(stats.replies),
            "quotes": self._metric_to_doc(stats.quotes),
            "impressions": self._metric_to_doc(stats.impressions),
            "bookmarks": self._metric_to_doc(stats.bookmarks),
            "authorFollowers": self._metric_to_doc(stats.author_followers),

            "profileVisits": self._metric_to_doc(stats.profile_visits),
            "detailExpands": self._metric_to_doc(stats.detail_expands),
            "linkClicks": self._metric_to_doc(stats.link_clicks),
            "userFollows": self._metric_to_doc(stats.user_follows),
            "engagementRate": self._metric_to_doc(stats.engagement_rate),
            "videoViews": self._metric_to_doc(stats.video_views),
            "mediaViews": self._metric_to_doc(stats.media_views),
            "mediaEngagements": self._metric_to_doc(stats.media_engagements),

            "raw": stats.raw or {}
        }

    def _stats_from_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[TwitterStats]:
        if not doc:
            return None

        return TwitterStats(
            likes=self._metric_from_doc(doc.get("likes")),
            retweets=self._metric_from_doc(doc.get("retweets")),
            replies=self._metric_from_doc(doc.get("replies")),
            quotes=self._metric_from_doc(doc.get("quotes")),
            impressions=self._metric_from_doc(doc.get("impressions")),
            bookmarks=self._metric_from_doc(doc.get("bookmarks")),
            author_followers=self._metric_from_doc(doc.get("authorFollowers")),

            profile_visits=self._metric_from_doc(doc.get("profileVisits")),
            detail_expands=self._metric_from_doc(doc.get("detailExpands")),
            link_clicks=self._metric_from_doc(doc.get("linkClicks")),
            user_follows=self._metric_from_doc(doc.get("userFollows")),
            engagement_rate=self._metric_from_doc(doc.get("engagementRate")),
            video_views=self._metric_from_doc(doc.get("videoViews")),
            media_views=self._metric_from_doc(doc.get("mediaViews")),
            media_engagements=self._metric_from_doc(doc.get("mediaEngagements")),

            raw=doc.get("raw", {})
        )

    # ---------------------------------------------------------
    # SERIALIZATION HELPERS — EMBEDDING REFS
    # ---------------------------------------------------------

    def _embedding_refs_to_doc(self, refs: Optional[TweetEmbeddingRefs]) -> Optional[Dict[str, Any]]:
        if refs is None:
            return None

        return {
            "tweetTextId": refs.tweet_text_id,
            "videoTranscriptId": refs.video_transcript_id,
            "creatorStyleId": refs.creator_style_id,
        }

    def _embedding_refs_from_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[TweetEmbeddingRefs]:
        if not doc:
            return None

        return TweetEmbeddingRefs(
            tweet_text_id=doc.get("tweetTextId"),
            video_transcript_id=doc.get("videoTranscriptId"),
            creator_style_id=doc.get("creatorStyleId"),
        )

    # ---------------------------------------------------------
    # SERIALIZATION HELPERS — GROWTH SCORE
    # ---------------------------------------------------------

    def _growth_score_to_doc(self, score: Optional[GrowthScore]) -> Optional[Dict[str, Any]]:
        if score is None:
            return None

        return {
            "engagement": score.engagement,
            "styleAlignment": score.style_alignment,
            "topicRelevance": score.topic_relevance,
            "overall": score.overall,
            "version": score.version,
        }

    def _growth_score_from_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[GrowthScore]:
        if not doc:
            return None

        return GrowthScore(
            engagement=doc.get("engagement"),
            style_alignment=doc.get("styleAlignment"),
            topic_relevance=doc.get("topicRelevance"),
            overall=doc.get("overall"),
            version=doc.get("version"),
        )

    # ---------------------------------------------------------
    # ENTITY <-> DOCUMENT
    # ---------------------------------------------------------

    def _doc_to_entity(self, doc: dict) -> Tweet:
        return Tweet(
            id=str(doc["_id"]),
            user_id=str(doc["userId"]),
            video_id=str(doc["videoId"]),
            generation_id=str(doc["generationId"]),
            text=doc["text"],
            index_in_generation=doc.get("indexInGeneration"),
            published=doc.get("published", False),
            published_at=doc.get("publishedAt"),
            twitter_id=doc.get("twitterId"),
            twitter_stats=self._stats_from_doc(doc.get("twitterStats")),
            embedding_refs=self._embedding_refs_from_doc(doc.get("embeddingRefs")),
            growth_score=self._growth_score_from_doc(doc.get("growthScore")),
            created_at=doc.get("createdAt", datetime.utcnow()),
            updated_at=doc.get("updatedAt", datetime.utcnow())
        )

    def _entity_to_doc(self, tweet: Tweet) -> dict:
        doc = {
            "userId": ObjectId(tweet.user_id),
            "videoId": ObjectId(tweet.video_id),
            "generationId": ObjectId(tweet.generation_id),
            "text": tweet.text,
            "indexInGeneration": tweet.index_in_generation,
            "published": tweet.published,
            "publishedAt": tweet.published_at,
            "twitterId": tweet.twitter_id,
            "twitterStats": self._stats_to_doc(tweet.twitter_stats),
            "embeddingRefs": self._embedding_refs_to_doc(tweet.embedding_refs),
            "growthScore": self._growth_score_to_doc(tweet.growth_score),
            "createdAt": tweet.created_at,
            "updatedAt": tweet.updated_at,
        }

        return {k: v for k, v in doc.items() if v is not None}
