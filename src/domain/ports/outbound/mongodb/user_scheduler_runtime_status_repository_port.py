# src/domain/ports/outbound/mongodb/user_scheduler_runtime_status_repository_port.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union

from bson import ObjectId

from domain.entities.user_scheduler_runtime_status import UserSchedulerRuntimeStatus


UserId = Union[str, ObjectId]


class UserSchedulerRuntimeStatusRepositoryPort(ABC):
    """
    Hexagonal outbound port (repository interface) for persisting and
    manipulating UserSchedulerRuntimeStatus entities in MongoDB.

    All methods are async because the concrete adapter will use an async
    MongoDB driver (motor). Implementations should perform minimal
    validation and prefer atomic updates (upsert / $set / $inc) where
    appropriate to avoid race conditions.
    """

    @abstractmethod
    async def get_by_user_id(self, user_id: UserId) -> Optional[UserSchedulerRuntimeStatus]:
        """
        Retrieve the runtime status entity for the given user_id.
        Return None if no document exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def create(self, status: UserSchedulerRuntimeStatus) -> ObjectId:
        """
        Insert a new UserSchedulerRuntimeStatus document.
        Return the inserted ObjectId.
        """
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, status: UserSchedulerRuntimeStatus) -> None:
        """
        Upsert the provided status by user_id (create if missing, replace or set fields otherwise).
        Should update `updated_at` automatically.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_fields(self, user_id: UserId, fields: Dict[str, Any]) -> None:
        """
        Atomically update specific fields on the user's runtime status document.
        `fields` should contain the document keys (snake_case or the repository's chosen mapping).
        Implementations should set `updated_at` to now.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_by_user_id(self, user_id: UserId) -> None:
        """
        Delete the runtime status document for the given user_id.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, limit: Optional[int] = None) -> List[UserSchedulerRuntimeStatus]:
        """
        Return all runtime status documents, optionally limited.
        """
        raise NotImplementedError

    # Convenience atomic operations commonly needed by scheduler logic

    @abstractmethod
    async def mark_ingestion_started(self, user_id: UserId, started_at: Any) -> None:
        """
        Atomically mark ingestion pipeline as running and set last started timestamp.
        Should set isIngestionPipelineRunning = True, lastIngestionPipelineStartedAt = started_at,
        and update updated_at.
        """
        raise NotImplementedError

    @abstractmethod
    async def mark_ingestion_finished(self, user_id: UserId, finished_at: Any, success: bool) -> None:
        """
        Atomically mark ingestion pipeline as finished.
        If success is True, set isIngestionPipelineRunning = False, lastIngestionPipelineFinishedAt = finished_at,
        and reset consecutiveFailuresIngestionPipeline to 0.
        If success is False, increment consecutiveFailuresIngestionPipeline by 1 and set lastIngestionPipelineFinishedAt.
        Always update updated_at.
        """
        raise NotImplementedError

    @abstractmethod
    async def mark_publishing_started(self, user_id: UserId, started_at: Any) -> None:
        """
        Atomically mark publishing pipeline as running and set last started timestamp.
        """
        raise NotImplementedError

    @abstractmethod
    async def mark_publishing_finished(self, user_id: UserId, finished_at: Any, success: bool) -> None:
        """
        Atomically mark publishing pipeline as finished. Behavior mirrors mark_ingestion_finished.
        """
        raise NotImplementedError

    @abstractmethod
    async def increment_ingestion_failures(self, user_id: UserId, by: int = 1) -> None:
        """
        Atomically increment the consecutiveFailuresIngestionPipeline counter by `by`.
        """
        raise NotImplementedError

    @abstractmethod
    async def reset_ingestion_failures(self, user_id: UserId) -> None:
        """
        Atomically reset consecutiveFailuresIngestionPipeline to 0.
        """
        raise NotImplementedError
