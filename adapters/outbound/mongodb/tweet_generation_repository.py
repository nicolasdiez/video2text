# adapters/outbound/mongo/tweet_generation_repository.py

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.tweet_generation import TweetGeneration, OpenAIRequest
from domain.ports.outbound.mongodb.tweet_generation_repository_port import (
    TweetGenerationRepositoryPort
)

# Reuso la conexión _db definida en el adaptador de videos
from adapters.outbound.mongodb.video_repository import _db


class MongoTweetGenerationRepository(TweetGenerationRepositoryPort):
    def __init__(self, db: AsyncIOMotorDatabase = _db):
        self._coll = db.get_collection("tweet_generations")

    async def save(self, tweet_generation: TweetGeneration) -> str:
        doc = self._entity_to_doc(tweet_generation)
        result = await self._coll.insert_one(doc)
        return str(result.inserted_id)

    async def find_by_id(self, tg_id: str) -> Optional[TweetGeneration]:
        doc = await self._coll.find_one({"_id": ObjectId(tg_id)})
        return self._doc_to_entity(doc) if doc else None

    async def find_by_video_id(self, video_id: str) -> List[TweetGeneration]:
        cursor = self._coll.find({"videoId": ObjectId(video_id)})
        items: List[TweetGeneration] = []
        async for doc in cursor:
            items.append(self._doc_to_entity(doc))
        return items

    def _doc_to_entity(self, doc: dict) -> TweetGeneration:
        req = doc["openaiRequest"]
        openai_req = OpenAIRequest(
            prompt=req["prompt"],
            model=req["model"],
            temperature=req["temperature"],
            max_tokens=req["maxTokens"]
        )
        return TweetGeneration(
            id=str(doc["_id"]),
            user_id=str(doc["userId"]),
            video_id=str(doc["videoId"]),
            openai_request=openai_req,
            generated_at=doc.get("generatedAt", datetime.utcnow())
        )

    def _entity_to_doc(self, tg: TweetGeneration) -> dict:
        return {
            "userId": ObjectId(tg.user_id),
            "videoId": ObjectId(tg.video_id),
            "openaiRequest": {
                "prompt": tg.openai_request.prompt,
                "model": tg.openai_request.model,
                "temperature": tg.openai_request.temperature,
                "maxTokens": tg.openai_request.max_tokens
            },
            "generatedAt": tg.generated_at
        }
