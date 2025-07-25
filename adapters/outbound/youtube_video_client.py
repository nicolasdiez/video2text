import os
from typing import List
from googleapiclient.discovery import build

from domain.ports.video_source_port import VideoSourcePort, VideoMetadata


# Usar un DTO  explícito que cumple con VideoMetadata del puerto
class YouTubeVideo(VideoMetadata):
    def __init__(self, videoId: str, title: str, url: str):
        self.videoId = videoId
        self.title = title
        self.url = url


class YouTubeVideoClient(VideoSourcePort):

    def __init__(self, api_key: str = None):

        # Recupera la API key de env var (si no se pasa en el constructor)
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise RuntimeError("YOUTUBE_API_KEY no definido")
        
        # Construye el cliente de YouTube
        self.youtube = build(
            "youtube",    # servicio
            "v3",         # versión
            developerKey=self.api_key
        )

    async def fetch_new_videos(self, channel_id: str, max_videos: int = 10) -> List[VideoMetadata]:
        
        # 1) Obtener el playlist de uploads del canal
        channel_req = self.youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        channel_resp = channel_req.execute()
        playlist_id = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # 2) Listar ítems del playlist
        pl_req = self.youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=max_videos
        )
        pl_resp = pl_req.execute()

        # 3) Mapear a nuestro DTO / protocolo
        videos: List[VideoMetadata] = []
        for item in pl_resp.get("items", []):
            vid_id = item["snippet"]["resourceId"]["videoId"]
            title  = item["snippet"]["title"]
            url    = f"https://www.youtube.com/watch?v={vid_id}"
            videos.append(YouTubeVideo(videoId=vid_id, title=title, url=url))

        # Logging
        print(f"[YouTubeVideoClient] Canal: {channel_id}")
        print(f"[YouTubeVideoClient] Solicitados: {max_videos}, Obtenidos: {len(videos)}")

        return videos
