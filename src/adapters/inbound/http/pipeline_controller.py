# adapters/inbound/http/pipeline_controller.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from application.services.ingestion_pipeline_service import IngestionPipelineService
from application.services.publishing_pipeline_service import PublishingPipelineService

router = APIRouter(prefix="", tags=["pipeline"])

# global services variables, where the instances with the adapters put in place will be injected from main.py
ingestion_pipeline_service: IngestionPipelineService
publishing_pipeline_service: PublishingPipelineService

# DTO for ingestion
class IngestionRequest(BaseModel):
    prompt_file: str = "shortsentences-from-transcript.txt"
    max_videos_to_fetch_per_channel: int = 2
    max_tweets_to_generate_per_video: int = 3

# DTO for publishing
class PublishingRequest(BaseModel):
    max_tweets_to_fetch: int = 10
    max_tweets_to_publish: int = 5


@router.post("/pipelines/ingestion/run/{user_id}")
async def run_ingestion_pipeline(
    user_id: str, 
    body: IngestionRequest,
    service: IngestionPipelineService = Depends(lambda: ingestion_pipeline_service),
    ):
    """
    Lanza el pipeline de ingestion para el user indicado:
      - user_id: User ID
      - prompt_file: path al prompt base
      - max_videos_to_fetch_per_channel: videos máximos a recuperar de cada channel
      - max_tweets: tweets máximos a generar de cada video
    """

    try:
        await service.run_for_user(
            user_id = user_id, 
            prompt_file = body.prompt_file, 
            max_videos_to_fetch_per_channel = body.max_videos_to_fetch_per_channel, 
            max_tweets_to_generate_per_video = body.max_tweets_to_generate_per_video
        )
        return {"status": "success"}
    # User not found
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # Generic server error
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipelines/publishing/run/{user_id}")
async def run_publishing_pipeline(
    user_id: str,
    body: PublishingRequest,
    service: PublishingPipelineService = Depends(lambda: publishing_pipeline_service),
):
    try:
        await service.run_for_user(
            user_id=user_id,
            max_tweets_to_fetch = body.max_tweets_to_fetch,
            max_tweets_to_publish=body.max_tweets_to_publish,
        )
        return {"status": "success"}
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))