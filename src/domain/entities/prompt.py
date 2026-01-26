# src/domain/entities/prompt.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class TweetLengthMode(str, Enum):
    FIXED = "fixed"
    RANGE = "range"


class TweetLengthUnit(str, Enum):
    CHARS = "chars"
    TOKENS = "tokens"


@dataclass(kw_only=True)
class PromptContent:
    """
    Nested content for the Prompt entity holding the system and user messages.
    """
    system_message: str
    user_message: str


@dataclass(kw_only=True)
class TweetLengthPolicy:
    """
    Minimal, extensible policy for tweet length.
    - mode: "fixed" | "range"
    - min_length / max_length: integers in characters (or tokens if unit == tokens)
    - target_length: optional preferred length (primary for fixed; preference for range)
    - tolerance_percent: integer percent tolerance around target_length (default 10)
    - unit: "chars" | "tokens" (default "chars")
    """
    mode: TweetLengthMode = TweetLengthMode.FIXED
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    target_length: Optional[int] = None
    tolerance_percent: int = 10
    unit: TweetLengthUnit = TweetLengthUnit.CHARS


@dataclass(kw_only=True)
class Prompt:
    """
    Domain entity representing a prompt configuration for tweet generation.
    """
    id: Optional[str] = None                # maps to _id / ObjectId
    user_id: str                            # FK → users._id
    channel_id: str                         # FK → channels._id
    prompt_content: PromptContent           # nested system + user messages
    language_of_the_prompt: str             # ISO 639-2 code
    language_to_generate_tweets: str        # ISO 639-2 code
    tweet_length_policy: Optional[TweetLengthPolicy] = None  # optional; fallback to channel/user/system defaults
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)