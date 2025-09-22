# src/domain/value_objects/scheduler_config.py

from dataclasses import dataclass

@dataclass(frozen=True)
class SchedulerConfig:
    """
    Value Object que representa la configuración del scheduler.
    Inmutable y validado en su construcción.
    """
    ingestion_minutes: int
    publishing_minutes: int

    def __post_init__(self):
        if self.ingestion_minutes < 0:
            raise ValueError("ingestion_minutes no puede ser menor que 0")
        if self.publishing_minutes < 0:
            raise ValueError("publishing_minutes no puede ser menor que 0")
