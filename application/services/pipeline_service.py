# application/services/pipeline_service.py

class PipelineService:

    def __init__(self, video_source: VideoSourcePort, transcriber: TranscriptionPort, openai: OpenAIPort, twitter: TwitterPort, prompt_loader: PromptLoaderPort,):
        self.vs = video_source
        self.tr = transcriber
        self.ai = openai
        self.tw = twitter
        self.pl = prompt_loader


    async def run_for_channel(self, channel_id: str, prompt_file: str, max_tweets: int = 5):

        videos = await self.vs.fetch_new_videos(channel_id)
        
        for v in videos:
            transcript = await self.tr.transcribe(v.videoId)
            base = await self.pl.load_prompt(prompt_file)
            prompt = f"{base.strip()}\n{transcript}"

            tweets = await self.ai.generate_sentences(prompt, max_tweets, model="gpt-3.5-turbo")

            await self.tw.post_many(tweets)
