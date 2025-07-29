# adapters/outbound/mongodb/video_repository.py

from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from domain.entities.video import Video, TranscriptSegment
from domain.ports.outbound.mongodb.video_repository_port import VideoRepositoryPort

# Importa sólo la instancia de DB, no la configuración
from infrastructure.mongodb import db  


class MongoVideoRepository(VideoRepositoryPort):
    def __init__(self, database=None):
        self._coll = (database or db).get_collection("videos")

    async def save_video(self, video: Video) -> str:
        doc = self._entity_to_doc(video)
        result = await self._coll.insert_one(doc)
        return str(result.inserted_id)

    async def find_by_id(self, video_id: str) -> Optional[Video]:
        doc = await self._coll.find_one({"_id": ObjectId(video_id)})
        return self._doc_to_entity(doc) if doc else None

    async def find_by_channel(
        self, channel_id: str, limit: int = 50, offset: int = 0
    ) -> List[Video]:
        cursor = (
            self._coll
            .find({"channelId": ObjectId(channel_id)})
            .sort("createdAt", -1)
            .skip(offset)
            .limit(limit)
        )
        return [self._doc_to_entity(doc) async for doc in cursor]

    async def find_videos_pending_tweets(self, limit: int = 50) -> List[Video]:
        cursor = self._coll.find({"tweetsGenerated": False}).limit(limit)
        return [self._doc_to_entity(doc) async for doc in cursor]

    async def update_video(self, video: Video) -> None:
        doc = self._entity_to_doc(video)
        await self._coll.update_one(
            {"_id": ObjectId(video.id)}, {"$set": doc}
        )

    async def delete_video(self, video_id: str) -> None:
        await self._coll.delete_one({"_id": ObjectId(video_id)})

    def _doc_to_entity(self, doc: dict) -> Video:
        return Video(
            id=str(doc["_id"]),
            user_id=str(doc.get("userId")) if doc.get("userId") else None,
            channel_id=str(doc["channelId"]),
            youtube_video_id=doc["youtubeVideoId"],
            title=doc["title"],
            url=doc["url"],
            transcript=doc.get("transcript", ""),
            transcript_segments=[
                TranscriptSegment(**seg)
                for seg in doc.get("transcriptSegments", [])
            ],
            transcript_fetched_at=doc.get("transcriptFetchedAt"),
            tweets_generated=doc.get("tweetsGenerated", False),
            created_at=doc.get("createdAt", datetime.utcnow()),
            updated_at=doc.get("updatedAt", datetime.utcnow())
        )

    def _entity_to_doc(self, video: Video) -> dict:
        doc = {
            "userId": ObjectId(video.user_id) if video.user_id else None,
            "channelId": ObjectId(video.channel_id),
            "youtubeVideoId": video.youtube_video_id,
            "title": video.title,
            "url": video.url,
            "transcript": video.transcript,
            "transcriptSegments": [
                {"start": seg.start, "duration": seg.duration, "text": seg.text}
                for seg in video.transcript_segments
            ],
            "transcriptFetchedAt": video.transcript_fetched_at,
            "tweetsGenerated": video.tweets_generated,
            "createdAt": video.created_at,
            "updatedAt": video.updated_at,
        }
        # Elimina claves None
        return {k: v for k, v in doc.items() if v is not None}
