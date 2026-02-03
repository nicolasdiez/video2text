# domain/ports/inbound/prompt_composer_service_port.py

from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
from domain.entities.prompt import TweetLengthPolicy

class InstructionPosition(str, Enum):
    BEFORE = "before"
    AFTER = "after"

class PromptComposerServicePort(ABC):
    """
    Hexagonal port for composing prompt variations.
    Defines the contract that PromptComposerService must implement.
    """

    @abstractmethod
    def add_transcript(self, message: str, transcript: str, position: InstructionPosition = InstructionPosition.AFTER) -> str:
        """
        Append or prepend the transcript block to an existing message prompt.
        """
        pass

    @abstractmethod
    def add_objective(self, message: str, sentences: int = 3, position: InstructionPosition = InstructionPosition.BEFORE) -> str:
        """
        Prepend or append the objective block to an existing message prompt.
        """
        pass

    @abstractmethod
    def add_output_language(self, message: str, output_language: str = "Spanish (ESPAÑOL)", position: InstructionPosition = InstructionPosition.AFTER) -> str:
        """
        Append or prepend the output language block to an existing message prompt.
        """
        pass

    @abstractmethod
    def add_output_length(self, message: str, tweet_length_policy: Optional["TweetLengthPolicy"], position: InstructionPosition = InstructionPosition.AFTER) -> str:
        """
        Prepend or append an output length instruction block based on tweet_length_policy.
        """
        pass