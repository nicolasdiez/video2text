# application/controllers/pipeline_controller.py

from fastapi import APIRouter
from application.services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# guardaremos la instancia de PipelineService
pipeline_service: PipelineService  # será inyectada desde main.py

@router.post("/run/{channel_id}")
async def run_pipeline(channel_id: str, prompt_file: str = "default_prompt.txt", max_videos: int = 10, max_tweets: int = 5):
    """
    Lanza el pipeline para el canal indicado:
      - channel_id: YouTube channel ID
      - prompt_file: path al prompt base
      - max_sentences: tweets máximos a generar
    """
    await pipeline_service.run_for_channel(
        channel_id=channel_id,
        prompt_file=prompt_file,
        max_videos=max_videos,
        max_tweets=max_tweets
    )
    return {
        "status": "success",
        "message": f"Pipeline ejecutado para canal {channel_id}, con el prompt {prompt_file}, un número máximo de videos {max_videos}, y un número máximo de tweets {max_tweets}"
    }
