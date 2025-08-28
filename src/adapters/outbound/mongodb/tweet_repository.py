# adapters/outbound/mongo/tweet_repository.py

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.tweet import Tweet
from domain.ports.outbound.mongodb.tweet_repository_port import TweetRepositoryPort

from infrastructure.mongodb import db


class MongoTweetRepository(TweetRepositoryPort):
    def __init__(self, database: AsyncIOMotorDatabase = db):
        self._coll = database.get_collection("tweets")

    async def save(self, tweet: Tweet) -> str:
        """
        Insert a new tweet document and return by its id.
        """
        doc = self._entity_to_doc(tweet)
        result = await self._coll.insert_one(doc)
        return str(result.inserted_id)
    
    async def save_all(self, tweets: List[Tweet]) -> List[str]:
        """
        Batch insert multiple Tweet entities and return their IDs as strings.
        """
        if not tweets:
            return []

        docs = [self._entity_to_doc(tweet) for tweet in tweets]
        result = await self._coll.insert_many(docs)
        return [str(_id) for _id in result.inserted_ids]

    async def find_by_id(self, tweet_id: str) -> Optional[Tweet]:
        """
        Fetch one tweet by its id.
        """
        doc = await self._coll.find_one({"_id": ObjectId(tweet_id)})
        return self._doc_to_entity(doc) if doc else None

    async def find_by_generation_id(self, generation_id: str) -> List[Tweet]:
        """
        Fetch all tweets associated to a given tweet generation.
        """
        cursor = self._coll.find({"generationId": ObjectId(generation_id)})
        items: List[Tweet] = []
        async for doc in cursor:
            items.append(self._doc_to_entity(doc))
        return items

    async def update(self, tweet: Tweet) -> None:
        """
        Updates an existing tweet.
        """
        doc = self._entity_to_doc(tweet)
        await self._coll.update_one(
            {"_id": ObjectId(tweet.id)},
            {"$set": doc}
        )

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
            created_at=doc.get("createdAt", datetime.utcnow())
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
            "createdAt": tweet.created_at,
        }
        # Elimina campos con valor None
        return {k: v for k, v in doc.items() if v is not None}
