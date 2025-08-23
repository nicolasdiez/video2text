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

@router.post("/pipelines/ingestion/run/{used_id}")
async def run_pipeline(user_id: str, body: RunRequest):
    """
    Lanza el pipeline para el canal indicado:
      - channel_id: YouTube channel ID
      - prompt_file: path al prompt base
      - max_videos: videos máximos a recuperar del channel_id
      - max_tweets: tweets máximos a generar
    """

    try:
        await ingestion_pipeline_service.run_for_user (user_id = user_id, prompt_file = body.prompt_file, max_videos = body.max_videos, max_tweets = body.max_tweets)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, str(e))