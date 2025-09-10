# adapters/outbound/mongodb/prompt_repository.py

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.prompt import Prompt
from domain.ports.outbound.mongodb.prompt_repository_port import PromptRepositoryPort
from infrastructure.mongodb import db


class MongoPromptRepository(PromptRepositoryPort):
    """
    MongoDB adapter for PromptRepositoryPort. Maps between Prompt entities and Mongo documents.
    """
    def __init__(self, database: AsyncIOMotorDatabase = db):
        self._collection = database.get_collection("prompts")

    async def save(self, prompt: Prompt) -> str:
        doc = self._to_document(prompt)
        result = await self._collection.insert_one(doc)
        return str(result.inserted_id)

    async def find_by_id(self, prompt_id: str) -> Optional[Prompt]:
        raw = await self._collection.find_one({"_id": ObjectId(prompt_id)})
        return self._to_entity(raw) if raw else None

    async def find_by_user_id(self, user_id: str) -> List[Prompt]:
        cursor = self._collection.find({"userId": ObjectId(user_id)})
        return [self._to_entity(doc) async for doc in cursor]

    async def find_by_channel_id(self, channel_id: str) -> List[Prompt]:
        cursor = self._collection.find({"channelId": ObjectId(channel_id)})
        return [self._to_entity(doc) async for doc in cursor]
    
    async def find_by_user_and_channel(self, user_id: str, channel_id: str) -> Optional[Prompt]:
        """
        Retrieve a single Prompt by both user_id and channel_id.
        Returns None if not found.
        Raises ValueError if more than one Prompt exists for the same user and channel.
        """
        cursor = self._collection.find({
            "userId": ObjectId(user_id),
            "channelId": ObjectId(channel_id)
        })

        prompts = [self._to_entity(doc) async for doc in cursor]

        if not prompts:
            return None
        if len(prompts) > 1:
            raise ValueError(
                f"Multiple prompts found for user {user_id} and channel {channel_id}.""Expected exactly one."
            )

        return prompts[0]

    async def delete(self, prompt_id: str) -> None:
        await self._collection.delete_one({"_id": ObjectId(prompt_id)})

    def _to_entity(self, doc: dict) -> Prompt:
        return Prompt(
            id=str(doc["_id"]),
            user_id=str(doc["userId"]),
            channel_id=str(doc["channelId"]),
            text=doc["text"],
            language_of_the_text=doc["languageOfTheText"],
            language_to_generate_tweets=doc["languageToGenerateTweets"],
            max_tweets_to_generate_per_video=doc["maxTweetsToGeneratePerVideo"],
            created_at=doc.get("createdAt", datetime.utcnow()),
            updated_at=doc.get("updatedAt", datetime.utcnow())
        )

    def _to_document(self, prompt: Prompt) -> dict:
        doc = {
            "userId": ObjectId(prompt.user_id),
            "channelId": ObjectId(prompt.channel_id),
            "text": prompt.text,
            "languageOfTheText": prompt.language_of_the_text,
            "languageToGenerateTweets": prompt.language_to_generate_tweets,
            "maxTweetsToGeneratePerVideo": prompt.max_tweets_to_generate_per_video,
            "createdAt": prompt.created_at,
            "updatedAt": prompt.updated_at,
        }
        return {key: value for key, value in doc.items() if value is not None}

