# application/services/pipeline_service.py

# recordatorio hexagonal --> todo lo que vive en /application (negocio) solo debe importar y usar Ports (no Adapters)

# Los Adapters los inyectaremos en la instancia pipeline_service (creada en el controller) desde main.py

from domain.ports.outbound.video_source_port import VideoSourcePort, VideoMetadata
from domain.ports.outbound.transcription_port import TranscriptionPort
from domain.ports.outbound.openai_port import OpenAIPort
from domain.ports.outbound.twitter_port import TwitterPort
from domain.ports.outbound.prompt_loader_port import PromptLoaderPort

from typing import List

class PipelineService:
    """
    Orquesta el flujo completo:
      1. Fetch videos de un canal
      2. Transcribe cada video
      3. Carga un prompt base y lo combina con la transcripción
      4. Genera tweets con OpenAI
      5. Publica cada tweet en Twitter
    """

    def __init__(
        self,
        video_source: VideoSourcePort,
        transcriber: TranscriptionPort,
        prompt_loader: PromptLoaderPort,
        openai_client: OpenAIPort,
        twitter_client: TwitterPort,
    ):
        self.video_source   = video_source
        self.transcriber    = transcriber
        self.prompt_loader  = prompt_loader
        self.openai         = openai_client
        self.twitter        = twitter_client

    # TODO 01-08-2025: 
    # [pipeline_controller] modify controller route so it receives a userId as input, not a channelId
    # [pipeline service] fetch channels from mongoDB which the userId is subscribed to
    # [pipeline service] modify pipeline so tweets are not published, but stored in mongoDB instead

    async def run_for_channel(self, channel_id: str, prompt_file: str, max_videos: int = 10, max_tweets: int = 5) -> None:

        # 1) Cargar prompt base desde fichero (sin bloquear hilo)
        base_prompt = await self.prompt_loader.load_prompt(prompt_file)
        print(f"[PipelineService] Prompt cargado: {prompt_file}")

        # 2) Obtener videos nuevos del canal
        videos: List[VideoMetadata] = await self.video_source.fetch_new_videos(channel_id, max_videos)
        print(f"[PipelineService] {len(videos)} videos obtenidos del canal {channel_id}")

        # 3) Procesar cada video
        for idx, video in enumerate(videos, start=1):
            print(f"[PipelineService] Procesando video {idx}/{len(videos)} (video {video.videoId}): {video.title}")

            # 3.1 Transcripción
            transcript = await self.transcriber.transcribe(video.videoId, language=['es'])
            print(f"[PipelineService] Transcripción recibida (video {video.videoId}), {len(transcript)} caracteres")

            # 3.2 Generar prompt completo
            prompt = f"{base_prompt.strip()}\n{transcript}"

            # 3.3 Llamada a OpenAI para generar tweets
            tweets = await self.openai.generate_tweets(
                prompt=prompt,
                max_sentences=max_tweets,
                model="gpt-3.5-turbo"
            )
            print(f"[PipelineService] {len(tweets)} tweets sugeridos para video {video.videoId}")

            # 3.4 Publicar en Twitter --> a partir de ahora hay que guardar en la collection {tweets}
            for t_idx, tweet_text in enumerate(tweets, start=1):
                # Depuración: imprimir cada tweet
                print(f"Tweet: {t_idx} - {tweet_text}")

                # tweet_id = await self.twitter.publish(tweet_text)
                # print(f"Publicado en Twitter con ID: {tweet_id}")