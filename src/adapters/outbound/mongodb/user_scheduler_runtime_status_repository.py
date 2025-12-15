# src/adapters/outbound/mongodb/user_scheduler_runtime_status_repository.py

from datetime import datetime
from typing import Optional, List, Dict, Any, Union

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone

from domain.entities.user_scheduler_runtime_status import UserSchedulerRuntimeStatus
from domain.ports.outbound.mongodb.user_scheduler_runtime_status_repository_port import UserSchedulerRuntimeStatusRepositoryPort

# Type alias for user id inputs
UserId = Union[str, ObjectId]


def _to_object_id(value: UserId) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    return ObjectId(value)


def _snake_to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class MongoUserSchedulerRuntimeStatusRepository(UserSchedulerRuntimeStatusRepositoryPort):
    """
    MongoDB implementation for UserSchedulerRuntimeStatus repository.
    Stores documents in collection 'user_scheduler_runtime_status' using camelCase keys.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        self._coll = database.get_collection("user_scheduler_runtime_status")

    # -----------------------
    # Mapping helpers
    # -----------------------
    def _doc_to_entity(self, doc: Dict[str, Any]) -> UserSchedulerRuntimeStatus:
        if not doc:
            return None  # type: ignore

        return UserSchedulerRuntimeStatus(
            id=doc.get("_id"),
            user_id=doc.get("userId"),
            is_ingestion_pipeline_running=bool(doc.get("isIngestionPipelineRunning", False)),
            is_publishing_pipeline_running=bool(doc.get("isPublishingPipelineRunning", False)),
            last_ingestion_pipeline_started_at=doc.get("lastIngestionPipelineStartedAt"),
            last_ingestion_pipeline_finished_at=doc.get("lastIngestionPipelineFinishedAt"),
            last_publishing_pipeline_started_at=doc.get("lastPublishingPipelineStartedAt"),
            last_publishing_pipeline_finished_at=doc.get("lastPublishingPipelineFinishedAt"),
            next_scheduled_ingestion_pipeline_starting_at=doc.get("nextScheduledIngestionPipelineStartingAt"),
            next_scheduled_publishing_pipeline_starting_at=doc.get("nextScheduledPublishingPipelineStartingAt"),
            consecutive_failures_ingestion_pipeline=int(doc.get("consecutiveFailuresIngestionPipeline", 0)),
            consecutive_failures_publishing_pipeline=int(doc.get("consecutiveFailuresPublishingPipeline", 0)),
            created_at=doc.get("createdAt") or datetime.utcnow(),
            updated_at=doc.get("updatedAt") or datetime.utcnow(),
        )

    def _entity_to_doc(self, ent: UserSchedulerRuntimeStatus) -> Dict[str, Any]:
        doc: Dict[str, Any] = {
            "userId": ent.user_id,
            "isIngestionPipelineRunning": ent.is_ingestion_pipeline_running,
            "isPublishingPipelineRunning": ent.is_publishing_pipeline_running,
            "lastIngestionPipelineStartedAt": ent.last_ingestion_pipeline_started_at,
            "lastIngestionPipelineFinishedAt": ent.last_ingestion_pipeline_finished_at,
            "lastPublishingPipelineStartedAt": ent.last_publishing_pipeline_started_at,
            "lastPublishingPipelineFinishedAt": ent.last_publishing_pipeline_finished_at,
            "nextScheduledIngestionPipelineStartingAt": ent.next_scheduled_ingestion_pipeline_starting_at,
            "nextScheduledPublishingPipelineStartingAt": ent.next_scheduled_publishing_pipeline_starting_at,
            "consecutiveFailuresIngestionPipeline": ent.consecutive_failures_ingestion_pipeline,
            "consecutiveFailuresPublishingPipeline": ent.consecutive_failures_publishing_pipeline,
            "createdAt": ent.created_at,
            "updatedAt": ent.updated_at,
        }
        # remove None values to keep documents compact
        return {k: v for k, v in doc.items() if v is not None}

    # -----------------------
    # CRUD + list
    # -----------------------
    async def get_by_user_id(self, user_id: UserId) -> Optional[UserSchedulerRuntimeStatus]:
        oid = _to_object_id(user_id)
        doc = await self._coll.find_one({"userId": oid})
        return self._doc_to_entity(doc) if doc else None
        
    async def update_by_user_id(self, user_id: str, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update the runtime document for userId using $set with the provided fields.
        If 'updatedAt' is not provided in update, add it automatically.
        Returns the updated document, or None if no document matched.
        """
        # copy update to avoid mutating caller's dict
        update_payload = dict(update)
        if "updatedAt" not in update_payload:
            update_payload["updatedAt"] = datetime.now(timezone.utc)

        result = await self._coll.update_one({"userId": user_id}, {"$set": update_payload})
        if result.matched_count == 0:
            return None

        updated_doc = await self._coll.find_one({"userId": user_id})
        return updated_doc

    async def create(self, status: UserSchedulerRuntimeStatus) -> ObjectId:
        now = datetime.utcnow()
        status.created_at = now
        status.updated_at = now
        doc = self._entity_to_doc(status)
        res = await self._coll.insert_one(doc)
        return res.inserted_id

    async def upsert(self, status: UserSchedulerRuntimeStatus) -> None:
        now = datetime.utcnow()
        status.updated_at = now
        doc = self._entity_to_doc(status)
        # Upsert by userId to ensure one document per user
        await self._coll.update_one(
            {"userId": status.user_id},
            {"$set": doc, "$setOnInsert": {"createdAt": status.created_at or now}},
            upsert=True
        )

    async def update_fields(self, user_id: UserId, fields: Dict[str, Any]) -> None:
        """
        Accepts fields in snake_case or camelCase. Converts snake_case keys to camelCase.
        Always updates updatedAt.
        """
        if not fields:
            return
        oid = _to_object_id(user_id)
        db_fields: Dict[str, Any] = {}
        for k, v in fields.items():
            key = k if k[0].islower() and ("_" not in k) and k[0].isalpha() and k[0] == k else _snake_to_camel(k)
            db_fields[key] = v
        db_fields["updatedAt"] = datetime.utcnow()
        await self._coll.update_one({"userId": oid}, {"$set": db_fields}, upsert=False)

    async def delete_by_user_id(self, user_id: UserId) -> None:
        oid = _to_object_id(user_id)
        await self._coll.delete_one({"userId": oid})

    async def list_all(self, limit: Optional[int] = None) -> List[UserSchedulerRuntimeStatus]:
        cursor = self._coll.find({})
        if limit:
            cursor = cursor.limit(limit)
        docs = await cursor.to_list(length=limit or 1000)
        return [self._doc_to_entity(d) for d in docs]

    # -----------------------
    # Convenience atomic operations
    # -----------------------
    async def mark_ingestion_started(self, user_id: UserId, started_at: Any) -> None:
        oid = _to_object_id(user_id)
        await self._coll.update_one(
            {"userId": oid},
            {
                "$set": {
                    "isIngestionPipelineRunning": True,
                    "lastIngestionPipelineStartedAt": started_at,
                    "updatedAt": datetime.utcnow()
                }
            },
            upsert=True
        )

    async def mark_ingestion_finished(self, user_id: UserId, finished_at: Any, success: bool) -> None:
        oid = _to_object_id(user_id)
        if success:
            update = {
                "$set": {
                    "isIngestionPipelineRunning": False,
                    "lastIngestionPipelineFinishedAt": finished_at,
                    "consecutiveFailuresIngestionPipeline": 0,
                    "updatedAt": datetime.utcnow()
                }
            }
        else:
            update = {
                "$set": {
                    "isIngestionPipelineRunning": False,
                    "lastIngestionPipelineFinishedAt": finished_at,
                    "updatedAt": datetime.utcnow()
                },
                "$inc": {"consecutiveFailuresIngestionPipeline": 1}
            }
        await self._coll.update_one({"userId": oid}, update, upsert=True)

    async def mark_publishing_started(self, user_id: UserId, started_at: Any) -> None:
        oid = _to_object_id(user_id)
        await self._coll.update_one(
            {"userId": oid},
            {
                "$set": {
                    "isPublishingPipelineRunning": True,
                    "lastPublishingPipelineStartedAt": started_at,
                    "updatedAt": datetime.utcnow()
                }
            },
            upsert=True
        )

    async def mark_publishing_finished(self, user_id: UserId, finished_at: Any, success: bool) -> None:
        oid = _to_object_id(user_id)
        if success:
            update = {
                "$set": {
                    "isPublishingPipelineRunning": False,
                    "lastPublishingPipelineFinishedAt": finished_at,
                    "consecutiveFailuresPublishingPipeline": 0,
                    "updatedAt": datetime.utcnow()
                }
            }
        else:
            update = {
                "$set": {
                    "isPublishingPipelineRunning": False,
                    "lastPublishingPipelineFinishedAt": finished_at,
                    "updatedAt": datetime.utcnow()
                },
                "$inc": {"consecutiveFailuresPublishingPipeline": 1}
            }
        await self._coll.update_one({"userId": oid}, update, upsert=True)

    async def increment_ingestion_failures(self, user_id: UserId, by: int = 1) -> None:
        oid = _to_object_id(user_id)
        await self._coll.update_one(
            {"userId": oid},
            {"$inc": {"consecutiveFailuresIngestionPipeline": int(by)}, "$set": {"updatedAt": datetime.utcnow()}},
            upsert=True
        )

    async def reset_ingestion_failures(self, user_id: UserId) -> None:
        oid = _to_object_id(user_id)
        await self._coll.update_one(
            {"userId": oid},
            {"$set": {"consecutiveFailuresIngestionPipeline": 0, "updatedAt": datetime.utcnow()}},
            upsert=False
        )

    async def increment_publishing_failures(self, user_id: UserId, by: int = 1) -> None:
        oid = _to_object_id(user_id)
        await self._coll.update_one(
            {"userId": oid},
            {"$inc": {"consecutiveFailuresPublishingPipeline": int(by)}, "$set": {"updatedAt": datetime.utcnow()}},
            upsert=True
        )

    async def reset_publishing_failures(self, user_id: UserId) -> None:
        oid = _to_object_id(user_id)
        await self._coll.update_one(
            {"userId": oid},
            {"$set": {"consecutiveFailuresPublishingPipeline": 0, "updatedAt": datetime.utcnow()}},
            upsert=False
        )
