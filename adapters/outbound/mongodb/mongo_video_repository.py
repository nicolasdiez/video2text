# adapters/outbound/mongo/video_repository.py

import os
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from dataclasses import dataclass, field

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

from domain.entities.video import Video, TranscriptSegment
from domain.ports.outbound.mongodb.video_repository_port import VideoRepositoryPort

# ------------------------------------------------------------------------------
# 1) CARGA DE VARIABLES DE ENTORNO
# ------------------------------------------------------------------------------

load_dotenv()  # busca un .env en el cwd y lo carga en os.environ

MONGO_USER     = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST     = os.getenv("MONGO_HOST")
MONGO_DB       = os.getenv("MONGO_DB")

if not (MONGO_USER and MONGO_PASSWORD and MONGO_DB):
    raise RuntimeError("Faltan credenciales de Mongo en variables de entorno")

# URI de conexión para Motor (async) y PyMongo (sync ping)
_BASE_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}/{MONGO_DB}"
MONGO_URI_ASYNC = _BASE_URI + "?retryWrites=true&w=majority"
MONGO_URI_SYNC  = _BASE_URI + "?retryWrites=true&w=majority"

# ------------------------------------------------------------------------------
# 2) CLIENTES: Motor para operaciones async, PyMongo para ping test
# ------------------------------------------------------------------------------

# Cliente async
_motor_client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URI_ASYNC)
_db: AsyncIOMotorDatabase = _motor_client[MONGO_DB]

# Cliente sync solo para testear conexión
_sync_client = MongoClient(
    MONGO_URI_SYNC,
    server_api=ServerApi("1")
)

def ping_mongo_sync() -> None:
    """
    Ejecuta un ping de prueba usando PyMongo para verificar credenciales y red.
    """
    try:
        _sync_client.admin.command("ping")
        print("✅ Ping exitoso a MongoDB Atlas")
    except errors.PyMongoError as e:
        print(f"❌ Error en ping a MongoDB: {e}")

# descomentar la siguiente línea para testear al importar:
# ping_mongo_sync()

# ------------------------------------------------------------------------------
# 3) ADAPTADOR: implementación del puerto VideoRepositoryPort
# ------------------------------------------------------------------------------

class MongoVideoRepository(VideoRepositoryPort):
    def __init__(self, db: AsyncIOMotorDatabase = _db):
        self._coll = db.get_collection("videos")

    async def save_video(self, video: Video) -> str:
        doc = self._entity_to_doc(video)
        result = await self._coll.insert_one(doc)
        return str(result.inserted_id)

    async def find_by_id(self, video_id: str) -> Optional[Video]:
        doc = await self._coll.find_one({"_id": ObjectId(video_id)})
        return self._doc_to_entity(doc) if doc else None

    async def find_by_channel(
        self,
        channel_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Video]:
        cursor = (
            self._coll
            .find({"channelId": ObjectId(channel_id)})
            .sort("createdAt", -1)
            .skip(offset)
            .limit(limit)
        )
        videos: List[Video] = []
        async for doc in cursor:
            videos.append(self._doc_to_entity(doc))
        return videos

    async def find_videos_pending_tweets(self, limit: int = 50) -> List[Video]:
        cursor = self._coll.find({"tweetsGenerated": False}).limit(limit)
        videos: List[Video] = []
        async for doc in cursor:
            videos.append(self._doc_to_entity(doc))
        return videos

    async def update_video(self, video: Video) -> None:
        doc = self._entity_to_doc(video)
        await self._coll.update_one(
            {"_id": ObjectId(video.id)},
            {"$set": doc}
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
                {
                    "start": seg.start,
                    "duration": seg.duration,
                    "text": seg.text
                }
                for seg in video.transcript_segments
            ],
            "transcriptFetchedAt": video.transcript_fetched_at,
            "tweetsGenerated": video.tweets_generated,
            "createdAt": video.created_at,
            "updatedAt": video.updated_at,
        }
        # Quitar claves con valor None (p. ej. userId)
        return {k: v for k, v in doc.items() if v is not None}
