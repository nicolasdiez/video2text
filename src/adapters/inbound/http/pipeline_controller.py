# src/adapters/inbound/http/pipeline_controller.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from application.services.generation_pipeline_service import GenerationPipelineService
from application.services.publishing_pipeline_service import PublishingPipelineService

router = APIRouter(prefix="", tags=["pipeline"])

# global services variables, where the instances with the adapters put in place will be injected from main.py
generation_pipeline_service: GenerationPipelineService
publishing_pipeline_service: PublishingPipelineService


@router.post("/pipelines/generation/run/{user_id}")
async def run_generation_pipeline(user_id: str, service: GenerationPipelineService = Depends(lambda: generation_pipeline_service)):
    """
    Lanza el pipeline de generation para el user indicado:
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