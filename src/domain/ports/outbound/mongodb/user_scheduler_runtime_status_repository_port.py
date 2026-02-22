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
    async def update_by_user_id(self, user_id: str, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Apply a $set update with the provided fields to the runtime document identified by user_id.
        Returns the updated document, or None if no document matched.
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
        `fields` may be snake_case or camelCase.
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

    # ---------------------------------------------------------
    # INGESTION PIPELINE
    # ---------------------------------------------------------

    @abstractmethod
    async def mark_ingestion_started(self, user_id: UserId, started_at: Any) -> None:
        """
        Atomically mark ingestion pipeline as running and set last started timestamp.
        """
        raise NotImplementedError

    @abstractmethod
    async def mark_ingestion_finished(self, user_id: UserId, finished_at: Any, success: bool) -> None:
        """
        Atomically mark ingestion pipeline as finished.
        Reset or increment consecutiveFailuresIngestionPipeline accordingly.
        """
        raise NotImplementedError

    @abstractmethod
    async def increment_ingestion_failures(self, user_id: UserId, by: int = 1) -> None:
        """
        Atomically increment the consecutiveFailuresIngestionPipeline counter.
        """
        raise NotImplementedError

    @abstractmethod
    async def reset_ingestion_failures(self, user_id: UserId) -> None:
        """
        Reset consecutiveFailuresIngestionPipeline to 0.
        """
        raise NotImplementedError

    # ---------------------------------------------------------
    # PUBLISHING PIPELINE
    # ---------------------------------------------------------

    @abstractmethod
    async def mark_publishing_started(self, user_id: UserId, started_at: Any) -> None:
        """
        Atomically mark publishing pipeline as running and set last started timestamp.
        """
        raise NotImplementedError

    @abstractmethod
    async def mark_publishing_finished(self, user_id: UserId, finished_at: Any, success: bool) -> None:
        """
        Atomically mark publishing pipeline as finished.
        Reset or increment consecutiveFailuresPublishingPipeline accordingly.
        """
        raise NotImplementedError

    @abstractmethod
    async def increment_publishing_failures(self, user_id: UserId, by: int = 1) -> None:
        """
        Atomically increment the consecutiveFailuresPublishingPipeline counter.
        """
        raise NotImplementedError

    @abstractmethod
    async def reset_publishing_failures(self, user_id: UserId) -> None:
        """
        Reset consecutiveFailuresPublishingPipeline to 0.
        """
        raise NotImplementedError

    # ---------------------------------------------------------
    # STATS PIPELINE
    # ---------------------------------------------------------

    @abstractmethod
    async def mark_stats_started(self, user_id: UserId, started_at: Any) -> None:
        """
        Atomically mark stats pipeline as running and set last started timestamp.
        Should set isStatsPipelineRunning = True and update updated_at.
        """
        raise NotImplementedError

    @abstractmethod
    async def mark_stats_finished(self, user_id: UserId, finished_at: Any, success: bool) -> None:
        """
        Atomically mark stats pipeline as finished.
        If success=True: reset consecutiveFailuresStatsPipeline.
        If success=False: increment consecutiveFailuresStatsPipeline.
        Always update updated_at.
        """
        raise NotImplementedError

    @abstractmethod
    async def increment_stats_failures(self, user_id: UserId, by: int = 1) -> None:
        """
        Atomically increment the consecutiveFailuresStatsPipeline counter.
        """
        raise NotImplementedError

    @abstractmethod
    async def reset_stats_failures(self, user_id: UserId) -> None:
        """
        Reset consecutiveFailuresStatsPipeline to 0.
        """
        raise NotImplementedError
    
    # ---------------------------------------------------------
    # EMBEDDINGS PIPELINE
    # ---------------------------------------------------------

    @abstractmethod
    async def mark_embeddings_started(self, user_id: UserId, started_at: Any) -> None:
        """
        Atomically mark embeddings pipeline as running and set last started timestamp.
        Should set isEmbeddingsPipelineRunning = True and update updated_at.
        """
        raise NotImplementedError

    @abstractmethod
    async def mark_embeddings_finished(self, user_id: UserId, finished_at: Any, success: bool) -> None:
        """
        Atomically mark embeddings pipeline as finished.
        If success=True: reset consecutiveFailuresEmbeddingsPipeline.
        If success=False: increment consecutiveFailuresEmbeddingsPipeline.
        Always update updated_at.
        """
        raise NotImplementedError

    @abstractmethod
    async def increment_embeddings_failures(self, user_id: UserId, by: int = 1) -> None:
        """
        Atomically increment the consecutiveFailuresEmbeddingsPipeline counter.
        """
        raise NotImplementedError

    @abstractmethod
    async def reset_embeddings_failures(self, user_id: UserId) -> None:
        """
        Reset consecutiveFailuresEmbeddingsPipeline to 0.
        """
        raise NotImplementedError

