# src/domain/ports/outbound/mongodb/app_config_repository_port.py

from abc import ABC, abstractmethod
from domain.entities.app_config import AppConfig

class AppConfigRepositoryPort(ABC):
    @abstractmethod
    async def get_config(self) -> AppConfig:
        ...

    @abstractmethod
    async def update_config(self, config: AppConfig) -> None:
        ...
