# application/services/prompt_composer_service.py

from domain.entities.prompt import Prompt

class PromptComposerService:
    """
    Service to compose different variations of a prompt from a Prompt entity and additional runtime data like the transcript.
    """

    def compose_with_language(self, prompt: Prompt) -> str:
        """
        Compose partial prompt: text + languageToGenerateTweets.
        """
        return f"{prompt.text}\nAll tweets must be written entirely in the following language (ISO-639-2): {prompt.language_to_generate_tweets}."

    def compose_with_max_tweets(self, prompt: Prompt) -> str:
        """
        Compose partial prompt: text + maxTweetsToGeneratePerVideo.
        """
        return f"{prompt.text}\nGenerate exactly {prompt.max_tweets_to_generate_per_video} tweets based solely on the transcript provided below."

    def add_transcript(self, base_prompt: str, transcript: str) -> str:
        """
        Append only the transcript to an existing prompt string.
        """
        return f"{base_prompt}\n\nHere is the transcript (use only this content as your source):\n{transcript}"
    
    def compose_full_prompt(self, prompt: Prompt, transcript: str) -> str:
        """
        Compose full prompt: text + language + max tweets + transcript at the end.
        The order of language and max tweets is not relevant, but transcript must be last.
        """
        parts = [
            prompt.text,
            #f" ONE VERY IMPORTANT THING TO TAKE INTO ACCOUNT: All sentences (tweets) must be written entirely in the following language: {prompt.language_to_generate_tweets}.",
            #f" Generate exactly {prompt.max_tweets_to_generate_per_video} sentences (tweets) based solely on the transcript provided below.",
            f" Here is the transcript:",
            transcript
        ]
        return "\n".join(str(p) for p in parts if p)
