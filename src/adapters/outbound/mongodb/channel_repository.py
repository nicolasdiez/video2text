# src/adapters/outbound/mongodb/channel_repository.py

from datetime import datetime
from typing import List, Optional, Any, Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.channel import Channel
from domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from infrastructure.mongodb import db


class MongoChannelRepository(ChannelRepositoryPort):
    """
    MongoDB adapter for ChannelRepositoryPort. Maps between Channel entities and Mongo documents.
    """

    def __init__(self, database: AsyncIOMotorDatabase = db):
        # Use the shared `db` instance from infrastructure.mongodb
        self._collection = database.get_collection("channels")

    async def save(self, channel: Channel) -> str:
        """
        Insert a new channel document and return its ID.
        """
        doc = self._to_document(channel)
        result = await self._collection.insert_one(doc)
        return str(result.inserted_id)

    async def find_by_id(self, channel_id: str) -> Optional[Channel]:
        """
        Fetch one channel by its ObjectId.
        """
        raw = await self._collection.find_one({"_id": ObjectId(channel_id)})
        return self._to_entity(raw) if raw else None

    async def find_by_user_id(self, user_id: str) -> List[Channel]:
        """
        Return all channels for a given user.
        """
        cursor = self._collection.find({"userId": ObjectId(user_id)})
        return [self._to_entity(doc) async for doc in cursor]

    async def find_by_youtube_channel_id(self, youtube_channel_id: str) -> Optional[Channel]:
        """
        Fetch a single channel by its YouTube channel identifier.
        """
        raw = await self._collection.find_one({"youtubeChannelId": youtube_channel_id})
        return self._to_entity(raw) if raw else None

    async def find_by_selected_prompt_id(self, prompt_id: str) -> List[Channel]: 
        """
        Retrieve channels that reference the given user prompt ID in selectedPromptId.
        """
        cursor = self._collection.find({"selectedPromptId": ObjectId(prompt_id)})
        return [self._to_entity(doc) async for doc in cursor]

    async def find_all(self) -> List[Channel]:
        """
        Retrieve all channels.
        """
        cursor = self._collection.find({})
        return [self._to_entity(doc) async for doc in cursor]

    async def update(self, channel: Channel) -> None:
        """
        Replace fields of an existing channel document.
        """
        doc = self._to_document(channel)
        await self._collection.update_one(
            {"_id": ObjectId(channel.id)},
            {"$set": doc}
        )

    async def update_by_id(self, channel_id: ObjectId, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a channel document by its ID and return the updated document.
        Note: update_data is expected to be a Mongo-style partial document (fields already mapped to DB keys).
        """
        result = await self._collection.find_one_and_update(
            {"_id": channel_id},
            {"$set": update_data},
            return_document=True  # keep existing behavior; motor may accept this as truthy to return updated doc
        )
        return result

    async def delete(self, channel_id: str) -> None:
        """
        Remove a channel document by ID.
        """
        await self._collection.delete_one({"_id": ObjectId(channel_id)})

    async def delete_all(self) -> int:
        """
        Delete all documents in channels collection. Returns number deleted.
        """
        res = await self._collection.delete_many({})
        return res.deleted_count

    def _to_entity(self, doc: dict) -> Channel:
        """
        Convert a Mongo document into a Channel entity.
        """
        return Channel(
            id=str(doc["_id"]),
            user_id=str(doc["userId"]),
            youtube_channel_id=doc["youtubeChannelId"],
            selected_prompt_id=str(doc.get("selectedPromptId")) if doc.get("selectedPromptId") is not None else None,
            title=doc["title"],
            polling_interval=doc.get("pollingInterval"),
            max_videos_to_fetch_from_channel=doc.get("maxVideosToFetchFromChannel"),
            tweets_to_generate_per_video=doc.get("tweetsToGeneratePerVideo"),
            last_polled_at=doc.get("lastPolledAt"),
            created_at=doc.get("createdAt", datetime.utcnow()),
            updated_at=doc.get("updatedAt", datetime.utcnow())
        )

    def _to_document(self, channel: Channel) -> dict:
        """
        Convert a Channel entity into a Mongo document. Filters out None values.
        Converts string IDs to ObjectId where appropriate.
        """
        doc: Dict[str, Any] = {
            "userId": ObjectId(channel.user_id) if channel.user_id else None,
            "youtubeChannelId": channel.youtube_channel_id,
            "selectedPromptId": ObjectId(channel.selected_prompt_id) if channel.selected_prompt_id else None,
            "title": channel.title,
            "pollingInterval": channel.polling_interval,
            "maxVideosToFetchFromChannel": channel.max_videos_to_fetch_from_channel,
            "tweetsToGeneratePerVideo": channel.tweets_to_generate_per_video,
            "lastPolledAt": channel.last_polled_at,
            "createdAt": channel.created_at,
            "updatedAt": channel.updated_at,
        }
        # Remove keys with None values so we don't overwrite existing fields unintentionally
        return {key: value for key, value in doc.items() if value is not None}
