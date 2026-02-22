# src/domain/value_objects/scheduler_config.py

from dataclasses import dataclass, field

@dataclass(frozen=True)     # value object = inmutable = frozen
class SchedulerConfig:
    """
    Value Object representing scheduler configuration.
    Immutable and validated at construction.

    Fields:
      - ingestion_pipeline_frequency_minutes: int >= 0
      - publishing_pipeline_frequency_minutes: int >= 0
      - stats_pipeline_frequency_minutes: int >= 0
      - is_ingestion_pipeline_enabled: bool
      - is_publishing_pipeline_enabled: bool
      - is_stats_pipeline_enabled: bool
    """
    ingestion_pipeline_frequency_minutes: int   = field(default=10)
    publishing_pipeline_frequency_minutes: int  = field(default=10)
    stats_pipeline_frequency_minutes: int       = field(default=10)
    embeddings_pipeline_frequency_minutes: int       = field(default=10)
    is_ingestion_pipeline_enabled: bool         = field(default=True)
    is_publishing_pipeline_enabled: bool        = field(default=True)
    is_stats_pipeline_enabled: bool             = field(default=True)
    is_embeddigns_pipeline_enabled: bool             = field(default=True)

    def __post_init__(self):
        if not isinstance(self.ingestion_pipeline_frequency_minutes, int):
            raise TypeError("ingestion_pipeline_frequency_minutes must be an integer")
        if not isinstance(self.publishing_pipeline_frequency_minutes, int):
            raise TypeError("publishing_pipeline_frequency_minutes must be an integer")
        if not isinstance(self.stats_pipeline_frequency_minutes, int):
            raise TypeError("stats_pipeline_frequency_minutes must be an integer")
        if not isinstance(self.embeddings_pipeline_frequency_minutes, int):
            raise TypeError("embeddings_pipeline_frequency_minutes must be an integer")
        if self.ingestion_pipeline_frequency_minutes < 0:
            raise ValueError("ingestion_pipeline_frequency_minutes cannot be negative")
        if self.publishing_pipeline_frequency_minutes < 0:
            raise ValueError("publishing_pipeline_frequency_minutes cannot be negative")
        if self.stats_pipeline_frequency_minutes < 0:
            raise ValueError("stats_pipeline_frequency_minutes cannot be negative")
        if self.embeddings_pipeline_frequency_minutes < 0:
            raise ValueError("embeddings_pipeline_frequency_minutes cannot be negative")    
        if not isinstance(self.is_ingestion_pipeline_enabled, bool):
            raise TypeError("is_ingestion_pipeline_enabled must be a boolean")
        if not isinstance(self.is_publishing_pipeline_enabled, bool):
            raise TypeError("is_publishing_pipeline_enabled must be a boolean")
        if not isinstance(self.is_stats_pipeline_enabled, bool):
            raise TypeError("is_stats_pipeline_enabled must be a boolean")
        if not isinstance(self.is_embeddings_pipeline_enabled, bool):
            raise TypeError("is_embeddings_pipeline_enabled must be a boolean")
