# application/controllers/pipeline_controller.py

from fastapi import APIRouter, HTTPException
from application.services.pipeline_service import PipelineService
from pydantic import BaseModel

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# creamos esta variable global pipeline_service, que es donde inyectaremos la instancia de PipelineService desde main.py
pipeline_service: PipelineService  # será inyectada desde main.py

# DTO para cargar el body de la request
class RunRequest(BaseModel):
    prompt_file: str = "shortsentences-from-transcript.txt"
    max_videos: int = 10
    max_tweets: int = 5

@router.post("/run/{channel_id}")
async def run_pipeline(channel_id: str, body: RunRequest):
    """
    Lanza el pipeline para el canal indicado:
      - channel_id: YouTube channel ID
      - prompt_file: path al prompt base
      - max_tweets: tweets máximos a generar
    """
    
    try:
        await pipeline_service.run_for_channel(channel_id = channel_id, prompt_file = body.prompt_file, max_videos = body.max_videos, max_tweets = body.max_tweets)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, str(e))