# src/adapters/outbound/mongodb/app_config_repository.py

from domain.entities.app_config import AppConfig
from domain.value_objects.scheduler_config import SchedulerConfig
from domain.ports.outbound.mongodb.app_config_repository_port import AppConfigRepositoryPort


class MongoAppConfigRepository(AppConfigRepositoryPort):
    def __init__(self, database):
        self._coll = database.get_collection("app_config")

    async def get_config(self) -> AppConfig:
        """
        Read the global app config document and map the schedulerConfig subdocument
        to the SchedulerConfig value object.
        """
        doc = await self._coll.find_one({"_id": "global"}) or {}
        scheduler_config = doc.get("schedulerConfig", {})

        return AppConfig(
            scheduler_config=SchedulerConfig(
                ingestion_pipeline_frequency_minutes=int(
                    scheduler_config.get("ingestionPipelineFrequencyMinutes", 5)
                ),
                publishing_pipeline_frequency_minutes=int(
                    scheduler_config.get("publishingPipelineFrequencyMinutes", 2)
                ),
                is_ingestion_pipeline_enabled=bool(
                    scheduler_config.get("isIngestionPipelineEnabled", True)
                ),
                is_publishing_pipeline_enabled=bool(
                    scheduler_config.get("isPublishingPipelineEnabled", True)
                ),
            )
        )

    async def update_config(self, config: AppConfig) -> None:
        """
        Persist the SchedulerConfig from the AppConfig into the app_config collection.
        """
        sc = config.scheduler_config
        await self._coll.update_one(
            {"_id": "global"},
            {
                "$set": {
                    "schedulerConfig": {
                        "ingestionPipelineFrequencyMinutes": sc.ingestion_pipeline_frequency_minutes,
                        "publishingPipelineFrequencyMinutes": sc.publishing_pipeline_frequency_minutes,
                        "isIngestionPipelineEnabled": sc.is_ingestion_pipeline_enabled,
                        "isPublishingPipelineEnabled": sc.is_publishing_pipeline_enabled,
                    }
                }
            },
            upsert=True,
        )
