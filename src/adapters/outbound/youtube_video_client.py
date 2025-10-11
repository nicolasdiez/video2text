# adapters/outbound/youtube_video_client.py

import os

# logging
import inspect
import logging

from typing import List
from googleapiclient.discovery import build

from domain.ports.outbound.video_source_port import VideoSourcePort, VideoMetadata

# Specific logger for this module
logger = logging.getLogger(__name__)


# Usar un DTO  explícito que cumple con VideoMetadata del puerto
class YouTubeVideo(VideoMetadata):
    def __init__(self, videoId: str, title: str, url: str):
        self.videoId = videoId
        self.title = title
        self.url = url
        # TODO: incluir fecha de publicación, e idioma (para pasarselo al TranscriptionService)


class YouTubeVideoClient(VideoSourcePort):
    """
    Implementación del puerto VideoSourcePort para recuperar videos de un canal mediante fetch_new_videos.
    """

    def __init__(self, api_key: str = None):
        
        # load api key --> retrieving videos from a youtube channel only requires API KEY, no OAuth user authentication.
        if not api_key:
            raise RuntimeError("YOUTUBE_API_KEY not defined")
        self.api_key = api_key
        
        
        # Construye el cliente de YouTube
        self.youtube = build(
            "youtube",    # servicio
            "v3",         # versión
            developerKey=self.api_key
        )

        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})


    async def fetch_new_videos(self, channel_id: str, max_videos: int = 10) -> List[VideoMetadata]:
        
        # 1) Obtener el playlist de uploads del canal
        channel_req = self.youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        channel_resp = channel_req.execute()
        playlist_id = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        logger.info("Video playlist retrieved for channel: %s", channel_id , extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})


        # 2) Listar ítems del playlist
        pl_req = self.youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=max_videos
        )
        pl_resp = pl_req.execute()
        logger.info("Items from playlist retrieved for channel: %s", channel_id , extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})


        # 3) Mapear a nuestro DTO / protocolo
        videos: List[VideoMetadata] = []
        for item in pl_resp.get("items", []):
            vid_id = item["snippet"]["resourceId"]["videoId"]
            title  = item["snippet"]["title"]
            url    = f"https://www.youtube.com/watch?v={vid_id}"
            videos.append(YouTubeVideo(videoId=vid_id, title=title, url=url))

        # Logging
        logger.info("Videos retrieved: %s (out of max: %s)", len(videos), max_videos , extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return videos
