# POC App

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

import os
from dotenv import load_dotenv

from openai import OpenAI

import re

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

import tweepy

# Set Hugging Face cache directory to D:\hf_cache
os.environ["HF_HOME"] = "D:/software_projects/hf_cache"

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


def load_twitter_api_credentials():

    # Carga las variables definidas en el fichero .env al entorno de ejecución
    load_dotenv()

    # Recupera cada una de las 5 credenciales necesarias
    consumer_key    = os.getenv('X_OAUTH1_API_KEY')
    consumer_secret = os.getenv('X_OAUTH1_API_SECRET')
    access_token    = os.getenv('X_OAUTH1_ACCESS_TOKEN')
    access_secret   = os.getenv('X_OAUTH1_ACCESS_TOKEN_SECRET')
    bearer_token    = os.getenv('X_OAUTH2_API_BEARER_TOKEN')

    # Comprueba si falta alguna
    missing = []
    if not consumer_key:    missing.append('X_OAUTH1_API_KEY')
    if not consumer_secret: missing.append('X_OAUTH1_API_SECRET')
    if not access_token:    missing.append('X_OAUTH1_ACCESS_TOKEN')
    if not access_secret:   missing.append('X_OAUTH1_ACCESS_TOKEN_SECRET')
    if not bearer_token:    missing.append('X_OAUTH2_API_BEARER_TOKEN')

    if missing:
        raise RuntimeError(
            f"Faltan las siguientes credenciales de Twitter en el .env: {', '.join(missing)}"
        )

    print("Todas las credenciales de Twitter se han cargado correctamente.")
    return consumer_key, consumer_secret, access_token, access_secret, bearer_token


def get_videos_from_channel(channel_id, max_videos=10):
    
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
        part="snippet", playlistId=playlist_id, maxResults=max_videos
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

    print(f"Channel ID: {channel_id}")
    print(f"Max requested videos: {max_videos}")
    print(f"Number of videos fetched: {len(videos)}")

    return videos


def get_transcript_from_video(video_id, languages=['es']):
    """
    Returns a plain-text transcript for the given YouTube video ID.
    """
    # Fetch raw transcript segments
    transcript_list = YouTubeTranscriptApi.get_transcript(
        video_id, languages=languages
    )
    # Join all text segments into one string
    full_text = " ".join(segment['text'] for segment in transcript_list)

    print(f"Video:{video_id} transcript created successfully.")

    return full_text


def load_prompt_from_file(prompt_file_name):
    ruta = f"prompts/{prompt_file_name}"
    with open(ruta, "r", encoding="utf-8") as f:
        print(f"Prompt loaded successfully from file: {prompt_file_name}")
        return f.read()
    

def call_openai_api(prompt: str, max_sentences: int = 5, model: str = "gpt-3.5-turbo") -> list[str]:
    
    api_key = load_openai_api_key()
    
    if not api_key:
        raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

    client = OpenAI(api_key=api_key)

    # Wrap the prompt with an instruction to output max_sentences sentences, one per line
    system_message = {
        "role": "system",
        "content": (
            "You are a helpful assistant."
            "Summarize the following transcript into "
            f"{max_sentences} independent, education-focused sentences "
            "designed for Twitter. Output each sentence on its own line, "
            "without numbering or bullet points."
        )
    }
    user_message = {"role": "user", "content": prompt}

    # Llamada a la API
    response = client.chat.completions.create(
        model=model,
        messages=[system_message, user_message],
        temperature=0.7
    )

    raw_output = response.choices[0].message.content

    # Split lines, strip whitespace, remove any leading digits or bullets
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
    clean_sentences = [re.sub(r"^[\d\.\-\)\s]+", "", line) for line in lines]

    return clean_sentences


def post_tweet_v2(text: str) -> str:

    X_OAUTH1_API_KEY, X_OAUTH1_API_SECRET, X_OAUTH1_ACCESS_TOKEN, X_OAUTH1_ACCESS_TOKEN_SECRET, X_OAUTH2_API_BEARER_TOKEN = load_twitter_api_credentials()

    print(X_OAUTH1_API_KEY, X_OAUTH1_API_SECRET, X_OAUTH1_ACCESS_TOKEN, X_OAUTH1_ACCESS_TOKEN_SECRET, X_OAUTH2_API_BEARER_TOKEN)

    client = tweepy.Client(
        consumer_key=X_OAUTH1_API_KEY,
        consumer_secret=X_OAUTH1_API_SECRET,
        access_token=X_OAUTH1_ACCESS_TOKEN,
        access_token_secret=X_OAUTH1_ACCESS_TOKEN_SECRET,
        bearer_token=X_OAUTH2_API_BEARER_TOKEN
    )

    resp = client.create_tweet(text=text)
    return resp.data["id"]


