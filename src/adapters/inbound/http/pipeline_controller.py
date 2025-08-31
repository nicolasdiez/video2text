# adapters/inbound/http/pipeline_controller.py

from fastapi import APIRouter, HTTPException
from application.services.ingestion_pipeline_service import IngestionPipelineService
from pydantic import BaseModel

router = APIRouter(prefix="", tags=["pipeline"])

# creamos variable global ingestion_pipeline_service, donde inyectaremos la instancia de IngestionPipelineService con los adapters desde main.py
ingestion_pipeline_service: IngestionPipelineService  # será inyectada desde main.py

# DTO para cargar el body de la request
class RunRequest(BaseModel):
    prompt_file: str = "shortsentences-from-transcript.txt"
    max_videos: int = 2
    max_tweets: int = 3

@router.post("/pipelines/ingestion/run/{user_id}")
async def run_pipeline(user_id: str, body: RunRequest):
    """
    Lanza el pipeline para el user indicado:
      - user_id: User ID
      - prompt_file: path al prompt base
      - max_videos: videos máximos a recuperar de cada channel
      - max_tweets: tweets máximos a generar de cada video
    """

    try:
        await ingestion_pipeline_service.run_for_user(
            user_id = user_id, 
            prompt_file = body.prompt_file, 
            max_videos = body.max_videos, 
            max_tweets = body.max_tweets
        )
        return {"status": "success"}
    # User not found
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # Generic server error
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))