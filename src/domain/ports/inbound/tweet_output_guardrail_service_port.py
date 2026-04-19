# src/domain/ports/inbound/tweet_output_guardrail_port.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from domain.entities.user_prompt import TweetLengthPolicy


class TweetOutputGuardrailPort(ABC):
    """
    Port defining guardrail validation operations for tweet generation outputs.
    """

    @abstractmethod
    def is_count_valid(self, json_response: Dict, expected_count: int) -> bool:
        """
        Returns True if the number of tweets in the JSON matches the expected count.
        """
        raise NotImplementedError

    @abstractmethod
    def is_length_valid(self, json_response: Dict, policy: TweetLengthPolicy) -> bool:
        """
        Returns True if all tweets satisfy the length constraints defined by the policy.
        """
        raise NotImplementedError

    @abstractmethod
    def is_json_structure_valid(self, json_response: Any) -> Tuple[bool, Optional[str]]:
        """
        Pure JSON-format validator for LLM output.

        - Input: the parsed adapter output (any type).
        - Behaviour: perform only structural checks (no business rules, no normalization,
          no truncation). Must detect whether the payload is a dict containing a 'tweets'
          list with at least one plausible text candidate (string or dict with a text-like key).
        - Return: (True, None) when structure is acceptable; (False, reason_code) otherwise.
        - Logging: implementations SHOULD log a concise info line with the validation result
          (use the same logger style as other guardrail methods).
        - Side effects: none (no exceptions for expected validation failures; exceptions
          reserved for unexpected errors).
        """
        raise NotImplementedError

    @abstractmethod
    def is_semantically_valid(self, json_response: Dict) -> bool:
        """
        Placeholder for future semantic validation using an LLM.
        Always returns True for now.
        """
        raise NotImplementedError
