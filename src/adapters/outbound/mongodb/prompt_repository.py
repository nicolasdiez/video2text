# src/adapters/outbound/mongodb/prompt_repository.py

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.prompt import (
    Prompt,
    PromptContent,
    TweetLengthPolicy,
    TweetLengthMode,
    TweetLengthUnit,
)
from domain.ports.outbound.mongodb.prompt_repository_port import PromptRepositoryPort
from infrastructure.mongodb import db


class MongoPromptRepository(PromptRepositoryPort):
    """
    MongoDB adapter for PromptRepositoryPort. Maps between Prompt entities and Mongo documents.
    """
    def __init__(self, database: AsyncIOMotorDatabase = db):    # TODO: eliminar el db por defecto y el import, que solo sea por inyección al constructor
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
    
    async def find_by_user_and_channel(self, user_id: str, channel_id: str) -> List[Prompt]:
        """
        Retrieve all Prompts for a given user_id and channel_id.
        Returns an empty list if none found. Does not raise if multiple prompts exist.
        """
        # Build query with safe ObjectId conversion when possible
        try:
            user_q = ObjectId(user_id)
        except Exception:
            user_q = user_id

        try:
            channel_q = ObjectId(channel_id)
        except Exception:
            channel_q = channel_id

        cursor = self._collection.find({
            "userId": user_q,
            "channelId": channel_q
        })

        prompts = [self._to_entity(doc) async for doc in cursor]
        return prompts


    async def update(self, prompt: Prompt) -> None:
        """
        Update an existing Prompt document by its id.
        - Preserves createdAt.
        - Refreshes updatedAt to now.
        - Raises LookupError if the document does not exist.
        """
        if not prompt.id:
            raise ValueError("Prompt id is required for update")

        # Build doc from entity
        update_doc = self._to_document(prompt)

        # Never override createdAt when updating
        update_doc.pop("createdAt", None)

        # set updatedAt
        update_doc["updatedAt"] = datetime.utcnow()

        result = await self._collection.update_one(
            {"_id": ObjectId(prompt.id)},
            {"$set": update_doc}
        )

        if result.matched_count == 0:
            raise LookupError(f"Prompt {prompt.id} not found for update")

    async def delete(self, prompt_id: str) -> None:
        await self._collection.delete_one({"_id": ObjectId(prompt_id)})

    async def delete_all(self) -> int:
        res = await self._collection.delete_many({})
        return res.deleted_count

    def _to_entity(self, doc: dict) -> Prompt:
        # Parse tweetLengthPolicy if present
        tlp_doc = doc.get("tweetLengthPolicy")
        tweet_length_policy = None
        if isinstance(tlp_doc, dict):
            # Safe parsing with defaults
            mode_val = tlp_doc.get("mode")
            try:
                mode = TweetLengthMode(mode_val) if mode_val else TweetLengthMode.FIXED
            except ValueError:
                mode = TweetLengthMode.FIXED

            unit_val = tlp_doc.get("unit")
            try:
                unit = TweetLengthUnit(unit_val) if unit_val else TweetLengthUnit.CHARS
            except ValueError:
                unit = TweetLengthUnit.CHARS

            tweet_length_policy = TweetLengthPolicy(
                mode=mode,
                min_length=tlp_doc.get("minLength"),
                max_length=tlp_doc.get("maxLength"),
                target_length=tlp_doc.get("targetLength"),
                tolerance_percent=tlp_doc.get("tolerancePercent", 10),
                unit=unit,
            )

        return Prompt(
            id=str(doc["_id"]),
            user_id=str(doc["userId"]),
            channel_id=str(doc["channelId"]),
            prompt_content=PromptContent(
                system_message=doc.get("promptContent", {}).get("systemMessage", ""),
                user_message=doc.get("promptContent", {}).get("userMessage", "")
            ),
            language_of_the_prompt=doc.get("languageOfThePrompt", ""),
            language_to_generate_tweets=doc.get("languageToGenerateTweets", ""),
            tweet_length_policy=tweet_length_policy,
            created_at=doc.get("createdAt", datetime.utcnow()),
            updated_at=doc.get("updatedAt", datetime.utcnow())
        )

    def _to_document(self, prompt: Prompt) -> dict:
        """
        Map Prompt entity to MongoDB document (without _id).
        Omite None para no pisar campos con valores nulos accidentalmente.
        """
        doc = {
            "userId": ObjectId(prompt.user_id),
            "channelId": ObjectId(prompt.channel_id),
            "promptContent": {
                "systemMessage": prompt.prompt_content.system_message,
                "userMessage": prompt.prompt_content.user_message,
            },
            "languageOfThePrompt": prompt.language_of_the_prompt,
            "languageToGenerateTweets": prompt.language_to_generate_tweets,
            "createdAt": prompt.created_at,
            "updatedAt": prompt.updated_at,
        }

        # Include tweetLengthPolicy if present
        if getattr(prompt, "tweet_length_policy", None):
            tlp = prompt.tweet_length_policy
            tlp_doc = {
                "mode": tlp.mode.value if hasattr(tlp.mode, "value") else str(tlp.mode),
                "minLength": tlp.min_length,
                "maxLength": tlp.max_length,
                "targetLength": tlp.target_length,
                "tolerancePercent": tlp.tolerance_percent,
                "unit": tlp.unit.value if hasattr(tlp.unit, "value") else str(tlp.unit),
            }
            # remove None values from tlp_doc
            tlp_doc = {k: v for k, v in tlp_doc.items() if v is not None}
            if tlp_doc:
                doc["tweetLengthPolicy"] = tlp_doc

        return {key: value for key, value in doc.items() if value is not None}
