# adapters/inbound/http/pipeline_controller.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from application.services.ingestion_pipeline_service import IngestionPipelineService
from application.services.publishing_pipeline_service import PublishingPipelineService

router = APIRouter(prefix="", tags=["pipeline"])

# global services variables, where the instances with the adapters put in place will be injected from main.py
ingestion_pipeline_service: IngestionPipelineService
publishing_pipeline_service: PublishingPipelineService


@router.post("/pipelines/ingestion/run/{user_id}")
async def run_ingestion_pipeline(user_id: str, service: IngestionPipelineService = Depends(lambda: ingestion_pipeline_service)):
    """
    Lanza el pipeline de ingestion para el user indicado:
      - user_id: User ID
    """
    try:
        await service.run_for_user(user_id = user_id)
        return {"status": "success"}
    # User not found
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # Generic server error
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipelines/publishing/run/{user_id}")
async def run_publishing_pipeline(user_id: str, service: PublishingPipelineService = Depends(lambda: publishing_pipeline_service)):
    """
    Lanza el pipeline de publicación para el user indicado:
      - user_id: User ID
    """
    try:
        await service.run_for_user(user_id=user_id)
        return {"status": "success"}
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))