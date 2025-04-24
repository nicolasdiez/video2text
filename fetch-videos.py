from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

import os
from dotenv import load_dotenv

import openai


# Replace with your API key
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def load_youtube_api_key():
    
    # Load variables from the .env file into the environment
    load_dotenv()

    # Retrieve the YouTube API key from environment variables
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

    # Now use the key, for example, when configuring your API client
    if YOUTUBE_API_KEY is None:
        raise Exception("YouTube API key not found. Make sure your .env file is properly set.")

    print("Loaded YouTube API key successfully.")
    return YOUTUBE_API_KEY


def load_openai_api_key():
    # Load variables from the .env file into the environment
    load_dotenv()

    # Retrieve the Open AI API key from environment variables
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Now use the key, for example, when configuring your API client
    if OPENAI_API_KEY is None:
        raise Exception("OpenAI API key not found. Make sure your .env file is properly set.")

    print("Loaded Open AI API key successfully.")
    return OPENAI_API_KEY


def get_channel_videos(channel_id):
    
    # load youtube API KEY
    developer_key = load_youtube_api_key()

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


def summarize_for_twitter(text: str) -> str:
    """
    Sends the transcript text to ChatGPT and returns a 3–5 sentence,
    finance-focused Twitter summary.
    """

    developer_key = load_openai_api_key()

    client = openai.OpenAI(api_key=developer_key)

    # 2. Define your prompt with the transcript appended
    prompt = (
        "Could you summarize the video script I pass you below in several independent sentences?\n"
        "The sentences should be education-focused and designed to be posted on Twitter (X) as independent posts.\n"
        "Provide 3–5 short sentences, not more. Sentences should be really meaningful and targeted to a financial investing community.\n"
        "Some examples of previously produced sentences:\n"
        "1– Warren Buffett is stockpiling cash, not to time the market but to seize rare opportunities when prices drop—patience pays. 💰📉 #InvestingWisdom #ValueInvesting\n"
        "2– Market corrections often stem from external catalysts, not overvaluation alone. Staying prepared beats market timing. 🧠📊 #StockMarket #LongTermInvesting\n"
        "3– Diversification and a long-term mindset are key in navigating market volatility. Ride the waves, don’t chase the tide. 🌊📈 #FinancialFreedom #InvestSmart\n"
        "4– In market downturns, cash is king. Buffett’s 2008 investments in Goldman Sachs and GE proved that opportunity comes to the prepared. 🔑💼 #CashOnHand #BuffettWisdom\n"
        "5– Stock market corrections can be golden opportunities. As Buffett says, when it rains gold, carry a wash tub—not a teaspoon. 🌧️💵 #StockMarketCorrection #WealthBuilding\n\n"
        f"---\n\nHere’s the transcript:\n{text}\n\n"
        "Please output only the list of new sentences."
    )

    prompt_short = (
        "Summarize the following transcript into 2 short, independent, finance-focused sentences for Twitter:\n"
        f"{text}\n"
        "Only return the 2 sentences."
    )

    # 3. Call the ChatCompletion endpoint
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or "gpt-4o-mini" if cost is a concern and you have access or "gpt-4o"
        messages=[{"role": "user", "content": prompt_short}],
        temperature=0.5,
        max_tokens=100
    )

    # 4. Extract and return the assistant’s reply
    return response.choices[0].message.content.strip()


# Example usage
if __name__ == "__main__":
    channel_id = "UCJQQVLyM6wtPleV4wFBK06g"  # Example channel ID (Google Developers)
    videos = get_channel_videos(channel_id)
    for video in videos:
        print(f"Title: {video['title']}, Video ID: {video['videoId']}, URL: {video['url']}")

    vid = "2GDyF6Nv6Dc"  # Replace with your videoId - "V9I8K0R3tgU" b1jUQUSsp0A
    transcript_text = fetch_transcript(vid)
    print(f"\nVideo transcript: {transcript_text}")

    twitter_summary = summarize_for_twitter(transcript_text)
    print("Generated Tweets:\n", twitter_summary)
