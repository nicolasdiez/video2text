# src/application/services/ingestion_pipeline_service.py

from datetime import datetime
from typing import List

from domain.ports.inbound.ingestion_pipeline_port import IngestionPipelinePort
from domain.ports.outbound.channel_repository_port import ChannelRepositoryPort
from domain.ports.outbound.video_repository_port import VideoRepositoryPort, Video
from domain.ports.outbound.transcription_service_port import TranscriptionServicePort
from domain.ports.outbound.tweet_generation_service_port import TweetGenerationServicePort, Tweet
from domain.ports.outbound.tweet_repository_port import TweetRepositoryPort

from domain.ports.outbound.video_source_port import VideoSourcePort, VideoMetadata
from domain.ports.outbound.transcription_port import TranscriptionPort
from domain.ports.outbound.openai_port import OpenAIPort
from domain.ports.outbound.twitter_port import TwitterPort
from domain.ports.outbound.prompt_loader_port import PromptLoaderPort


class IngestionPipelineService(IngestionPipelinePort):
    """
    Orquesta el pipeline de ingestión para un usuario:
      1) Obtiene los canales del user_id
      2) Recupera vídeos nuevos de cada canal
      3) Transcribe los vídeos sin transcripción
      4) Genera tweets para cada vídeo
      5) Persiste todos los tweets generados
    """

    def __init__(
        self,
        channel_repo: ChannelRepositoryPort,
        video_repo: VideoRepositoryPort,
        transcription_service: TranscriptionServicePort,
        tweet_gen_service: TweetGenerationServicePort,
        tweet_repo: TweetRepositoryPort,
    ):
        self.channel_repo = channel_repo
        self.video_repo = video_repo
        self.transcription_service = transcription_service
        self.tweet_gen_service = tweet_gen_service
        self.tweet_repo = tweet_repo

    async def run_for_user(self, user_id: str) -> None:
        # 1) Fetch canales asociados al usuario
        channels = await self.channel_repo.find_by_user_id(user_id)

        # 2) Procesar cada canal
        for channel in channels:
            # 2.1) Obtener vídeos nuevos
            videos: List[VideoMetadata] = await self.video_repo.find_new_videos(channel.id)

            # 3) Para cada vídeo sin transcripción, obtener y marcar transcriptFetchedAt
            for video in videos:
                if video.transcript_fetched_at is None:
                    transcript = await self.transcription_service.fetch_transcript(video)
                    video.transcript = transcript
                    video.transcript_fetched_at = datetime.utcnow()
                    await self.video_repo.update(video)

                # 4) Generar tweets basados en el vídeo y su transcripción
                tweets: List[Tweet] = await self.tweet_gen_service.generate_for_video(video)

                # 5) Persistir todos los tweets generados
                if tweets:
                    await self.tweet_repo.save_all(tweets)
