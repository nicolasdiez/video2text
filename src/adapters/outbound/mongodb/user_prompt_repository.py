# src/adapters/outbound/mongodb/user_prompt_repository.py

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.user_prompt import (
    UserPrompt,
    PromptContent,
    TweetLengthPolicy,
    TweetLengthMode,
    TweetLengthUnit,
)
from domain.ports.outbound.mongodb.user_prompt_repository_port import UserPromptRepositoryPort
from infrastructure.mongodb import db


class MongoPromptRepository(UserPromptRepositoryPort):
    """
    MongoDB adapter for UserPromptRepositoryPort. Maps between UserPrompt entities and Mongo documents.
    """
    def __init__(self, database: AsyncIOMotorDatabase = db):    # TODO: eliminar el db por defecto y el import, que solo sea por inyección al constructor
        self._collection = database.get_collection("user_prompts")

    async def save(self, user_prompt: UserPrompt) -> str:
        doc = self._to_document(user_prompt)
        result = await self._collection.insert_one(doc)
        return str(result.inserted_id)

    async def find_by_id(self, user_prompt_id: str) -> Optional[UserPrompt]:
        raw = await self._collection.find_one({"_id": ObjectId(user_prompt_id)})
        return self._to_entity(raw) if raw else None

    async def find_by_user_id(self, user_id: str) -> List[UserPrompt]:
        cursor = self._collection.find({"userId": ObjectId(user_id)})
        return [self._to_entity(doc) async for doc in cursor]

    async def update(self, user_prompt: UserPrompt) -> None:
        """
        Update an existing UserPrompt document by its id.
        - Preserves createdAt.
        - Refreshes updatedAt to now.
        - Raises LookupError if the document does not exist.
        """
        if not user_prompt.id:
            raise ValueError("UserPrompt id is required for update")

        # Build doc from entity
        update_doc = self._to_document(user_prompt)

        # Never override createdAt when updating
        update_doc.pop("createdAt", None)

        # set updatedAt
        update_doc["updatedAt"] = datetime.utcnow()

        result = await self._collection.update_one(
            {"_id": ObjectId(user_prompt.id)},
            {"$set": update_doc}
        )

        if result.matched_count == 0:
            raise LookupError(f"UserPrompt {user_prompt.id} not found for update")

    async def delete(self, user_prompt_id: str) -> None:
        await self._collection.delete_one({"_id": ObjectId(user_prompt_id)})

    async def delete_all(self) -> int:
        res = await self._collection.delete_many({})
        return res.deleted_count

    def _to_entity(self, doc: dict) -> UserPrompt:
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

        return UserPrompt(
            id=str(doc["_id"]),
            user_id=str(doc["userId"]),
            master_prompt_id=str(doc["masterPromptId"]),
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

    def _to_document(self, user_prompt: UserPrompt) -> dict:
        """
        Map UserPrompt entity to MongoDB document (without _id).
        Omite None para no pisar campos con valores nulos accidentalmente.
        """
        doc = {
            "userId": ObjectId(user_prompt.user_id),
            "masterPromptId": ObjectId(user_prompt.master_prompt_id),
            "promptContent": {
                "systemMessage": user_prompt.prompt_content.system_message,
                "userMessage": user_prompt.prompt_content.user_message,
            },
            "languageOfThePrompt": user_prompt.language_of_the_prompt,
            "languageToGenerateTweets": user_prompt.language_to_generate_tweets,
            "createdAt": user_prompt.created_at,
            "updatedAt": user_prompt.updated_at,
        }

        # Include tweetLengthPolicy if present
        if getattr(user_prompt, "tweet_length_policy", None):
            tlp = user_prompt.tweet_length_policy
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
