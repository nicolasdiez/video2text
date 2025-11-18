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
    
    def add_transcript(self, message: str, transcript: str) -> str:
        """
        Append the transcript to an existing message prompt.
        """        
        parts = [
            message,
            f" Here is the transcript:",
            transcript
        ]
        return "\n".join(str(p) for p in parts if p)
    

    def add_objective(self, message: str, max_sentences: int = 3) -> str:
        """
        Append the objective to an existing message prompt.
        """   
        objective_block = (
            f"=== OBJECTIVE ===\n"
            f"Based on the provided transcript, create exactly {max_sentences} short, standalone tweets.\n\n"
        )

        message_with_objective = message.rstrip() + "\n\n" + objective_block
    
        return message_with_objective


    def add_output_language(self, message: str, output_language: str = "Spanish (ESPAÑOL)") -> str:
        """
        Append the output language to an existing message prompt.
        """   
        output_language_block = (
            f"=== OUTPUT LANGUAGE ===\n"
            f"The short and standalone tweets must be generated in {output_language} language.\n\n"
        )

        # Build system_content respecting the input prompt_system_message
        message_with_output_language = message.rstrip() + "\n\n" + output_language_block

        return message_with_output_language
