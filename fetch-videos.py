from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

import os
from dotenv import load_dotenv



# Replace with your API key
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def load_api_key():
    
    # Load variables from the .env file into the environment
    load_dotenv()

    # Retrieve the YouTube API key from environment variables
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

    # Now use the key, for example, when configuring your API client
    if YOUTUBE_API_KEY is None:
        raise Exception("YouTube API key not found. Make sure your .env file is properly set.")

    print("Loaded YouTube API key successfully.")
    return YOUTUBE_API_KEY


def get_channel_videos(channel_id):
    
    # load youtube API KEY
    developer_key = load_api_key()

    # Build the YouTube API client
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey = developer_key)
    
    # Fetch the uploaded videos playlist for the channel
    request = youtube.channels().list(part="contentDetails", id=channel_id)
    response = request.execute()
    
    # Get the uploads playlist ID
    playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    # Fetch videos from the playlist
    request = youtube.playlistItems().list(
        part="snippet", playlistId=playlist_id, maxResults=10
    )
    response = request.execute()
    
    # Parse and return video details
    videos = [
        {
            "title": item["snippet"]["title"],
            "videoId": item["snippet"]["resourceId"]["videoId"],
            "url": f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}"
        }
        for item in response.get("items", [])
    ]
    return videos


def fetch_transcript(video_id, languages=['es']):
    """
    Returns a plain-text transcript for the given YouTube video ID.
    """
    # Fetch raw transcript segments
    transcript_list = YouTubeTranscriptApi.get_transcript(
        video_id, languages=languages
    )
    # Join all text segments into one string
    full_text = " ".join(segment['text'] for segment in transcript_list)
    return full_text


# Example usage
if __name__ == "__main__":
    channel_id = "UCJQQVLyM6wtPleV4wFBK06g"  # Example channel ID (Google Developers)
    videos = get_channel_videos(channel_id)
    for video in videos:
        print(f"Title: {video['title']}, Video ID: {video['videoId']}, URL: {video['url']}")

    vid = "2GDyF6Nv6Dc"  # Replace with your videoId - "V9I8K0R3tgU" b1jUQUSsp0A
    text = fetch_transcript(vid)
    print(f"\nVideo transcript: {text}")
