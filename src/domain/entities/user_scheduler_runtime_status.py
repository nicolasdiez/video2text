from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from bson import ObjectId


@dataclass
class UserSchedulerRuntimeStatus:
    """
    Entity that represents the runtime status of the scheduler for a given user.

    Notes:
      - This is an entity (mutable, identifiable) stored in its own collection.
    """

    id: Optional[ObjectId] = None                                   # Mongo _id
    user_id: ObjectId = field(default_factory=lambda: ObjectId())   # FK -> users._id

    # Pipeline running flags
    is_ingestion_pipeline_running: bool = False
    is_publishing_pipeline_running: bool = False
    is_stats_pipeline_running: bool = False
    is_embeddings_pipeline_running: bool = False

    # Ingestion timestamps
    last_ingestion_pipeline_started_at: Optional[datetime] = None
    last_ingestion_pipeline_finished_at: Optional[datetime] = None

    # Publishing timestamps
    last_publishing_pipeline_started_at: Optional[datetime] = None
    last_publishing_pipeline_finished_at: Optional[datetime] = None

    # Stats timestamps
    last_stats_pipeline_started_at: Optional[datetime] = None
    last_stats_pipeline_finished_at: Optional[datetime] = None
    
    # Embeddings timestamps
    last_embeddings_pipeline_started_at: Optional[datetime] = None
    last_embeddings_pipeline_finished_at: Optional[datetime] = None

    # Next scheduled runs
    next_scheduled_ingestion_pipeline_starting_at: Optional[datetime] = None
    next_scheduled_publishing_pipeline_starting_at: Optional[datetime] = None
    next_scheduled_stats_pipeline_starting_at: Optional[datetime] = None
    next_scheduled_embeddings_pipeline_starting_at: Optional[datetime] = None

    # Failure counters
    consecutive_failures_ingestion_pipeline: int = 0
    consecutive_failures_publishing_pipeline: int = 0
    consecutive_failures_stats_pipeline: int = 0
    consecutive_failures_embeddings_pipeline: int = 0

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        # Basic type and value validation
        if not isinstance(self.user_id, ObjectId):
            raise TypeError("user_id must be a bson.ObjectId")

        # Running flags
        if not isinstance(self.is_ingestion_pipeline_running, bool):
            raise TypeError("is_ingestion_pipeline_running must be a boolean")
        if not isinstance(self.is_publishing_pipeline_running, bool):
            raise TypeError("is_publishing_pipeline_running must be a boolean")
        if not isinstance(self.is_stats_pipeline_running, bool):
            raise TypeError("is_stats_pipeline_running must be a boolean")
        if not isinstance(self.is_embeddings_pipeline_running, bool):
            raise TypeError("is_embeddings_pipeline_running must be a boolean")

        # Failure counters
        if not isinstance(self.consecutive_failures_ingestion_pipeline, int) or self.consecutive_failures_ingestion_pipeline < 0:
            raise ValueError("consecutive_failures_ingestion_pipeline must be a non-negative integer")
        if not isinstance(self.consecutive_failures_publishing_pipeline, int) or self.consecutive_failures_publishing_pipeline < 0:
            raise ValueError("consecutive_failures_publishing_pipeline must be a non-negative integer")
        if not isinstance(self.consecutive_failures_stats_pipeline, int) or self.consecutive_failures_stats_pipeline < 0:
            raise ValueError("consecutive_failures_stats_pipeline must be a non-negative integer")
        if not isinstance(self.consecutive_failures_embeddings_pipeline, int) or self.consecutive_failures_stats_pipeline < 0:
            raise ValueError("consecutive_failures_embeddings_pipeline must be a non-negative integer")

        # Timestamps
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")
        if not isinstance(self.updated_at, datetime):
            raise TypeError("updated_at must be a datetime")
