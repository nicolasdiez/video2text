# src/domain/ports/outbound/llm_port.py

from abc import ABC, abstractmethod

class LLMPort(ABC):
    """
    Port that abstracts text generation through any Large Language Model (LLM).
    Implementations may use OpenAI, Anthropic, Mistral, etc.
    """

    @abstractmethod
    async def generate_tweets(
        self,
        prompt_user_message: str,
        prompt_system_message: str,
        max_tweets: int,
        output_language: str,
        model: str
    ) -> list[str]:
        """
        Sends a prompt to an LLM and returns a list of clean tweet sentences.

        :param prompt_user_message: the actual user request or content to process
        :param prompt_system_message: instructions defining behavior, tone, or rules for the model
        :param max_tweets: maximum number of tweet sentences to generate
        :param output_language: language in which the tweets should be generated
        :param model: identifier of the LLM model to use
        :return: list of tweet sentences without numbering or bullet points
        """
        pass
