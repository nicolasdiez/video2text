# src/adapters/outbound/mongodb/app_config_repository.py

from domain.entities.app_config import AppConfig
from domain.value_objects.scheduler_config import SchedulerConfig
from domain.ports.outbound.mongodb.app_config_repository_port import AppConfigRepositoryPort

class MongoAppConfigRepository(AppConfigRepositoryPort):
    def __init__(self, database):
        self._coll = database.get_collection("app_config")

    async def get_config(self) -> AppConfig:
        doc = await self._coll.find_one({"_id": "global"}) or {}
        scheduler_config = doc.get("schedulerConfig", {})
        return AppConfig(
            scheduler_config=SchedulerConfig(
                ingestion_minutes=int(scheduler_config.get("ingestionPipelineFrequencyMinutes", 5)),
                publishing_minutes=int(scheduler_config.get("publishingPipelineFrequencyMinutes", 2)),
            )
        )

    async def update_config(self, config: AppConfig) -> None:
        await self._coll.update_one(
            {"_id": "global"},
            {"$set": {
                "schedulerConfig": {
                    "ingestionPipelineFrequencyMinutes": config.scheduler_config.ingestion_minutes,
                    "publishingPipelineFrequencyMinutes": config.scheduler_config.publishing_minutes,
                }
            }},
            upsert=True
        )
