# src/adapters/outbound/mongodb/mongo_master_prompt_repository.py

from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.master_prompt import MasterPrompt
from domain.entities.user_prompt import PromptContent, TweetLengthPolicy
from domain.ports.outbound.mongodb.master_prompt_repository_port import MasterPromptRepositoryPort


class MongoMasterPromptRepository(MasterPromptRepositoryPort):

    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database["master_prompts"]

    # -----------------------------
    # Helpers
    # -----------------------------
    def _document_to_entity(self, doc: Dict[str, Any]) -> MasterPrompt:
        """
        Convert a MongoDB document into a MasterPrompt domain entity.
        """
        return MasterPrompt(
            id=str(doc["_id"]),
            category=doc["category"],
            subcategory=doc["subcategory"],
            prompt_content=PromptContent(
                system_message=doc["promptContent"]["systemMessage"],
                user_message=doc["promptContent"]["userMessage"],
            ),
            language_of_the_prompt=doc["languageOfThePrompt"],
            language_to_generate_tweets=doc["languageToGenerateTweets"],
            tweet_length_policy=TweetLengthPolicy(
                mode=doc["tweetLengthPolicy"]["mode"],
                min_length=doc["tweetLengthPolicy"].get("minLength"),
                max_length=doc["tweetLengthPolicy"].get("maxLength"),
                target_length=doc["tweetLengthPolicy"].get("targetLength"),
                tolerance_percent=doc["tweetLengthPolicy"].get("tolerancePercent", 10),
                unit=doc["tweetLengthPolicy"].get("unit", "chars"),
            ) if doc.get("tweetLengthPolicy") else None,
            created_at=doc["createdAt"],
            updated_at=doc["updatedAt"],
        )

    def _entity_to_document(self, entity: MasterPrompt) -> Dict[str, Any]:
        """
        Convert a MasterPrompt domain entity into a MongoDB document.
        """
        return {
            "category": entity.category,
            "subcategory": entity.subcategory,
            "promptContent": {
                "systemMessage": entity.prompt_content.system_message,
                "userMessage": entity.prompt_content.user_message,
            },
            "languageOfThePrompt": entity.language_of_the_prompt,
            "languageToGenerateTweets": entity.language_to_generate_tweets,
            "tweetLengthPolicy": (
                {
                    "mode": entity.tweet_length_policy.mode,
                    "minLength": entity.tweet_length_policy.min_length,
                    "maxLength": entity.tweet_length_policy.max_length,
                    "targetLength": entity.tweet_length_policy.target_length,
                    "tolerancePercent": entity.tweet_length_policy.tolerance_percent,
                    "unit": entity.tweet_length_policy.unit,
                }
                if entity.tweet_length_policy
                else None
            ),
            "createdAt": entity.created_at,
            "updatedAt": entity.updated_at,
        }

    # -----------------------------
    # CRUD methods
    # -----------------------------
    async def find_by_id(self, master_prompt_id: ObjectId) -> Optional[MasterPrompt]:
        doc = await self.collection.find_one({"_id": ObjectId(master_prompt_id)})
        return self._document_to_entity(doc) if doc else None

    async def find_all(self) -> List[MasterPrompt]:
        cursor = self.collection.find({})
        docs = await cursor.to_list(length=None)
        return [self._document_to_entity(doc) for doc in docs]

    async def find_by_category(self, category: str) -> List[MasterPrompt]:
        cursor = self.collection.find({"category": category})
        docs = await cursor.to_list(length=None)
        return [self._document_to_entity(doc) for doc in docs]

    async def insert_one(self, master_prompt: MasterPrompt) -> MasterPrompt:
        payload = self._entity_to_document(master_prompt)
        result = await self.collection.insert_one(payload)
        master_prompt.id = str(result.inserted_id)
        return master_prompt

    async def update_by_id(self, master_prompt_id: ObjectId, update_data: Dict[str, Any]) -> Optional[MasterPrompt]:
        doc = await self.collection.find_one_and_update(
            {"_id": ObjectId(master_prompt_id)},
            {"$set": update_data},
            return_document=True
        )
        return self._document_to_entity(doc) if doc else None

    async def delete_by_id(self, master_prompt_id: ObjectId) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(master_prompt_id)})
        return result.deleted_count == 1
