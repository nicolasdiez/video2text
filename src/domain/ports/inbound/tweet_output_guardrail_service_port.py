# src/domain/ports/inbound/tweet_output_guardrail_service_port.py

from abc import ABC, abstractmethod
from typing import Dict
from domain.entities.prompt import TweetLengthPolicy


class TweetOutputGuardrailServicePort(ABC):
    """
    Port defining guardrail validation operations for tweet generation outputs.
    """

    @abstractmethod
    def is_count_valid(self, json_response: Dict, expected_count: int) -> bool:
        """
        Returns True if the number of tweets in the JSON matches the expected count.
        """
        pass

    @abstractmethod
    def is_length_valid(self, json_response: Dict, policy: TweetLengthPolicy) -> bool:
        """
        Returns True if all tweets satisfy the length constraints defined by the policy.
        """
        pass

    @abstractmethod
    def is_semantically_valid(self, json_response: Dict) -> bool:
        """
        Placeholder for future semantic validation using an LLM.
        Always returns True for now.
        """
        pass