def load_tweets_debugging():

    # Prepara un objeto 'tweets' con 5 elementos para depuración
    tweets = [
        "For beginner investors, focusing on stock market investments through index funds like the S&P 500 can reduce risk and provide automatic diversification. 📈💼 #Investing101 #IndexFunds",
        "Selecting individual stocks may not be the best strategy for beginners due to the necessary time and knowledge. Index funds offer a simpler and more hands-off approach to investing. 📊🔍 #InvestSmart #Diversification",
        "Utilizing a broker to facilitate stock purchases and implementing a strategy of regular, scheduled investments can help beginners navigate the complexities of the market with reduced risk. 💻💸 #Brokerage #InvestingStrategy",
        "Investing in index funds allows beginners to access a diverse portfolio of top companies, with the added benefit of automatic adjustments to maintain portfolio balance. 🌐💰 #FinancialEducation #AutomaticInvesting",
        "Beginner investors can start their investment journey with minimal risk by opting for index funds, which offer exposure to a broad range of companies without the need for extensive time and expertise. 📚💡 #InvestingBasics #LowRiskInvesting"
        ]


    return tweets


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
        max_tokens=100,
    )

    # 4. Extract and return the assistant’s reply
    return response.choices[0].message.content.strip()


def get_text_generator(
        model_name: str = "google/flan-t5-small",  # Changed from LlamaForCausalLM to a compatible seq2seq model
        max_new_tokens: int = 64,
        temperature: float = 0.7,                  # Slightly lower for more factual, financial tone
        do_sample: bool = True,
        tokenizer: str = "google/flan-t5-small",
    ):
    """
    Returns a Hugging Face text-generation pipeline configured with your parameters.
    :param model_name: the pre-trained model to use (must match tokenizer for seq2seq)
    :param max_new_tokens: how many new tokens to generate
    :param temperature: sampling temperature (0.0 for greedy)
    :param do_sample: whether to use sampling (vs. greedy decoding)
    """
    return pipeline(
        "text2text-generation",  # Changed to match model type (flan-T5 is encoder-decoder)
        model=model_name,
        framework="pt",  # <-- Force PyTorch backend (optional)
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=do_sample,
        tokenizer=tokenizer
    )


def call_llm(generator, prompt: str) -> str:
    """
    Feeds your prompt into the given generator pipeline.

    :param generator: a transformers text-generation pipeline
    :param prompt: the full prompt/instruction you want the model to follow
    """

    output = generator(prompt)[0]["generated_text"]

    # Remove the prompt from the beginning of the result
    return output[len(prompt):].strip()


# Example usage
if __name__ == "__main__":

    channel_id = "UCJQQVLyM6wtPleV4wFBK06g"  # VisPol (UCTqb7oZzCYpzOhPenq6AOyQ - SolFon)

    videos = get_videos_from_channel(channel_id)
    
    for i, video in enumerate(videos, start=1):
        print(f"Video: {i}, Title: {video['title']}, Video ID: {video['videoId']}, URL: {video['url']}")

    videoId = "2GDyF6Nv6Dc"  # Replace with your videoId - "V9I8K0R3tgU" b1jUQUSsp0A
    
    transcript_text = get_transcript_from_video(videoId)
    # print(f"Video transcript:\n{transcript_text}")

    prompt_base = load_prompt_from_file("shortsentences-from-transcript.txt")
    prompt_with_transcript = f"{prompt_base.strip()}\n{transcript_text}"

    print(f"Prompt base + Video transcript:\n{prompt_with_transcript}")

    tweets = call_openai_api(prompt_with_transcript, max_sentences=5)
    tweets = load_tweets_debugging()

    for idx, tweet in enumerate(tweets, start=1):
        print(f"Tweet: {idx} - {tweet}")

    tweet_text = tweets.pop(0)
    tweet_id = post_tweet_v2(tweet_text)
    print(f"Publicado en X (v2) con ID: {tweet_id}")

    # twitter_summary = summarize_for_twitter(transcript_text)

    # instantiate once (fast) and reuse
    # gen = get_text_generator()

    # twitter_summary = call_llm(gen, prompt)

    # print("Generated Tweets:\n", twitter_summary)
