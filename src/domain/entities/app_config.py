# src/domain/entities/app_config.py

from dataclasses import dataclass
from domain.value_objects.scheduler_config import SchedulerConfig

@dataclass
class AppConfig:
    """
    Entidad raíz que representa la configuración global de la aplicación.
    """
    scheduler_config: SchedulerConfig
