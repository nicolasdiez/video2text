# src/domain/value_objects/final_prompt.py

from dataclasses import dataclass
from typing import Optional

from domain.entities.user_prompt import PromptContent, TweetLengthPolicy


@dataclass(frozen=True)
class FinalPrompt:
    """
    Value object representing the fully resolved prompt used for tweet generation.
    Combines:
      - MasterPrompt (base content)
      - UserPrompt (overrides)
      - User-specific generation settings
    Immutable and never persisted directly.
    """
    system_message: str
    user_message: str

    language_to_generate_tweets: str
    tweet_length_policy: Optional[TweetLengthPolicy]
